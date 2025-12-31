"""
VDG v3.4 - Gemini 3 Pro Structured Output Compatible
Removed Dict[str, Any] fields that cause 500 errors
"""
from pydantic import BaseModel, Field
from typing import List, Optional

# ==================== METADATA & METRICS ====================
class VideoMetrics(BaseModel):
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: Optional[int] = None
    hashtags: List[str] = Field(default_factory=list)

# ==================== HOOK MICROBEATS ====================
class Microbeat(BaseModel):
    t: float
    role: str = "start"
    cue: str = "visual"
    note: str = ""

class ViralityAnalysis(BaseModel):
    curiosity_gap: str = ""
    meme_potential: str = "low"
    relatability_factor: str = ""
    engagement_pattern: str = "scroll_stop"

# ==================== PSYCHOLOGY & HOOK ====================
class HookGenome(BaseModel):
    start_sec: float = 0.0
    end_sec: float = 3.0
    pattern: str = "other"
    delivery: str = "visual_gag"
    strength: float = Field(0.5, ge=0.0, le=1.0)
    hook_summary: str = ""
    microbeats: List[Microbeat] = Field(default_factory=list)
    virality_analysis: ViralityAnalysis = Field(default_factory=ViralityAnalysis)
    information_density: str = "medium"

class DopamineRadar(BaseModel):
    visual_spectacle: int = Field(5, ge=0, le=10)
    audio_stimulation: int = Field(5, ge=0, le=10)
    narrative_intrigue: int = Field(5, ge=0, le=10)
    emotional_resonance: int = Field(5, ge=0, le=10)
    comedy_shock: int = Field(5, ge=0, le=10)

class IronyAnalysis(BaseModel):
    setup: str = ""
    twist: str = ""
    gap_type: str = "none"

# ==================== SENTIMENT TRACKING ====================
class SentimentShift(BaseModel):
    t: float
    from_emotion: str
    to_emotion: str
    cue: str = ""

class SentimentArc(BaseModel):
    start_sentiment: str = "neutral"
    end_sentiment: str = "positive"
    micro_shifts: List[SentimentShift] = Field(default_factory=list)
    trajectory: str = ""

# ==================== PRODUCTION & STRUCTURE ====================
class AudioEvent(BaseModel):
    timestamp: float
    event: str = "sfx_hit"
    description: str = ""
    intensity: str = "medium"

class AudioStyle(BaseModel):
    music: str = ""
    ambient_sound: str = ""
    tone: str = ""
    audio_events: List[AudioEvent] = Field(default_factory=list)

class Keyframe(BaseModel):
    role: str = "start"
    desc: str = ""
    t_rel_shot: float = 0.0

class Camera(BaseModel):
    shot: str = "MS"
    angle: str = "eye"
    move: str = "static"

class Composition(BaseModel):
    grid: str = "center"
    notes: List[str] = Field(default_factory=list)

class Shot(BaseModel):
    shot_id: str
    start: float
    end: float
    camera: Camera = Field(default_factory=Camera)
    composition: Composition = Field(default_factory=Composition)
    keyframes: List[Keyframe] = Field(default_factory=list)
    confidence: str = "medium"

class VisualStyle(BaseModel):
    lighting: str = ""
    mood_palette: List[str] = Field(default_factory=list)
    edit_pace: str = "medium"

class Setting(BaseModel):
    location: str = ""
    visual_style: VisualStyle = Field(default_factory=VisualStyle)
    audio_style: AudioStyle = Field(default_factory=AudioStyle)

class NarrativeUnit(BaseModel):
    role: str = "Development"
    summary: str = ""
    dialogue: Optional[str] = None
    dialogue_lang: str = ""
    dialogue_translation_en: Optional[str] = None
    rhetoric: List[str] = Field(default_factory=list)
    comedic_device: List[str] = Field(default_factory=list)

class Scene(BaseModel):
    scene_id: str
    time_start: float
    time_end: float
    duration_sec: float
    narrative_unit: NarrativeUnit = Field(default_factory=NarrativeUnit)
    setting: Setting = Field(default_factory=Setting)
    shots: List[Shot] = Field(default_factory=list)

# ==================== REPLICATION GUIDE ====================
class ProductionConstraints(BaseModel):
    min_actors: int = 1
    locations: List[str] = Field(default_factory=list)
    props: List[str] = Field(default_factory=list)
    difficulty: str = "Medium"
    primary_challenge: str = ""

class ShotlistItem(BaseModel):
    seq: int
    duration: float
    action: str
    shot: str = "MS"

class ProductPlacementGuide(BaseModel):
    recommended_timing: str = ""
    invariant_elements: List[str] = Field(default_factory=list)
    variable_elements: List[str] = Field(default_factory=list)
    product_slot: str = ""

class CapsuleBrief(BaseModel):
    hook_script: str = ""
    shotlist: List[ShotlistItem] = Field(default_factory=list)
    constraints: ProductionConstraints = Field(default_factory=ProductionConstraints)
    do_not: List[str] = Field(default_factory=list)
    product_placement_guide: ProductPlacementGuide = Field(default_factory=ProductPlacementGuide)

# ==================== INTENT ====================
class IntentLayer(BaseModel):
    hook_trigger: str = "curiosity_gap"
    hook_trigger_reason: str = ""
    retention_strategy: str = ""
    irony_analysis: IronyAnalysis = Field(default_factory=IronyAnalysis)
    dopamine_radar: DopamineRadar = Field(default_factory=DopamineRadar)
    sentiment_arc: SentimentArc = Field(default_factory=SentimentArc)

