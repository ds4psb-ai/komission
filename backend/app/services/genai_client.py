"""
Google GenAI Client Module

Centralized client for the new google-genai SDK (v1.56.0+)
Replaces deprecated google.generativeai

Usage:
    from app.services.genai_client import get_genai_client, get_model

    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[...],
    )
"""
import os
import logging
from functools import lru_cache
from typing import Optional

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    Part,
    Content,
    Tool,
    SafetySetting,
)

logger = logging.getLogger(__name__)

# Default model names
DEFAULT_MODEL_FLASH = "gemini-2.0-flash-exp"
DEFAULT_MODEL_PRO = "gemini-2.0-pro-exp"
DEFAULT_MODEL_AUDIO = "gemini-2.5-flash-native-audio-latest"


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
    logger.info("✅ GenAI client initialized (using google-genai SDK)")
    
    return client


def generate_content(
    contents: list,
    model: str = DEFAULT_MODEL_FLASH,
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
    response_mime_type: Optional[str] = None,
    system_instruction: Optional[str] = None,
) -> str:
    """
    Simplified content generation wrapper.
    
    Args:
        contents: List of content parts (strings, Parts, etc.)
        model: Model name (default: gemini-2.0-flash-exp)
        temperature: Sampling temperature
        max_output_tokens: Max output tokens
        response_mime_type: e.g. "application/json"
        system_instruction: System prompt
        
    Returns:
        Generated text response
    """
    client = get_genai_client()
    
    config = GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        candidate_count=1,
    )
    
    if response_mime_type:
        config.response_mime_type = response_mime_type
    
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    
    return response.text


async def generate_content_async(
    contents: list,
    model: str = DEFAULT_MODEL_FLASH,
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
    response_mime_type: Optional[str] = None,
    system_instruction: Optional[str] = None,
) -> str:
    """
    Async content generation wrapper.
    
    Uses client.aio.models for true async operation.
    """
    client = get_genai_client()
    
    config = GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        candidate_count=1,
    )
    
    if response_mime_type:
        config.response_mime_type = response_mime_type
    
    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    
    return response.text


# Re-export commonly used types for convenience
__all__ = [
    "get_genai_client",
    "generate_content",
    "generate_content_async",
    "Part",
    "Content",
    "GenerateContentConfig",
    "Tool",
    "SafetySetting",
    "DEFAULT_MODEL_FLASH",
    "DEFAULT_MODEL_PRO",
    "DEFAULT_MODEL_AUDIO",
]
