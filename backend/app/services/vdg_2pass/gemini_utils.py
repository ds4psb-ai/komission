"""
Gemini API Utilities

P0-4: Retry + Async Fallback + JSON Repair
"""
from typing import TypeVar, Type, Callable, Any, Optional
import json
import asyncio
import logging
import time
import random
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


async def robust_generate_content(
    model,
    contents: list,
    result_schema: Type[T],
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    json_repair_prompt: str = "Your previous output was not valid JSON. Respond with ONLY valid JSON matching the schema, no extra text."
) -> T:
    """
    Robust content generation with retry, backoff, and JSON repair.
    
    P0-4 Hardening:
    1. Retry with exponential backoff (429/5xx/network errors)
    2. Async fallback (use sync generate_content in thread if async fails)
    3. JSON repair loop (1 attempt if parsing fails)
    
    Args:
        model: Gemini GenerativeModel instance
        contents: Content parts to send
        result_schema: Pydantic model class for parsing
        max_retries: Maximum retry attempts
        initial_backoff: Starting backoff in seconds
        json_repair_prompt: Prompt for JSON repair attempt
        
    Returns:
        Parsed result of type T
        
    Raises:
        Exception: If all retries exhausted
    """
    last_error = None
    backoff = initial_backoff
    
    for attempt in range(max_retries):
        try:
            # Try async first
            response = await _try_generate_async(model, contents)
            
            # Try to parse response
            try:
                result_dict = json.loads(response.text)
                return result_schema(**result_dict)
            except json.JSONDecodeError as je:
                logger.warning(f"JSON parse failed (attempt {attempt + 1}): {je}")
                
                # JSON Repair: One repair attempt
                if attempt < max_retries - 1:
                    repair_contents = contents + [json_repair_prompt]
                    repair_response = await _try_generate_async(model, repair_contents)
                    result_dict = json.loads(repair_response.text)
                    return result_schema(**result_dict)
                else:
                    raise
                    
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check if retryable
            is_retryable = any(x in error_str for x in [
                "429", "rate limit", "quota", 
                "500", "502", "503", "504", "internal", 
                "timeout", "connection", "network"
            ])
            
            if is_retryable and attempt < max_retries - 1:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, backoff * 0.5)
                wait_time = backoff + jitter
                logger.warning(f"⚠️ Retryable error (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"   Waiting {wait_time:.1f}s before retry...")
                await asyncio.sleep(wait_time)
                backoff *= 2  # Exponential backoff
            else:
                logger.error(f"❌ Non-retryable error or max retries reached: {e}")
                raise
    
    raise last_error or Exception("All retries exhausted")


async def _try_generate_async(model, contents: list):
    """
    Try async generation with sync fallback.
    """
    try:
        # Try async method first
        if hasattr(model, 'generate_content_async'):
            return await model.generate_content_async(contents=contents)
        else:
            # Fallback to sync in thread
            logger.info("Using sync generate_content in thread executor")
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: model.generate_content(contents=contents)
            )
    except AttributeError:
        # Async method doesn't exist, use sync fallback
        logger.info("Async method not available, using sync fallback")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: model.generate_content(contents=contents)
        )


def extract_json_from_text(text: str) -> dict:
    """
    Extract JSON from text that might have extra content.
    
    Handles cases like:
    - Plain JSON
    - JSON in markdown code blocks
    - JSON with trailing text
    """
    text = text.strip()
    
    # Try plain JSON first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code block
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
    
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
    
    # Try finding JSON object/array bounds
    if "{" in text:
        start = text.find("{")
        depth = 0
        for i, c in enumerate(text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        break
    
    raise json.JSONDecodeError("Could not extract JSON from text", text, 0)
