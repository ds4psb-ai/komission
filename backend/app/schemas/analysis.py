from pydantic import BaseModel, Field
from typing import List, Optional

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

class GeminiAnalysisResult(BaseModel):
    video_id: str
    metadata: AudioMetadata
    visual_dna: VisualDNA
    commerce_context: CommerceContext
    meme_dna: MemeDNA
