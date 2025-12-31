"""
Progressive VDG schema testing - find exact breaking point
"""
import google.genai as genai
from google.genai import types
from app.config import settings
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os

# === Level 1: Core VDG (works) ===
class VDGLevel1(BaseModel):
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    summary: str = ""

# === Level 2: Add Hook (based on original VDG) ===
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

class VDGLevel2(BaseModel):
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    summary: str = ""
    hook_genome: HookGenome = Field(default_factory=HookGenome)

# === Level 3: Add Scenes ===
class Camera(BaseModel):
    shot: str = "MS"
    angle: str = "eye"
    move: str = "static"

class Shot(BaseModel):
    shot_id: str
    start: float
    end: float
    camera: Camera = Field(default_factory=Camera)

class NarrativeUnit(BaseModel):
    role: str = "Development"
    summary: str = ""
    dialogue: Optional[str] = None

class Scene(BaseModel):
    scene_id: str
    time_start: float
    time_end: float
    duration_sec: float
    narrative_unit: NarrativeUnit = Field(default_factory=NarrativeUnit)
    shots: List[Shot] = Field(default_factory=list)

class VDGLevel3(BaseModel):
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    summary: str = ""
    hook_genome: HookGenome = Field(default_factory=HookGenome)
    scenes: List[Scene] = Field(default_factory=list)

# === Level 4: Add Focus Windows with Dict[str, float] ===
class FocusWindowHotspot(BaseModel):
    reasons: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)  # <-- THIS IS SUSPICIOUS
    confidence: float = 0.8

class FocusWindow(BaseModel):
    window_id: str
    t_window: List[float] = Field(default_factory=list)
    hotspot: FocusWindowHotspot = Field(default_factory=FocusWindowHotspot)

class VDGLevel4(BaseModel):
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    summary: str = ""
    hook_genome: HookGenome = Field(default_factory=HookGenome)
    scenes: List[Scene] = Field(default_factory=list)
    focus_windows: List[FocusWindow] = Field(default_factory=list)

# === Level 5: Add Dict[str, Any] ===
class FocusWindowHotspotWithAny(BaseModel):
    reasons: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    source_evidence: Dict[str, Any] = Field(default_factory=dict)  # <-- Dict[str, Any]
    confidence: float = 0.8

class FocusWindowWithAny(BaseModel):
    window_id: str
    t_window: List[float] = Field(default_factory=list)
    hotspot: FocusWindowHotspotWithAny = Field(default_factory=FocusWindowHotspotWithAny)

class VDGLevel5(BaseModel):
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    summary: str = ""
    focus_windows: List[FocusWindowWithAny] = Field(default_factory=list)


def test_level(level_name: str, schema_class):
    print(f"\n{'='*50}")
    print(f"Testing {level_name}: {schema_class.__name__}")
    print(f"Fields: {len(schema_class.model_fields)}")
    
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    video_path = '/var/folders/dx/3ncv415x2bz4x54ydrcn4hsh0000gn/T/FjTVH7gIIi0.mp4'
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    
    try:
        response = client.models.generate_content(
            model='models/gemini-3-pro-preview',
            contents=[
                types.Part.from_bytes(data=video_bytes, mime_type='video/mp4'),
                'Analyze this video according to the schema.'
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema_class.model_json_schema()
            )
        )
        print(f"✅ SUCCESS! Response length: {len(response.text)} chars")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


if __name__ == "__main__":
    print("Progressive VDG Schema Testing")
    print("Finding exact breaking point...")
    
    levels = [
        ("Level 1: Core", VDGLevel1),
        ("Level 2: +Hook", VDGLevel2),
        ("Level 3: +Scenes", VDGLevel3),
        ("Level 4: +FocusWindow Dict[str, float]", VDGLevel4),
        ("Level 5: +Dict[str, Any]", VDGLevel5),
    ]
    
    for level_name, schema_class in levels:
        success = test_level(level_name, schema_class)
        if not success:
            print(f"\n🔴 BREAKING POINT FOUND: {level_name}")
            break
    else:
        print("\n🟢 ALL LEVELS PASSED!")
