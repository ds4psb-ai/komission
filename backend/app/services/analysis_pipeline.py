"""
Video Analysis Pipeline using Gemini 3.0 Pro Structured Output
Based on 15_FINAL_ARCHITECTURE.md

핵심 원칙:
- 영상 해석은 코드 기반 (재현성/버전관리)
- JSON Schema 출력 강제 (Structured Output)
- 결과는 DB에 저장 (SoR)
"""
import logging
from typing import Optional
from datetime import datetime
from app.services.genai_client import get_genai_client, DEFAULT_MODEL_FLASH

from app.schemas.analysis_schema import (
    VideoAnalysisSchema,
    AnalysisRequest,
    AnalysisResponse,
    HookAnalysis,
    ShotAnalysis,
    AttentionTechnique,
    VisualPattern,
)
from app.config import settings
from app.database import get_db
from app.models import NotebookLibraryEntry

logger = logging.getLogger(__name__)

# Gemini Model Configuration
ANALYSIS_MODEL = DEFAULT_MODEL_FLASH
SCHEMA_VERSION = "v1.0"


class AnalysisPipeline:
    """
    영상 분석 파이프라인
    Gemini 3.0 Pro를 사용하여 영상을 분석하고 스키마를 생성
    """
    
    def __init__(self):
        self.client = None
        self._configure_gemini()
    
    def _configure_gemini(self):
        """Gemini API 설정 (new SDK)"""
        try:
            self.client = get_genai_client()
            logger.info(f"Gemini client configured: {ANALYSIS_MODEL}")
        except ValueError as e:
            logger.warning(f"API key not set - analysis pipeline will use mock data: {e}")
    
    def _build_prompt(self, video_url: str, video_context: Optional[dict] = None) -> str:
        """분석 프롬프트 생성"""
        context_str = ""
        if video_context:
            context_str = f"\n\nAdditional context:\n{video_context}"
        
        return f"""Analyze this short-form video and extract structured patterns.

Video URL: {video_url}
{context_str}

Analyze the video and provide the following in JSON format:

1. **Hook Analysis (0-3 seconds)**:
   - hook_text: Any text shown or spoken
   - hook_duration_sec: Duration of the hook
   - attention_technique: One of [text_punch, face_zoom, question, shock_value, curiosity_gap, other]
   - hook_strength: 0.0 to 1.0

2. **Shot Sequence**:
   For each distinct shot, provide:
   - shot_index: Sequential number
   - duration_sec: Length in seconds
   - visual_pattern: One of [rapid_cut, slow_motion, zoom_in, zoom_out, transition, static, pan, tilt]
   - audio_pattern: One of [beat_sync, voice_over, music_drop, sound_effect, asmr, silence, trending_audio] or null
   - has_text_overlay: boolean
   - is_key_moment: boolean if this is a climax/highlight

3. **Audio Summary**: Describe the overall audio characteristics

4. **Scene Description**: Overall atmosphere and setting

5. **Timing Profile**: List of shot durations in seconds

6. **Keywords**: 3-10 relevant keywords/tags

7. **Primary Pattern**: A unique identifier like "Hook-2s-TextPunch" or "BeatSync-FastCut"

Return ONLY valid JSON matching this schema: {VideoAnalysisSchema.model_json_schema()}
"""

    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        영상 분석 실행
        
        Args:
            request: 분석 요청 (video_url, node_id 등)
        
        Returns:
            AnalysisResponse with schema or error
        """
        try:
            if not self.client:
                logger.warning("No client configured, returning mock analysis")
                return self._mock_analysis(request)
            
            # Generate analysis with new SDK
            prompt = self._build_prompt(request.video_url)
            response = self.client.models.generate_content(
                model=ANALYSIS_MODEL,
                contents=[prompt],
                config={
                    "temperature": 0.1,
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json",
                }
            )
            
            # Parse JSON response
            import json
            analysis_data = json.loads(response.text)
            analysis = VideoAnalysisSchema(**analysis_data)
            
            # Generate cluster_id from primary_pattern
            cluster_id = analysis.primary_pattern.replace(" ", "-").lower()
            
            return AnalysisResponse(
                success=True,
                node_id=request.node_id,
                schema_version=SCHEMA_VERSION,
                analysis=analysis,
                cluster_id=cluster_id,
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResponse(
                success=False,
                error=str(e),
            )
    
    def _mock_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """개발/테스트용 목업 분석"""
        mock_analysis = VideoAnalysisSchema(
            hook=HookAnalysis(
                hook_text="이거 진짜 대박인데...",
                hook_duration_sec=2.0,
                attention_technique=AttentionTechnique.TEXT_PUNCH,
                hook_strength=0.85,
            ),
            shots=[
                ShotAnalysis(
                    shot_index=0,
                    duration_sec=2.0,
                    visual_pattern=VisualPattern.ZOOM_IN,
                    audio_pattern=None,
                    has_text_overlay=True,
                    is_key_moment=False,
                ),
                ShotAnalysis(
                    shot_index=1,
                    duration_sec=3.5,
                    visual_pattern=VisualPattern.RAPID_CUT,
                    audio_pattern=None,
                    has_text_overlay=False,
                    is_key_moment=True,
                ),
            ],
            audio_summary="Trending K-pop beat with voice-over narration",
            audio_is_trending=True,
            scene_description="Indoor studio with bright lighting, product showcase",
            timing_profile=[2.0, 3.5, 2.5, 1.8],
            total_duration_sec=9.8,
            keywords=["K-beauty", "skincare", "tutorial", "viral"],
            primary_pattern="Hook-2s-TextPunch",
            pattern_confidence=0.8,
        )
        
        return AnalysisResponse(
            success=True,
            node_id=request.node_id,
            schema_version=SCHEMA_VERSION,
            analysis=mock_analysis,
            cluster_id="hook-2s-textpunch",
        )


# Singleton instance
_pipeline: Optional[AnalysisPipeline] = None


def get_analysis_pipeline() -> AnalysisPipeline:
    """파이프라인 싱글톤 반환"""
    global _pipeline
    if _pipeline is None:
        _pipeline = AnalysisPipeline()
    return _pipeline


async def analyze_video(video_url: str, node_id: Optional[str] = None) -> AnalysisResponse:
    """
    편의 함수: 영상 분석 실행
    
    Args:
        video_url: 분석할 영상 URL
        node_id: 연결할 노드 ID (optional)
    
    Returns:
        AnalysisResponse
    """
    pipeline = get_analysis_pipeline()
    request = AnalysisRequest(video_url=video_url, node_id=node_id)
    return await pipeline.analyze(request)
