"""
Test VDG schema step by step to find the breaking point
"""
import google.genai as genai
from google.genai import types
from app.config import settings
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os

# Simple test schema based on VDG structure
class SimpleHook(BaseModel):
    start_sec: float = 0.0
    end_sec: float = 3.0
    pattern: str = "other"
    strength: float = Field(0.5, ge=0.0, le=1.0)
    hook_summary: str = ""

class SimpleScene(BaseModel):
    scene_id: str
    time_start: float
    time_end: float
    summary: str = ""

class VDGSimple(BaseModel):
    """Simplified VDG for testing"""
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    summary: str = ""
    hook: SimpleHook = Field(default_factory=SimpleHook)
    scenes: List[SimpleScene] = Field(default_factory=list)

print("Testing VDG-Simple schema...")
print(f"Schema: {VDGSimple.__name__}")

client = genai.Client(api_key=settings.GEMINI_API_KEY)

video_path = '/var/folders/dx/3ncv415x2bz4x54ydrcn4hsh0000gn/T/FjTVH7gIIi0.mp4'
print(f"Video: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB")

with open(video_path, 'rb') as f:
    video_bytes = f.read()

print("Calling Gemini with VDG-Simple...")
try:
    response = client.models.generate_content(
        model='models/gemini-3-pro-preview',
        contents=[
            types.Part.from_bytes(data=video_bytes, mime_type='video/mp4'),
            '''Analyze this video in VDG format. Identify:
            - Content ID (video identifier)
            - Platform
            - Title
            - Duration
            - Summary
            - Hook analysis (0-3 seconds)
            - Scene breakdown'''
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VDGSimple.model_json_schema()
        )
    )
    print("SUCCESS with VDG-Simple!")
    print(f"Response: {response.text[:600]}...")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
