"""
VDG Analyzer - Main GeminiPipeline Class

영상 분석 파이프라인의 핵심 클래스
"""
import os
import json
import logging
import asyncio
import hashlib
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types
from app.config import settings
from app.services.video_downloader import video_downloader
from app.schemas.vdg import VDG
from app.schemas.vdg_v4 import VDGv4
from app.services.vdg_2pass.vdg_unified_pipeline import VDGUnifiedPipeline
from app.validators.schema_validator import validate_vdg_analysis_schema, SchemaValidationError

from .constants import VDG_PROMPT
from .prompt_builder import build_enhanced_prompt, get_analysis_depth_hints
from .converter import convert_unified_to_vdg_v4
from .sanitizer import sanitize_vdg_payload, populate_legacy_fields

logger = logging.getLogger(__name__)


class GeminiPipeline:
    """
    VDG (Video Data Graph) 분석 파이프라인
    
    v5.0: Unified Pass + CV
    - Pass 1: Gemini 3.0 Pro 1회 호출 (의미/인과/Plan Seed)
    - Pass 2: CV deterministic measurement (현재 skip)
    """
    
    def __init__(self):
        self.model = settings.GEMINI_MODEL
        # Prefer GEMINI_API_KEY first (GOOGLE_API_KEY was leaked)
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        if api_key:
            if settings.GEMINI_API_KEY and settings.GOOGLE_API_KEY:
                logger.info("Using GEMINI_API_KEY (preferred)")
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logger.warning("No API key set. GeminiPipeline will use mock data.")

    async def analyze_video(
        self, 
        video_url: str, 
        node_id: str,
        audience_comments: Optional[List[Dict[str, Any]]] = None
    ) -> VDG:
        """
        Legacy pipeline: Download -> Upload -> Analyze (VDG) -> Parse -> Return
        
        NOTE: This is the legacy v3 method. Use analyze_video_v4() for v5 pipeline.
        
        Args:
            video_url: Video URL to analyze
            node_id: Node ID for tracking
            audience_comments: Optional list of best comments for context
                [{"text": "...", "likes": 123, "lang": "en"}, ...]
        """
        if not self.client:
            logger.info("No API key, returning mock VDG data.")
            return self._get_mock_data(node_id)

        temp_path = None
        try:
            # 1. Download Video
            logger.warning(f"📥 Downloading video from {video_url}...")
            temp_path, metadata = await video_downloader.download(video_url)
            try:
                size_mb = os.path.getsize(temp_path) / (1024 * 1024)
                logger.warning(f"📦 Downloaded size: {size_mb:.2f} MB ({temp_path})")
            except Exception as e:
                logger.warning(f"📦 Downloaded size unavailable: {e}")
            
            # 2. Build inline video part (base64)
            try:
                with open(temp_path, "rb") as video_fp:
                    video_bytes = video_fp.read()
                import base64
                video_b64 = base64.standard_b64encode(video_bytes).decode("utf-8")
                video_part = types.Part.from_bytes(
                    data=base64.standard_b64decode(video_b64),
                    mime_type="video/mp4"
                )
            except Exception as e:
                logger.error(f"Failed to encode video: {e}")
                return self._get_mock_data(node_id)

            # 3. Build enhanced prompt with duration and comments
            duration_sec = metadata.duration or 30.0
            enhanced_prompt = build_enhanced_prompt(
                duration_sec=duration_sec,
                audience_comments=audience_comments
            )

            # 4. Analyze with Gemini
            logger.info(f"🔍 Running Gemini analysis for {node_id}...")
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=[video_part, enhanced_prompt],
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                )
            )

            # 5. Parse response
            raw_text = response.text.strip()
            
            # Extract JSON block
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            payload = json.loads(raw_text)
            
            # 6. Sanitize before validation
            payload = sanitize_vdg_payload(payload)
            
            # 7. Validate and return
            vdg = VDG(**payload)
            populate_legacy_fields(vdg)
            
            logger.info(f"✅ VDG analysis complete for {node_id}")
            return vdg

        except Exception as e:
            logger.error(f"❌ VDG analysis failed: {e}", exc_info=True)
            raise e
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    async def analyze_video_v4(
        self,
        video_url: str,
        node_id: str,
        audience_comments: Optional[List[Dict[str, Any]]] = None
    ) -> VDGv4:
        """
        VDG v5.0 Unified Pipeline Execution
        
        Pass 1: Gemini 3.0 Pro 1회 호출 (의미/인과/Plan Seed)
        Pass 2: CV 결정론적 측정 (수치/좌표) - 현재 skip
        
        ** Redis Cache 지원: 동일 영상+댓글 조합은 24시간 캐시 **
        """
        from app.services.cache import cache
        
        # Generate comments hash for cache key
        comments_str = json.dumps(audience_comments or [], sort_keys=True)
        comments_hash = hashlib.md5(comments_str.encode()).hexdigest()
        
        # 0. Check cache first
        try:
            await cache.connect()
            cached_data = await cache.get_vdg_v4(video_url, comments_hash)
            if cached_data:
                logger.info(f"✅ [v5] Cache HIT for {video_url[:50]}...")
                return VDGv4.model_validate(cached_data)
        except Exception as e:
            logger.warning(f"Cache check failed (continuing without cache): {e}")
        
        temp_path = None
        try:
            # 1. Download
            logger.info(f"📥 [v5] Downloading {video_url}...")
            temp_path, metadata = await video_downloader.download(video_url)
            
            duration_sec = metadata.duration or 0.0
            if duration_sec == 0.0:
                # Fallback: ffprobe로 측정
                from app.services.vdg_2pass.unified_pass import get_video_duration_ms
                duration_ms = get_video_duration_ms(temp_path)
                duration_sec = duration_ms / 1000.0 if duration_ms > 0 else 60.0

            platform = "youtube" 
            if "tiktok.com" in video_url: platform = "tiktok"
            elif "instagram.com" in video_url: platform = "instagram"
            elif "shorts" in video_url: platform = "youtube"

            # 2. Extract comments text
            top_comments = []
            if audience_comments:
                top_comments = [
                    c.get("text", "")[:200] for c in audience_comments[:20]
                    if c.get("text")
                ]

            # 3. Run unified pipeline (sync, but wrapped in executor for async context)
            logger.info("🚀 [v5] Running VDG Unified Pipeline...")
            
            def _run_sync():
                from app.services.vdg_2pass.vdg_unified_pipeline import PipelineConfig
                # Skip CV Pass to prevent indefinite hangs (CV optimization is separate task)
                config = PipelineConfig(skip_cv_pass=True)
                pipeline = VDGUnifiedPipeline(config=config)
                return pipeline.run(
                    video_path=temp_path,
                    platform=platform,
                    top_comments=top_comments,
                )
            
            # Run sync pipeline in thread pool
            loop = asyncio.get_event_loop()
            unified_result = await loop.run_in_executor(None, _run_sync)
            
            logger.info(
                f"✅ [v5] Pipeline complete: "
                f"pass1={unified_result.pass1_latency_ms}ms, "
                f"pass2={unified_result.pass2_latency_ms}ms"
            )
            
            # 4. Convert UnifiedResult to VDGv4 format
            vdg = convert_unified_to_vdg_v4(
                unified_result=unified_result,
                content_id=node_id,
                video_url=video_url,
                platform=platform,
                duration_sec=duration_sec,
            )
            
            # 4.5 P0-1: Quality Gate validation
            from app.services.vdg_2pass.quality_gate import proof_grade_gate
            proof_ready, quality_issues = proof_grade_gate.validate(
                vdg.model_dump(), 
                int(duration_sec * 1000)
            )
            
            # Update VDG meta with quality gate results
            vdg.meta = {
                "proof_ready": proof_ready,
                "quality_issues": quality_issues if quality_issues else None,
                "prompt_version": "v4.2",
                "model_id": "gemini-3.0-pro",
                "schema_version": vdg.vdg_version,
            }
            
            if proof_ready:
                logger.info(f"✅ [v5] Quality Gate PASSED")
            else:
                logger.warning(f"⚠️ [v5] Quality Gate FAILED: {quality_issues[:3]}")
            
            # Get final vdg_data for cache
            vdg_data = vdg.model_dump()
            
            # 5. Save to cache (24 hours)
            try:
                await cache.set_vdg_v4(video_url, comments_hash, vdg_data)
                logger.info(f"💾 [v5] Cached VDG for {video_url[:50]}...")
            except Exception as e:
                logger.warning(f"Cache save failed: {e}")
            
            return vdg

        except Exception as e:
            logger.error(f"❌ [v5] Pipeline failed: {e}", exc_info=True)
            raise e
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def _convert_unified_to_vdg_v4(
        self,
        unified_result,
        content_id: str,
        video_url: str,
        platform: str,
        duration_sec: float,
    ) -> VDGv4:
        """Wrapper for backward compatibility"""
        return convert_unified_to_vdg_v4(
            unified_result=unified_result,
            content_id=content_id,
            video_url=video_url,
            platform=platform,
            duration_sec=duration_sec,
        )

    def _sanitize_vdg_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for backward compatibility"""
        return sanitize_vdg_payload(payload)

    def _populate_legacy_fields(self, vdg: VDG) -> None:
        """Wrapper for backward compatibility"""
        return populate_legacy_fields(vdg)

    def _get_mock_data(self, video_id: str) -> VDG:
        """Return mock VDG data when API key is not available"""
        return VDG(
            content_id=video_id,
            title="Mock Video",
            duration_sec=15.0,
            summary="Mock summary",
            hook_genome=dict(hook_summary="Mock hook", strength=0.8),
            scenes=[],
            intent_layer=dict(
                hook_trigger="shock", 
                irony_analysis=dict(setup="A", twist="B"),
                dopamine_radar=dict(visual_spectacle=5, audio_stimulation=5, narrative_intrigue=5, emotional_resonance=5, comedy_shock=5)
            ),
            remix_suggestions=[],
            capsule_brief=dict(hook_script="Mock script", constraints=dict(primary_challenge="Mock challenge"))
        )


# Singleton instance
gemini_pipeline = GeminiPipeline()
