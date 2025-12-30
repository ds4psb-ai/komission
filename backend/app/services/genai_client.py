"""
Google GenAI Client Module v2.0

P0 Hardening Applied:
- H1: Response Envelope + Error Mapping
- H2: Timeout + Retry + Exponential Backoff

Usage:
    from app.services.genai_client import generate_content, GenAIResponse
    
    response = generate_content(contents=[...])
    if response.success:
        print(response.text)
    else:
        print(f"Error: {response.error_code} - {response.error}")
"""
import os
import time
import logging
import asyncio
from functools import lru_cache
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, Tuple
from enum import Enum

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    Part,
    Content,
    Tool,
    SafetySetting,
)

logger = logging.getLogger(__name__)

# ============================================
# Configuration
# ============================================

DEFAULT_MODEL_FLASH = "gemini-2.0-flash-exp"
DEFAULT_MODEL_PRO = "gemini-2.0-pro-exp"
DEFAULT_MODEL_AUDIO = "gemini-2.5-flash-native-audio-latest"

# Timeout and Retry Configuration
GENAI_TIMEOUT_SECONDS = 60
GENAI_MAX_RETRIES = 3
GENAI_BASE_DELAY_SECONDS = 1.0
GENAI_MAX_DELAY_SECONDS = 30.0


# ============================================
# Error Codes
# ============================================

class GenAIErrorCode(str, Enum):
    """Standardized error codes"""
    RATE_LIMIT = "rate_limit"       # 429
    TIMEOUT = "timeout"             # Request timeout
    SERVER_ERROR = "server_error"   # 5xx
    CONTENT_FILTER = "content_filter"  # Safety filter
    INVALID_REQUEST = "invalid_request"  # 4xx (not 429)
    API_KEY_INVALID = "api_key_invalid"
    QUOTA_EXCEEDED = "quota_exceeded"
    UNKNOWN = "unknown"


# ============================================
# Response Envelope
# ============================================

@dataclass
class GenAIResponse:
    """
    Standardized response envelope for all GenAI calls.
    
    Attributes:
        success: Whether the call succeeded
        text: Generated text (if success)
        raw_response: Original SDK response object
        usage: Token usage stats
        model: Model used
        latency_ms: Request duration in milliseconds
        
        error: Error message (if failed)
        error_code: Standardized error code
        retryable: Whether the error is retryable
        retry_after_ms: Suggested wait time before retry
        attempt_count: Number of attempts made
    """
    success: bool
    text: Optional[str] = None
    raw_response: Optional[Any] = None
    usage: Optional[Dict[str, int]] = None
    model: str = ""
    latency_ms: int = 0
    
    # Error fields
    error: Optional[str] = None
    error_code: Optional[GenAIErrorCode] = None
    retryable: bool = False
    retry_after_ms: Optional[int] = None
    attempt_count: int = 1


# ============================================
# Error Mapping
# ============================================

def _map_error(exception: Exception) -> Tuple[GenAIErrorCode, bool, Optional[int]]:
    """
    Map SDK exceptions to standardized error codes.
    
    Returns: (error_code, retryable, retry_after_ms)
    """
    error_str = str(exception).lower()
    exception_type = type(exception).__name__
    
    # Rate limit (429)
    if "429" in error_str or "rate" in error_str or "quota" in error_str:
        # Try to extract retry-after from error
        retry_after = 60000  # Default 60 seconds
        if "retry" in error_str:
            try:
                import re
                match = re.search(r'(\d+)\s*(?:second|sec|s)', error_str)
                if match:
                    retry_after = int(match.group(1)) * 1000
            except Exception:
                pass
        return GenAIErrorCode.RATE_LIMIT, True, retry_after
    
    # Timeout
    if "timeout" in error_str or exception_type == "TimeoutError":
        return GenAIErrorCode.TIMEOUT, True, 5000
    
    # Server errors (5xx)
    if any(code in error_str for code in ["500", "502", "503", "504"]):
        return GenAIErrorCode.SERVER_ERROR, True, 10000
    
    # Content filter / Safety
    if "safety" in error_str or "blocked" in error_str or "filter" in error_str:
        return GenAIErrorCode.CONTENT_FILTER, False, None
    
    # API key issues
    if "api_key" in error_str or "authentication" in error_str or "401" in error_str:
        return GenAIErrorCode.API_KEY_INVALID, False, None
    
    # Invalid request (4xx)
    if any(code in error_str for code in ["400", "403", "404"]):
        return GenAIErrorCode.INVALID_REQUEST, False, None
    
    # Unknown
    return GenAIErrorCode.UNKNOWN, False, None


