"""
Video Analysis Schema for Gemini 3.0 Pro Structured Output
Based on 15_FINAL_ARCHITECTURE.md
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class AttentionTechnique(str, Enum):
    """훅 주의 기법"""
    TEXT_PUNCH = "text_punch"
    FACE_ZOOM = "face_zoom"  
    QUESTION = "question"
    SHOCK_VALUE = "shock_value"
    CURIOSITY_GAP = "curiosity_gap"
    OTHER = "other"


class VisualPattern(str, Enum):
    """시각 패턴"""
    RAPID_CUT = "rapid_cut"
    SLOW_MOTION = "slow_motion"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    TRANSITION = "transition"
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"


class AudioPattern(str, Enum):
    """오디오 패턴"""
    BEAT_SYNC = "beat_sync"
    VOICE_OVER = "voice_over"
    MUSIC_DROP = "music_drop"
    SOUND_EFFECT = "sound_effect"
    ASMR = "asmr"
    SILENCE = "silence"
    TRENDING_AUDIO = "trending_audio"


class HookAnalysis(BaseModel):
    """훅 분석 (0-3초)"""
    hook_text: Optional[str] = Field(None, description="텍스트 훅 내용")
    hook_duration_sec: float = Field(default=2.0, description="훅 지속 시간 (초)")
    attention_technique: AttentionTechnique = Field(description="주의 끄는 기법")
    hook_strength: float = Field(default=0.5, ge=0.0, le=1.0, description="훅 강도 (0-1)")


class ShotAnalysis(BaseModel):
    """개별 샷 분석"""
    shot_index: int = Field(description="샷 인덱스")
    duration_sec: float = Field(description="샷 지속 시간 (초)")
    visual_pattern: VisualPattern = Field(description="시각 패턴")
    audio_pattern: Optional[AudioPattern] = Field(None, description="오디오 패턴")
    has_text_overlay: bool = Field(default=False, description="텍스트 오버레이 존재 여부")
    is_key_moment: bool = Field(default=False, description="핵심 순간 여부")


class VideoAnalysisSchema(BaseModel):
    """
    Gemini 3.0 Pro Structured Output용 영상 분석 스키마
    
    이 스키마는 JSON Schema 출력을 강제하여 재현성을 보장합니다.
    """
    # 훅 분석
    hook: HookAnalysis = Field(description="훅 분석 (0-3초)")
    
    # 샷 시퀀스
    shots: List[ShotAnalysis] = Field(description="샷별 분석 리스트")
    
    # 오디오 요약
    audio_summary: str = Field(description="전체 오디오 특성 요약")
    audio_is_trending: bool = Field(default=False, description="트렌딩 오디오 사용 여부")
    
    # 장면 설명
    scene_description: str = Field(description="전체 장면/분위기 설명")
    
    # 타이밍
    timing_profile: List[float] = Field(description="각 샷 길이 리스트 (초)")
    total_duration_sec: float = Field(description="전체 영상 길이 (초)")
    
    # 키워드/태그
    keywords: List[str] = Field(description="추출된 키워드 (3-10개)")
    
    # 패턴 분류 (클러스터링용)
    primary_pattern: str = Field(description="주요 패턴 식별자 (예: Hook-2s-TextPunch)")
    pattern_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="패턴 신뢰도")


class AnalysisRequest(BaseModel):
    """분석 요청"""
    video_url: str = Field(description="분석할 영상 URL")
    node_id: Optional[str] = Field(None, description="연결할 노드 ID")
    force_reanalyze: bool = Field(default=False, description="기존 분석 덮어쓰기")


class AnalysisResponse(BaseModel):
    """분석 응답"""
    success: bool
    node_id: Optional[str] = None
    schema_version: str = Field(default="v1.0")
    analysis: Optional[VideoAnalysisSchema] = None
    cluster_id: Optional[str] = None
    error: Optional[str] = None
