import google.genai as genai
from google.genai import types
from app.config import settings
from app.schemas.analysis_schema import VideoAnalysisSchema
import os

print("Testing with analysis_schema.VideoAnalysisSchema...")
print(f"Schema has {len(VideoAnalysisSchema.model_fields)} fields")

client = genai.Client(api_key=settings.GEMINI_API_KEY)

video_path = '/var/folders/dx/3ncv415x2bz4x54ydrcn4hsh0000gn/T/FjTVH7gIIi0.mp4'
print(f"Video: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB")

with open(video_path, 'rb') as f:
    video_bytes = f.read()

print("Sending to Gemini...")
try:
    response = client.models.generate_content(
        model='models/gemini-3-pro-preview',
        contents=[
            types.Part.from_bytes(data=video_bytes, mime_type='video/mp4'),
            'Analyze this video according to the provided schema.'
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoAnalysisSchema.model_json_schema()
        )
    )
    print("SUCCESS with simple schema!")
    print(f"Response: {response.text[:500]}...")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