def _extract_usage(response: Any) -> Optional[Dict[str, int]]:
    """Extract token usage from response if available."""
    try:
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            return {
                "prompt_tokens": getattr(usage, 'prompt_token_count', 0),
                "completion_tokens": getattr(usage, 'candidates_token_count', 0),
                "total_tokens": getattr(usage, 'total_token_count', 0),
            }
    except Exception:
        pass
    return None


# ============================================
# Client
# ============================================

@lru_cache(maxsize=1)
def get_genai_client() -> genai.Client:
    """
    Get singleton GenAI client.
    
    Uses GOOGLE_API_KEY or GEMINI_API_KEY from environment.
    
    Returns:
        google.genai.Client instance
    """
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("No API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    logger.info("✅ GenAI client initialized (using google-genai SDK v2.0)")
    
    return client


# ============================================
# Retry Logic
# ============================================

def _calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff with jitter."""
    import random
    delay = GENAI_BASE_DELAY_SECONDS * (2 ** attempt)
    delay = min(delay, GENAI_MAX_DELAY_SECONDS)
    # Add jitter (±25%)
    jitter = delay * 0.25 * (random.random() * 2 - 1)
    return delay + jitter


# ============================================
# Content Generation (Sync)
# ============================================

def generate_content(
    contents: list,
    model: str = DEFAULT_MODEL_FLASH,
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
    response_mime_type: Optional[str] = None,
    system_instruction: Optional[str] = None,
) -> GenAIResponse:
    """
    Generate content with standardized response envelope.
    
    Includes:
    - Automatic retry with exponential backoff (max 3 attempts)
    - Standardized error mapping
    - Latency tracking
    - Usage extraction
    
    Args:
        contents: List of content parts (strings, Parts, etc.)
        model: Model name (default: gemini-2.0-flash-exp)
        temperature: Sampling temperature
        max_output_tokens: Max output tokens
        response_mime_type: e.g. "application/json"
        system_instruction: System prompt (currently unused by new SDK)
        
    Returns:
        GenAIResponse with success/failure info
    """
    client = get_genai_client()
    
    config = GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        candidate_count=1,
    )
    
    if response_mime_type:
        config.response_mime_type = response_mime_type
    
    last_error: Optional[Exception] = None
    start_time = time.time()
    
    for attempt in range(GENAI_MAX_RETRIES):
        attempt_start = time.time()
        
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            logger.debug(
                f"GenAI success: model={model}, attempt={attempt+1}, "
                f"latency={latency_ms}ms"
            )
            
            return GenAIResponse(
                success=True,
                text=response.text,
                raw_response=response,
                model=model,
                latency_ms=latency_ms,
                usage=_extract_usage(response),
                attempt_count=attempt + 1,
            )
            
        except Exception as e:
            last_error = e
            error_code, retryable, retry_after = _map_error(e)
            
            logger.warning(
                f"GenAI error: model={model}, attempt={attempt+1}/{GENAI_MAX_RETRIES}, "
                f"error_code={error_code}, retryable={retryable}, error={str(e)[:100]}"
            )
            
            # Don't retry non-retryable errors
            if not retryable:
                break
            
            # Don't retry on last attempt
            if attempt < GENAI_MAX_RETRIES - 1:
                delay = _calculate_backoff(attempt)
                logger.info(f"Retrying in {delay:.2f}s...")
                time.sleep(delay)
    
    # All retries exhausted or non-retryable error
    latency_ms = int((time.time() - start_time) * 1000)
    error_code, retryable, retry_after = _map_error(last_error)
    
    return GenAIResponse(
        success=False,
        model=model,
        latency_ms=latency_ms,
        error=str(last_error),
        error_code=error_code,
        retryable=retryable,
        retry_after_ms=retry_after,
        attempt_count=GENAI_MAX_RETRIES if retryable else 1,
    )


# ============================================
# Content Generation (Async)
# ============================================

async def generate_content_async(
    contents: list,
    model: str = DEFAULT_MODEL_FLASH,
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
    response_mime_type: Optional[str] = None,
    system_instruction: Optional[str] = None,
    timeout: float = GENAI_TIMEOUT_SECONDS,
) -> GenAIResponse:
    """
    Async content generation with timeout and retry.
    
    Uses client.aio.models for true async operation.
    Includes timeout wrapping for safety.
    """
    client = get_genai_client()
    
    config = GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        candidate_count=1,
    )
    
    if response_mime_type:
        config.response_mime_type = response_mime_type
    
    last_error: Optional[Exception] = None
    start_time = time.time()
    
    for attempt in range(GENAI_MAX_RETRIES):
        try:
            # Wrap with timeout
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                ),
                timeout=timeout
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            logger.debug(
                f"GenAI async success: model={model}, attempt={attempt+1}, "
                f"latency={latency_ms}ms"
            )
            
            return GenAIResponse(
                success=True,
                text=response.text,
                raw_response=response,
                model=model,
                latency_ms=latency_ms,
                usage=_extract_usage(response),
                attempt_count=attempt + 1,
            )
            
        except asyncio.TimeoutError as e:
            last_error = e
            logger.warning(
                f"GenAI timeout: model={model}, attempt={attempt+1}/{GENAI_MAX_RETRIES}, "
                f"timeout={timeout}s"
            )
            
            if attempt < GENAI_MAX_RETRIES - 1:
                delay = _calculate_backoff(attempt)
                await asyncio.sleep(delay)
                
        except Exception as e:
            last_error = e
            error_code, retryable, retry_after = _map_error(e)
            
            logger.warning(
                f"GenAI async error: model={model}, attempt={attempt+1}/{GENAI_MAX_RETRIES}, "
                f"error_code={error_code}, error={str(e)[:100]}"
            )
            
            if not retryable:
                break
            
            if attempt < GENAI_MAX_RETRIES - 1:
                delay = _calculate_backoff(attempt)
                await asyncio.sleep(delay)
    
    # All retries exhausted
    latency_ms = int((time.time() - start_time) * 1000)
    
    if isinstance(last_error, asyncio.TimeoutError):
        error_code = GenAIErrorCode.TIMEOUT
        retryable = True
        retry_after = 5000
    else:
        error_code, retryable, retry_after = _map_error(last_error)
    
    return GenAIResponse(
        success=False,
        model=model,
        latency_ms=latency_ms,
        error=str(last_error),
        error_code=error_code,
        retryable=retryable,
        retry_after_ms=retry_after,
        attempt_count=GENAI_MAX_RETRIES,
    )


# ============================================
# Legacy Compatibility (returns str, raises on error)
# ============================================

def generate_content_text(
    contents: list,
    model: str = DEFAULT_MODEL_FLASH,
    **kwargs
) -> str:
    """
    Legacy wrapper that returns raw text or raises exception.
    
    Use generate_content() for new code.
    """
    response = generate_content(contents, model, **kwargs)
    
    if not response.success:
        raise RuntimeError(
            f"GenAI call failed: {response.error_code} - {response.error}"
        )
    
    return response.text or ""


async def generate_content_text_async(
    contents: list,
    model: str = DEFAULT_MODEL_FLASH,
    **kwargs
) -> str:
    """
    Legacy async wrapper that returns raw text or raises exception.
    
    Use generate_content_async() for new code.
    """
    response = await generate_content_async(contents, model, **kwargs)
    
    if not response.success:
        raise RuntimeError(
            f"GenAI async call failed: {response.error_code} - {response.error}"
        )
    
    return response.text or ""


# ============================================
# Exports
# ============================================

__all__ = [
    # Client
    "get_genai_client",
    
    # Main functions (new)
    "generate_content",
    "generate_content_async",
    
    # Legacy compatibility
    "generate_content_text",
    "generate_content_text_async",
    
    # Response types
    "GenAIResponse",
    "GenAIErrorCode",
    
    # SDK types
    "Part",
    "Content",
    "GenerateContentConfig",
    "Tool",
    "SafetySetting",
    
    # Constants
    "DEFAULT_MODEL_FLASH",
    "DEFAULT_MODEL_PRO",
    "DEFAULT_MODEL_AUDIO",
    "GENAI_TIMEOUT_SECONDS",
    "GENAI_MAX_RETRIES",
]
