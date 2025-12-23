from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field
from app.schemas.viral_codebook import VisualPatternCode, AudioPatternCode, SemanticIntent

# --- Physics & Simulation Primitives ---

class Vector3(BaseModel):
    x: float
    y: float
    z: float

class ColorHex(BaseModel):
    hex: str = Field(..., description="#RRGGBB format")
    alpha: float = Field(1.0, ge=0.0, le=1.0)

# --- Scene Components ---

class CameraSpec(BaseModel):
    type: Literal["static", "linear_tracking", "dolly_zoom", "handheld", "crane", "fpv_drone"] = "static"
    movement_vector: Vector3 = Field(default_factory=lambda: Vector3(x=0, y=0, z=0), description="Normalized velocity vector")
    fov_estimate: float = Field(60.0, description="Estimated Field of View in degrees")
    focus_target: str = Field("subject_face", description="Main focus point")
    shake_intensity: float = Field(0.0, ge=0.0, le=1.0, description="Camera shake amount")

class LightingSpec(BaseModel):
    intensity: float = Field(0.8, ge=0.0, le=1.0)
    color_temp_kelvin: int = Field(6500, description="Estimated color temperature")
    direction: Literal["front", "back", "side_left", "side_right", "top_down", "ambient"] = "front"
    shadow_softness: float = Field(0.5, ge=0.0, le=1.0)

class ActorAction(BaseModel):
    actor_id: str = Field(..., description="Unique ID for actor in scene")
    pose_description: str = Field(..., description="Short pose name e.g. 'squat', 't-pose'")
    velocity_vector: Vector3 = Field(default_factory=lambda: Vector3(x=0, y=0, z=0))
    screen_position_center: Vector3 = Field(..., description="Normalized screen coordinates [x, y, depth_z]")
    emotion_state: str = Field("neutral", description="Primary emotion")
    body_parts_engaged: List[str] = Field(default_factory=list, description="e.g. ['legs', 'arms']")

class AudioFabric(BaseModel):
    rms_intensity: float = Field(0.0, ge=0.0, le=1.0)
    spectral_centroid: float = Field(0.0, description="Brightness of sound")
    is_beat_hit: bool = Field(False)
    dominant_stems: List[str] = Field(default_factory=list, description="['vocals', 'bass', 'drums']")

# --- Viral Mosaic System (RL Ready) ---

class ViralMosaicTile(BaseModel):
    time_index: int = Field(..., description="Segment index (0, 1, 2...)")
    start_time: float
    end_time: float
    
    # Feature Codes (GA/RL State Space - MUST use Codebook Enums)
    visual_pattern_id: VisualPatternCode = Field(..., description="Standardized Visual Pattern")
    audio_pattern_id: AudioPatternCode = Field(..., description="Standardized Audio Pattern")
    
    # Semantic Intent (GA/RL Action Space)
    semantic_intent: SemanticIntent = Field(SemanticIntent.AROUSE_CURIOSITY, description="Viewer psychology target")
    predicted_retention: float = Field(1.0, ge=0.0, le=1.0)

# --- Global Context (For Human/Claude Summary) ---

class GlobalContext(BaseModel):
    title: str
    mood: str
    keywords: List[str]
    viral_hook_summary: str = Field(..., description="Summary of why this video is viral")
    key_action_description: str = Field(..., description="The main action to replicate (e.g. 'Squat Dance')")
    hashtags: List[str]
    
    # Legacy Compatibility (Hook Genome 2.0)
    hook_pattern: Literal["problem_solution", "pattern_break", "question", "proof", "other"] = Field("other", description="Legacy Hook Type")
    hook_delivery: Literal["dialogue", "voiceover", "on_screen_text", "visual_gag", "sfx_only"] = Field("visual_gag", description="Primary delivery method")
    hook_strength_score: float = Field(0.9, ge=0.0, le=1.0)

# --- Master Frame ---

class SceneFrame(BaseModel):
    timestamp: float
    duration: float
    
    # Simulation Data
    camera: CameraSpec
    lighting: LightingSpec
    actors: List[ActorAction]
    audio: AudioFabric
    
    # Metadata
    description: str

class ReconstructibleAnalysisResult(BaseModel):
    video_id: str
    fps: float = 30.0
    duration: float
    
    # High Level Context
    global_context: GlobalContext
    
    # The Simulation Data
    scene_frames: List[SceneFrame] = Field(..., description="Sampled at 1-2 FPS for reconstruction")
    
    # The RL Data
    viral_mosaic: List[ViralMosaicTile] = Field(..., description="Viral pattern blocks")


# --- Mutation Tracking (Genealogy Graph Core) ---

class MutationDelta(BaseModel):
    """단일 속성의 Before/After 변화"""
    before: str
    after: str
    delta_type: Literal["replaced", "added", "removed", "modified"] = "replaced"
    confidence: float = Field(0.9, ge=0.0, le=1.0)

class MutationProfile(BaseModel):
    """
    부모→자식 간 뮤테이션 요약
    Neo4j EVOLVED_TO 엣지에 저장되는 핵심 데이터
    """
    parent_node_id: str
    child_node_id: str
    
    # 주요 변화 필드 (Codebook Enum 기반)
    audio_mutation: Optional[MutationDelta] = None
    visual_mutation: Optional[MutationDelta] = None
    setting_mutation: Optional[MutationDelta] = None
    timing_mutation: Optional[MutationDelta] = None
    text_overlay_mutation: Optional[MutationDelta] = None
    hook_pattern_mutation: Optional[MutationDelta] = None
    
    # 메타데이터
    mutation_count: int = 0
    primary_mutation_type: str = ""  # "audio" | "visual" | "setting" | etc.
    mutation_summary: str = ""  # Human-readable summary
    
    # 성과 데이터 (나중에 채워짐)
    performance_delta: Optional[str] = None  # "+127%", "-20%"

