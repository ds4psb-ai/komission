"""
VDP Gold Schema - Complete Video Data Product
Based on original VDP structure + Gemini 3.0 Pro Intent Layer
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

# ==================== METADATA ====================
class VideoMetrics(BaseModel):
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: Optional[int] = None

# ==================== HOOK GENOME ====================
class HookGenome(BaseModel):
    start_sec: float = 0.0
    end_sec: float = 3.0
    pattern: Literal["problem_solution", "pattern_break", "question", "proof", "curiosity_gap", "other"] = "other"
    delivery: Literal["dialogue", "voiceover", "on_screen_text", "visual_gag", "sfx_only"] = "visual_gag"
    strength: float = Field(0.5, ge=0.0, le=1.0)

# ==================== AUDIENCE REACTION ====================
class NotableComment(BaseModel):
    text: str
    lang: str = "en"
    translation_en: Optional[str] = None

class AudienceReaction(BaseModel):
    analysis: str = ""
    common_reactions: List[str] = Field(default_factory=list)
    notable_comments: List[NotableComment] = Field(default_factory=list)
    overall_sentiment: Literal["Positive", "Mixed", "Negative"] = "Positive"

class OCRText(BaseModel):
    text: str
    lang: str = "en"
    translation_en: Optional[str] = None

# ==================== OVERALL ANALYSIS ====================
class OverallAnalysis(BaseModel):
    summary: str = ""
    emotional_arc: str = ""
    hook_genome: HookGenome = Field(default_factory=HookGenome)
    audience_reaction: AudienceReaction = Field(default_factory=AudienceReaction)
    asr_transcript: Optional[str] = None
    asr_lang: Optional[str] = None
    ocr_text: List[OCRText] = Field(default_factory=list)

# ==================== SHOT STRUCTURE ====================
class Keyframe(BaseModel):
    role: Literal["start", "peak", "end"] = "start"
    desc: str = ""
    t_rel_shot: float = 0.0

class Camera(BaseModel):
    shot: Literal["CU", "MS", "WS", "ECU"] = "MS"
    angle: Literal["eye", "low", "high", "dutch"] = "eye"
    move: Literal["static", "pan", "tilt", "dolly", "zoom", "handheld"] = "static"

class Composition(BaseModel):
    grid: str = "center"  # Relaxed: center, rule_of_thirds, left_third, right_heavy, etc.
    notes: List[str] = Field(default_factory=list)

class Shot(BaseModel):
    shot_id: str
    start: float
    end: float
    camera: Camera = Field(default_factory=Camera)
    composition: Composition = Field(default_factory=Composition)
    keyframes: List[Keyframe] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"

# ==================== AUDIO ====================
class AudioEvent(BaseModel):
    timestamp: float
    event: str = "sfx_hit"  # Relaxed: Gemini generates creative event names
    description: str = ""
    intensity: Literal["low", "medium", "high"] = "medium"

class AudioStyle(BaseModel):
    music: str = ""
    ambient_sound: str = ""
    tone: str = ""
    audio_events: List[AudioEvent] = Field(default_factory=list)

# ==================== VISUAL STYLE ====================
class EditGrammar(BaseModel):
    cut_speed: str = "medium"  # Relaxed: slow, medium, fast, etc.
    camera_style: str = "static_shot"  # Relaxed
    subtitle_style: str = "none"  # Relaxed

class VisualStyle(BaseModel):
    cinematic_properties: str = ""
    lighting: str = ""
    mood_palette: List[str] = Field(default_factory=list)
    edit_grammar: EditGrammar = Field(default_factory=EditGrammar)

class Setting(BaseModel):
    location: str = ""
    visual_style: VisualStyle = Field(default_factory=VisualStyle)
    audio_style: AudioStyle = Field(default_factory=AudioStyle)

# ==================== NARRATIVE UNIT ====================
class NarrativeUnit(BaseModel):
    role: Literal["Hook", "RisingAction", "Development", "Punchline", "Outro"] = "Development"
    summary: str = ""
    dialogue: Optional[str] = None
    dialogue_lang: Optional[str] = None
    dialogue_translation_en: Optional[str] = None
    rhetoric: List[str] = Field(default_factory=list)
    comedic_device: List[str] = Field(default_factory=list)

# ==================== SCENE ====================
class Scene(BaseModel):
    scene_id: str
    time_start: float
    time_end: float
    duration_sec: float
    importance: Literal["critical", "major", "minor"] = "major"
    narrative_unit: NarrativeUnit = Field(default_factory=NarrativeUnit)
    setting: Setting = Field(default_factory=Setting)
    shots: List[Shot] = Field(default_factory=list)

# ==================== PRODUCT MENTIONS ====================
class ProductMention(BaseModel):
    type: Literal["product", "brand", "logo"] = "product"
    name: str
    sources: List[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    category: str = ""
    time_ranges: List[List[float]] = Field(default_factory=list)

# ==================== SCENE COMMENT MAP ====================
class SceneCommentMap(BaseModel):
    scene_id: str
    comment_ids: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

# ==================== CROSS-SCENE ANALYSIS ====================
class ConsistentElement(BaseModel):
    aspect: str
    evidence: str
    scenes: List[str] = Field(default_factory=list)

class EvolvingElement(BaseModel):
    dimension: str
    description: str
    evidence: str

class SceneSentiment(BaseModel):
    scene_id: str
    start: Dict[str, Any] = Field(default_factory=dict)
    end: Dict[str, Any] = Field(default_factory=dict)

class MicroShift(BaseModel):
    t: float
    from_emotion: str = Field(alias="from")
    to_emotion: str = Field(alias="to")
    cue: str

    class Config:
        populate_by_name = True

class SentimentArc(BaseModel):
    per_scene: List[SceneSentiment] = Field(default_factory=list)
    micro_shifts: List[Dict[str, Any]] = Field(default_factory=list)
    global_trajectory: str = ""

class DirectorIntent(BaseModel):
    technique: str
    intended_effect: str
    rationale: str
    evidence: Dict[str, Any] = Field(default_factory=dict)

class CrossSceneAnalysis(BaseModel):
    global_summary: str = ""
    consistent_elements: List[ConsistentElement] = Field(default_factory=list)
    evolving_elements: List[EvolvingElement] = Field(default_factory=list)
    sentiment_arc: SentimentArc = Field(default_factory=SentimentArc)
    director_intent: List[DirectorIntent] = Field(default_factory=list)

# ==================== INTENT LAYER (Gemini 3.0 Pro) ====================
class IntentLayer(BaseModel):
    hook_trigger: Literal["curiosity_gap", "empathy", "shock", "visual_satisfaction", "educational"] = "curiosity_gap"
    hook_trigger_reason: str = ""
    retention_strategy: str = ""
    emotional_mapping: str = ""

# ==================== REMIX SUGGESTIONS ====================
class RemixSuggestion(BaseModel):
    target_niche: str
    concept: str
    key_elements_to_keep: List[str] = Field(default_factory=list)
    suggested_twist: str = ""

# ==================== CAPSULE BRIEF ====================
class ShotlistItem(BaseModel):
    seq: int
    duration: float
    action: str
    shot: str = "MS"

class CapsuleAudio(BaseModel):
    music_style: str = ""
    sfx_cues: List[str] = Field(default_factory=list)
    rhythm: str = "variable"  # Relaxed: fast, slow, variable, etc.

class CapsuleScene(BaseModel):
    location: str = ""
    props: List[str] = Field(default_factory=list)
    mood: str = ""

class CapsuleTiming(BaseModel):
    total_duration: float = 15.0
    hook_duration: float = 2.5
    avg_cut_length: float = 1.5
    tempo_changes: List[str] = Field(default_factory=list)

class CapsuleBrief(BaseModel):
    hook: str = ""
    shotlist: List[ShotlistItem] = Field(default_factory=list)
    audio: CapsuleAudio = Field(default_factory=CapsuleAudio)
    scene: CapsuleScene = Field(default_factory=CapsuleScene)
    timing: CapsuleTiming = Field(default_factory=CapsuleTiming)
    do_not: List[str] = Field(default_factory=list)

# ==================== MAIN VDP GOLD MODEL ====================
class VDPGold(BaseModel):
    """
    Complete Video Data Product - Gold Standard
    Combines original VDP structure with Gemini 3.0 Pro Intent Layer
    """
    # Metadata
    content_id: str
    platform: Literal["youtube", "tiktok", "instagram"] = "youtube"
    source_url: str = ""
    upload_date: Optional[str] = None
    duration_sec: float = 0.0
    metrics: VideoMetrics = Field(default_factory=VideoMetrics)
    
    # Core Analysis
    overall_analysis: OverallAnalysis = Field(default_factory=OverallAnalysis)
    scenes: List[Scene] = Field(default_factory=list)
    product_mentions: List[ProductMention] = Field(default_factory=list)
    scene_comment_map: List[SceneCommentMap] = Field(default_factory=list)
    cross_scene_analysis: CrossSceneAnalysis = Field(default_factory=CrossSceneAnalysis)
    
    # Gemini 3.0 Pro Extensions
    intent_layer: IntentLayer = Field(default_factory=IntentLayer)
    remix_suggestions: List[RemixSuggestion] = Field(default_factory=list)
    
    # Capsule Output (for Canvas Guide Node)
    capsule_brief: CapsuleBrief = Field(default_factory=CapsuleBrief)
    
    # Legacy Compatibility
    global_context: Optional[Dict[str, Any]] = None
    scene_frames: Optional[List[Dict[str, Any]]] = None
