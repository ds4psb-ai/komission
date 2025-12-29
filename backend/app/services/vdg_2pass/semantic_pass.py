"""
Semantic Pass (VDG v4.0 Pass 1)

P0-4: Uses robust_generate_content for retry/fallback/JSON repair
"""
from typing import List, Dict, Any
import json
import logging
import hashlib
from datetime import datetime
import google.generativeai as genai
from google.generativeai import types
from app.schemas.vdg_v4 import SemanticPassResult
from app.services.vdg_2pass.prompts.semantic_prompt import SEMANTIC_SYSTEM_PROMPT, SEMANTIC_USER_PROMPT
from app.services.vdg_2pass.gemini_utils import robust_generate_content
from app.config import settings

logger = logging.getLogger(__name__)


class SemanticPass:
    """
    VDG v4.0 Pass 1: Semantic Analysis
    
    Uses Gemini 2.0 Flash to extract:
    - Narrative Structure (Scenes, Hook)
    - Intent Layer
    - Entity Hints (Candidates)
    - Mise-en-scene Signals (from comments)
    
    P0-4 Hardening:
    - Retry with exponential backoff
    - Async fallback to sync
    - JSON repair loop
    - Provenance tracking
    """
    
    def __init__(self, client=None):
        self.client = client
        if not self.client and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use config or default to 2.0 Flash
        self.model_name = getattr(settings, "GEMINI_MODEL_FLASH", "gemini-2.0-flash-exp")

    async def analyze(
        self,
        video_bytes: bytes,
        duration_sec: float,
        comments: List[Dict[str, Any]],
        platform: str = "youtube"
    ) -> SemanticPassResult:
        """
        Execute semantic analysis pass.
        
        Args:
            video_bytes: Raw video data
            duration_sec: Video duration in seconds
            comments: List of popular comments [{'text':..., 'likes':...}]
            platform: 'youtube' | 'tiktok' | 'instagram'
            
        Returns:
            SemanticPassResult object
        """
        start_time = datetime.utcnow()
        
        # 1. Prepare Comments Context (sanitized)
        formatted_comments = "\n".join([
            f"- [{c.get('likes', 0)} likes] {c.get('text', '')[:200]}"
            for c in comments[:20]  # Limit to top 20
        ])
        
        # 2. Build Prompts
        system_prompt = SEMANTIC_SYSTEM_PROMPT.format(
            platform=platform,
            duration_sec=duration_sec
        )
        
        user_prompt = SEMANTIC_USER_PROMPT.format(
            comments_context=formatted_comments
        )
        
        # 3. Prepare Video Part
        video_part = types.Part(
            inline_data=types.Blob(
                data=video_bytes,
                mime_type="video/mp4"
            )
        )
        
        # 4. Generate Content with P0-4 hardening
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            generation_config=types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=SemanticPassResult,
                temperature=0.2,  # Low temp for structured extraction
                top_p=0.95,
                max_output_tokens=8192
            )
        )
        
        logger.info(f"🚀 Starting Semantic Pass (Model: {self.model_name})")
        
        # P0-4: Use robust generation with retry/fallback/repair
        result = await robust_generate_content(
            model=model,
            contents=[video_part, user_prompt],
            result_schema=SemanticPassResult,
            max_retries=3,
            initial_backoff=1.0
        )
        
        # 5. Add provenance (P0-4: tracking for debugging)
        end_time = datetime.utcnow()
        elapsed_sec = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Semantic Pass completed in {elapsed_sec:.1f}s")
        logger.info(f"   └─ Hook: {result.hook_genome.pattern if result.hook_genome else 'N/A'}")
        logger.info(f"   └─ Scenes: {len(result.scenes)}")
        logger.info(f"   └─ Entity Hints: {list(result.entity_hints.keys())}")
        logger.info(f"   └─ Mise-en-scene Signals: {len(result.mise_en_scene_signals) if hasattr(result, 'mise_en_scene_signals') else 0}")
        
        return result
