"""
VDG (Video Data Graph) v3.2
Complete schema with O2O product detection, audience reaction, and legacy essentials.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ==================== METADATA & METRICS ====================
class VideoMetrics(BaseModel):
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: Optional[int] = None
    hashtags: List[str] = Field(default_factory=list)  # 해시태그

# ==================== HOOK MICROBEATS ====================
class Microbeat(BaseModel):
    """Hook 내 세부 비트 (레거시 필수)"""
    t: float  # 타임스탬프
    role: str = "start"  # start | build | punch | end
    cue: str = "visual"  # visual | audio | text | action
    note: str = ""  # 설명

class ViralityAnalysis(BaseModel):
    """바이럴 핵심 분석 (레거시 필수)"""
    curiosity_gap: str = ""  # 호기심 유발 요소 (질문 형태로)
    meme_potential: str = "low"  # remixable_action | catchphrase | reaction_face | dance | low
    relatability_factor: str = ""  # 공감 요소 (surprise_reveal, everyday_struggle 등)
    engagement_pattern: str = "scroll_stop"  # watch_in_loop | scroll_stop | share_trigger | comment_bait

# ==================== PSYCHOLOGY & HOOK ====================
class HookGenome(BaseModel):
    start_sec: float = 0.0
    end_sec: float = 3.0
    pattern: str = "other"  # problem_solution, pattern_break, subversion
    delivery: str = "visual_gag"  # dialogue, voiceover, visual_gag
    strength: float = Field(0.5, ge=0.0, le=1.0)
    hook_summary: str = ""
    
    # Legacy Essential Fields
    microbeats: List[Microbeat] = Field(default_factory=list)
    virality_analysis: ViralityAnalysis = Field(default_factory=ViralityAnalysis)
    information_density: str = "medium"  # low | medium | high

class DopamineRadar(BaseModel):
    """How this video stimulates the brain (0-10 scale)"""
    visual_spectacle: int = Field(5, ge=0, le=10)
    audio_stimulation: int = Field(5, ge=0, le=10)
    narrative_intrigue: int = Field(5, ge=0, le=10)
    emotional_resonance: int = Field(5, ge=0, le=10)
    comedy_shock: int = Field(5, ge=0, le=10)

class IronyAnalysis(BaseModel):
    """Analysis of expectation vs reality gaps"""
    setup: str = ""
    twist: str = ""
    gap_type: str = "none"  # visual_audio_mismatch, expectation_subversion

# ==================== SENTIMENT TRACKING ====================
class SentimentShift(BaseModel):
    """감정 변화 포인트 (레거시 필수)"""
    t: float  # 타임스탬프
    from_emotion: str
    to_emotion: str
    cue: str = ""  # 변화 트리거

class SentimentArc(BaseModel):
    """전체 감정 아크"""
    start_sentiment: str = "neutral"
    end_sentiment: str = "positive"
    micro_shifts: List[SentimentShift] = Field(default_factory=list)
    trajectory: str = ""  # 전체 감정 흐름 요약

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
    dialogue_lang: str = ""  # ko, en, etc.
    dialogue_translation_en: Optional[str] = None  # 영어 번역
    
    # Legacy Essential: 수사법/코미디 기법
    rhetoric: List[str] = Field(default_factory=list)  # sarcasm, rhetorical_question
    comedic_device: List[str] = Field(default_factory=list)  # expectation_subversion, anticlimax

class Scene(BaseModel):
    scene_id: str
    time_start: float
    time_end: float
    duration_sec: float
    narrative_unit: NarrativeUnit = Field(default_factory=NarrativeUnit)
    setting: Setting = Field(default_factory=Setting)
    shots: List[Shot] = Field(default_factory=list)

# ==================== REPLICATION GUIDE (CAPSULE) ====================
class ProductionConstraints(BaseModel):
    """The 'Bill of Materials' for creating this video"""
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
    """체험단 제품 배치 가이드"""
    recommended_timing: str = ""  # 제품 등장 추천 시점
    invariant_elements: List[str] = Field(default_factory=list)  # 반드시 유지할 요소
    variable_elements: List[str] = Field(default_factory=list)  # 변주 가능한 요소
    product_slot: str = ""  # 제품 삽입 위치

class CapsuleBrief(BaseModel):
    """Actionable guide for the creator"""
    hook_script: str = ""
    shotlist: List[ShotlistItem] = Field(default_factory=list)
    constraints: ProductionConstraints = Field(default_factory=ProductionConstraints)
    do_not: List[str] = Field(default_factory=list)
    product_placement_guide: ProductPlacementGuide = Field(default_factory=ProductPlacementGuide)

# ==================== REMIX & INTENT ====================
class IntentLayer(BaseModel):
    hook_trigger: str = "curiosity_gap"
    hook_trigger_reason: str = ""
    retention_strategy: str = ""
    irony_analysis: IronyAnalysis = Field(default_factory=IronyAnalysis)
    dopamine_radar: DopamineRadar = Field(default_factory=DopamineRadar)
    sentiment_arc: SentimentArc = Field(default_factory=SentimentArc)  # NEW

class RemixSuggestion(BaseModel):
    """변주 제안 - 체험단 적용 가이드"""
    target_niche: str  # 타겟 크리에이터 유형
    concept: str  # 변주 컨셉
    template_type: str = "re_enact"  # re_enact | mashup | parody | product_placement
    viral_element_to_keep: str = ""  # 유지해야 할 바이럴 요소
    variable_elements: List[str] = Field(default_factory=list)  # 변경 가능한 요소들

# ==================== O2O COMMERCE (레거시 필수) ====================
class ProductMention(BaseModel):
    """제품/브랜드 언급"""
    name: str
    brand: Optional[str] = None
    category: str = ""  # beauty, food, fashion, tech
    timestamp: float = 0.0
    mention_type: str = "visual"  # visual | verbal | both

class Commerce(BaseModel):
    """O2O 커머스 분석"""
    product_mentions: List[ProductMention] = Field(default_factory=list)
    service_mentions: List[str] = Field(default_factory=list)
    cta_types: List[str] = Field(default_factory=list)  # link_bio, swipe_up, discount_code
    has_sponsored_content: bool = False

# ==================== AUDIENCE REACTION ====================
class NotableComment(BaseModel):
    """베스트 댓글"""
    text: str
    likes: int = 0
    author: str = ""
    lang: str = "en"
    translation_en: Optional[str] = None

class AudienceReaction(BaseModel):
    """시청자 반응 분석 (댓글 기반)"""
    analysis: str = ""  # 전체 분석 요약
    best_comments: List[NotableComment] = Field(default_factory=list)
    common_reactions: List[str] = Field(default_factory=list)  # 웃김, 공감, 충격
    overall_sentiment: str = "positive"
    viral_signal: str = ""  # 왜 바이럴됐는지 핵심 이유

# ==================== FOCUS WINDOW (v3.3) ====================
# v3.6: Dict fields replaced with typed objects for Gemini structured output
class HotspotScores(BaseModel):
    """Typed hotspot scores (replaces Dict[str, float])"""
    hook: float = 0.0
    interest: float = 0.0
    boundary: float = 0.0

class SourceEvidence(BaseModel):
    """Typed source evidence (replaces Dict[str, Any])"""
    cue_type: str = ""
    description: str = ""
    evidence_list: List[str] = Field(default_factory=list)

class FocusWindowHotspot(BaseModel):
    """구간별 주목도 분석"""
    reasons: List[str] = Field(default_factory=list)
    scores: HotspotScores = Field(default_factory=HotspotScores)
    confidence: float = 0.8
    source_evidence: SourceEvidence = Field(default_factory=SourceEvidence)

class CompositionSpec(BaseModel):
    """Typed composition (replaces Dict[str, Any])"""
    grid: str = "center"
    subject_size: str = "MS"

class LightingSpec(BaseModel):
    """Typed lighting (replaces Dict[str, str])"""
    type: str = "natural"
    intensity: str = "medium"

class LensSpec(BaseModel):
    """Typed lens (replaces Dict[str, str])"""
    fov_class: str = "normal"
    dof: str = "medium"

class FocusWindowMiseEnScene(BaseModel):
    """구간 내 미장센 분석"""
    composition: CompositionSpec = Field(default_factory=CompositionSpec)
    lighting: LightingSpec = Field(default_factory=LightingSpec)
    lens: LensSpec = Field(default_factory=LensSpec)
    camera_move: str = "static"

class EntityTraits(BaseModel):
    """Typed entity traits (replaces Dict[str, Any])"""
    pose: str = ""
    emotion: str = "neutral"
    outfit_color: str = ""

class FocusWindowEntity(BaseModel):
    """구간 내 엔티티 (인물/객체)"""
    label: str
    traits: EntityTraits = Field(default_factory=EntityTraits)
    role_in_window: str = "SUBJECT"

class FocusWindowTags(BaseModel):
    """Typed tags (replaces Dict[str, List[str]])"""
    narrative_roles: List[str] = Field(default_factory=list)
    cinematic: List[str] = Field(default_factory=list)

class FocusWindow(BaseModel):
    """특정 시간 구간의 집중 분석 (RL 보상 신호용)"""
    window_id: str
    t_window: List[float] = Field(default_factory=list)
    hotspot: FocusWindowHotspot = Field(default_factory=FocusWindowHotspot)
    mise_en_scene: FocusWindowMiseEnScene = Field(default_factory=FocusWindowMiseEnScene)
    entities: List[FocusWindowEntity] = Field(default_factory=list)
    parent_scene_id: Optional[str] = None
    tags: FocusWindowTags = Field(default_factory=FocusWindowTags)

# ==================== CROSS-SCENE ANALYSIS (v3.3) ====================
class DirectorIntentEvidence(BaseModel):
    """Typed evidence (replaces Dict[str, Any])"""
    scenes: List[str] = Field(default_factory=list)
    cues: List[str] = Field(default_factory=list)

class DirectorIntent(BaseModel):
    """연출 의도 분석"""
    technique: str = ""
    intended_effect: str = ""
    rationale: str = ""
    evidence: DirectorIntentEvidence = Field(default_factory=DirectorIntentEvidence)

class EntityStateChange(BaseModel):
    """캐릭터/객체 상태 변화 추적"""
    entity_id: str
    initial_state: str
    final_state: str
    triggering_event: str
    scene_id: str
    time_span: List[float] = Field(default_factory=list)

class ConsistentElement(BaseModel):
    """씬 간 일관된 요소"""
    aspect: str  # composition, comedic_device, aesthetic
    evidence: str
    scenes: List[str] = Field(default_factory=list)

class EvolvingElement(BaseModel):
    """씬 간 변화하는 요소"""
    dimension: str  # pacing, emotion_arc, character_outfit
    description: str
    evidence: str
    pattern: str = "unknown"  # steady, escalating, oscillating

class CrossSceneAnalysis(BaseModel):
    """전체 영상의 씬 간 관계 분석"""
    global_summary: str = ""
    consistent_elements: List[ConsistentElement] = Field(default_factory=list)
    evolving_elements: List[EvolvingElement] = Field(default_factory=list)
    director_intent: List[DirectorIntent] = Field(default_factory=list)
    entity_state_changes: List[EntityStateChange] = Field(default_factory=list)

# ==================== ASR/OCR (v3.3) ====================
class OCRItem(BaseModel):
    """화면 내 텍스트"""
    text: str
    lang: str = "en"
    translation_en: Optional[str] = None
    timestamp: Optional[float] = None

class ASRTranscript(BaseModel):
    """음성 인식 결과"""
    lang: str = "en"
    transcript: str = ""
    translation_en: Optional[str] = None

# ==================== MAIN VDG MODEL ====================
class VDG(BaseModel):
    """
    VDG (Video Data Graph) v3.3
    Complete schema with O2O, audience reaction, focus windows, and cross-scene analysis.
    
    v3.3 Changes:
    - Added focus_windows (RL reward signals)
    - Added cross_scene_analysis (pattern synthesis)
    - Added asr_transcript, ocr_text (explicit extraction)
    - Added upload_date for temporal context
    """
    # Identity
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    upload_date: Optional[str] = None  # NEW v3.3
    metrics: VideoMetrics = Field(default_factory=VideoMetrics)
    
    # Core Analysis
    summary: str = ""
    hook_genome: HookGenome = Field(default_factory=HookGenome)
    
    # The Meat (Structure)
    scenes: List[Scene] = Field(default_factory=list)
    
    # The Brain (Psychology)
    intent_layer: IntentLayer = Field(default_factory=IntentLayer)
    
    # Focus Windows (NEW v3.3 - RL reward signals)
    focus_windows: List[FocusWindow] = Field(default_factory=list)
    
    # Cross-Scene Analysis (NEW v3.3 - pattern synthesis)
    cross_scene_analysis: CrossSceneAnalysis = Field(default_factory=CrossSceneAnalysis)
    
    # ASR/OCR (NEW v3.3 - explicit extraction)
    asr_transcript: ASRTranscript = Field(default_factory=ASRTranscript)
    ocr_text: List[OCRItem] = Field(default_factory=list)
    
    # The Future (Action)
    remix_suggestions: List[RemixSuggestion] = Field(default_factory=list)
    capsule_brief: CapsuleBrief = Field(default_factory=CapsuleBrief)
    
    # O2O Commerce
    commerce: Commerce = Field(default_factory=Commerce)
    
    # Audience Reaction
    audience_reaction: AudienceReaction = Field(default_factory=AudienceReaction)
    
    # Note: Legacy fields (global_context, scene_frames) removed for Gemini structured output compatibility

