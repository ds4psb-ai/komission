from pydantic import BaseModel, Field
from typing import List, Optional

# --- Phase 1: Basic Metadata ---
class AudioMetadata(BaseModel):
    title: str = Field(..., description="Music title")
    artist: str = Field(..., description="Music artist")
    bpm: int = Field(..., description="Beats per minute")
    music_drop_timestamps: List[float] = Field(..., description="Timestamps of drops/highlights")
    mood: str = Field(..., description="Audio mood")

class VisualDNA(BaseModel):
    setting_description: str = Field(..., description="Description of the video setting")
    camera_movement: str = Field(..., description="Type of camera movement (static, pan, zoom, etc.)")
    lighting: str = Field(..., description="Lighting condition")
    color_palette: List[str] = Field(..., description="Dominant colors")

class CommerceContext(BaseModel):
    primary_category: str = Field(..., description="Main product category (e.g., beauty, fitness)")
    keywords: List[str] = Field(..., description="Relevant keywords for commerce")
    suitable_products: List[str] = Field(..., description="Types of products suitable for this video")

class MemeDNA(BaseModel):
    catchphrase: Optional[str] = Field(None, description="Key catchphrase if any")
    key_action: str = Field(..., description="The main repeatable action/dance move")
    humor_point: str = Field(..., description="What makes this funny or viral")

# --- Phase 2: Advanced Temporal & Spatial ---
class TimeSegment(BaseModel):
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    description: str = Field(..., description="Detailed description of action/event in this segment")
    visual_tags: List[str] = Field(..., description="Tags for visual elements (e.g., 'jump', 'smile')")
    audio_tags: List[str] = Field(..., description="Tags for audio elements (e.g., 'bass_drop', 'lyrics')")
    viral_score: int = Field(..., description="Virality score of this specific segment (1-10)")

class ViralHook(BaseModel):
    timestamp: float = Field(..., description="Exact timestamp of the hook")
    hook_type: str = Field(..., description="Type of hook (visual_shock, audio_drop, plot_twist, relatability)")
    description: str = Field(..., description="Why this moment captures attention")

class GeminiAnalysisResult(BaseModel):
    video_id: str
    
    # Basic
    metadata: AudioMetadata
    visual_dna: VisualDNA
    commerce_context: CommerceContext
    meme_dna: MemeDNA
    
    # Advanced
    timeline: List[TimeSegment] = Field(default_factory=list, description="Second-by-second breakdown")
    viral_hooks: List[ViralHook] = Field(default_factory=list, description="Key engaging moments")
    
    # Metrics
    virality_score: int = Field(0, description="Overall virality prediction (0-100)")
    imitability_level: str = Field("Medium", description="How easy it is to replicate (Easy, Medium, Hard)")