class RemixSuggestion(BaseModel):
    target_niche: str
    concept: str
    template_type: str = "re_enact"
    viral_element_to_keep: str = ""
    variable_elements: List[str] = Field(default_factory=list)

# ==================== O2O COMMERCE ====================
class ProductMention(BaseModel):
    name: str
    brand: Optional[str] = None
    category: str = ""
    timestamp: float = 0.0
    mention_type: str = "visual"

class Commerce(BaseModel):
    product_mentions: List[ProductMention] = Field(default_factory=list)
    service_mentions: List[str] = Field(default_factory=list)
    cta_types: List[str] = Field(default_factory=list)
    has_sponsored_content: bool = False

# ==================== AUDIENCE REACTION ====================
class NotableComment(BaseModel):
    text: str
    likes: int = 0
    author: str = ""
    lang: str = "en"
    translation_en: Optional[str] = None

class AudienceReaction(BaseModel):
    analysis: str = ""
    best_comments: List[NotableComment] = Field(default_factory=list)
    common_reactions: List[str] = Field(default_factory=list)
    overall_sentiment: str = "positive"
    viral_signal: str = ""

# ==================== ASR/OCR ====================
class OCRItem(BaseModel):
    text: str
    lang: str = "en"
    translation_en: Optional[str] = None
    timestamp: Optional[float] = None

class ASRTranscript(BaseModel):
    lang: str = "en"
    transcript: str = ""
    translation_en: Optional[str] = None

# ==================== FOCUS WINDOW (Simplified - no Dict[str, Any]) ====================
class FocusWindowHotspot(BaseModel):
    reasons: List[str] = Field(default_factory=list)
    hook_score: float = 0.0
    interest_score: float = 0.0
    confidence: float = 0.8

class FocusWindowMiseEnScene(BaseModel):
    composition_grid: str = "center"
    subject_size: str = "medium"
    lighting_type: str = "natural"
    lens_fov: str = "normal"
    camera_move: str = "static"

class FocusWindowEntity(BaseModel):
    label: str
    pose: str = ""
    emotion: str = "neutral"
    role_in_window: str = "SUBJECT"

class FocusWindow(BaseModel):
    window_id: str
    start_sec: float = 0.0
    end_sec: float = 0.0
    hotspot: FocusWindowHotspot = Field(default_factory=FocusWindowHotspot)
    mise_en_scene: FocusWindowMiseEnScene = Field(default_factory=FocusWindowMiseEnScene)
    entities: List[FocusWindowEntity] = Field(default_factory=list)
    parent_scene_id: Optional[str] = None
    narrative_roles: List[str] = Field(default_factory=list)
    cinematic_tags: List[str] = Field(default_factory=list)

# ==================== CROSS-SCENE ANALYSIS (Simplified) ====================
class DirectorIntent(BaseModel):
    technique: str = ""
    intended_effect: str = ""
    rationale: str = ""
    evidence_scenes: List[str] = Field(default_factory=list)

class EntityStateChange(BaseModel):
    entity_id: str
    initial_state: str
    final_state: str
    triggering_event: str
    scene_id: str
    start_sec: float = 0.0
    end_sec: float = 0.0

class ConsistentElement(BaseModel):
    aspect: str
    evidence: str
    scenes: List[str] = Field(default_factory=list)

class EvolvingElement(BaseModel):
    dimension: str
    description: str
    evidence: str
    pattern: str = "unknown"

class CrossSceneAnalysis(BaseModel):
    global_summary: str = ""
    consistent_elements: List[ConsistentElement] = Field(default_factory=list)
    evolving_elements: List[EvolvingElement] = Field(default_factory=list)
    director_intent: List[DirectorIntent] = Field(default_factory=list)
    entity_state_changes: List[EntityStateChange] = Field(default_factory=list)

# ==================== MAIN VDG MODEL ====================
class VDGv34(BaseModel):
    """
    VDG (Video Data Graph) v3.4
    Gemini 3 Pro Structured Output Compatible Version
    
    Changes from v3.3:
    - Replaced all Dict[str, Any] with typed fields
    - Removed optional Dict fields
    - Simplified FocusWindow and CrossSceneAnalysis
    """
    # Identity
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    upload_date: Optional[str] = None
    metrics: VideoMetrics = Field(default_factory=VideoMetrics)
    
    # Core Analysis
    summary: str = ""
    hook_genome: HookGenome = Field(default_factory=HookGenome)
    
    # Structure
    scenes: List[Scene] = Field(default_factory=list)
    
    # Psychology
    intent_layer: IntentLayer = Field(default_factory=IntentLayer)
    
    # Focus Windows
    focus_windows: List[FocusWindow] = Field(default_factory=list)
    
    # Cross-Scene Analysis
    cross_scene_analysis: CrossSceneAnalysis = Field(default_factory=CrossSceneAnalysis)
    
    # ASR/OCR
    asr_transcript: ASRTranscript = Field(default_factory=ASRTranscript)
    ocr_text: List[OCRItem] = Field(default_factory=list)
    
    # Action
    remix_suggestions: List[RemixSuggestion] = Field(default_factory=list)
    capsule_brief: CapsuleBrief = Field(default_factory=CapsuleBrief)
    
    # O2O Commerce
    commerce: Commerce = Field(default_factory=Commerce)
    
    # Audience Reaction
    audience_reaction: AudienceReaction = Field(default_factory=AudienceReaction)
