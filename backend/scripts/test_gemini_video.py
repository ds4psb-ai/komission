import google.genai as genai
from google.genai import types
from app.config import settings
import os

print("Starting test...")

client = genai.Client(api_key=settings.GEMINI_API_KEY)

video_path = '/var/folders/dx/3ncv415x2bz4x54ydrcn4hsh0000gn/T/FjTVH7gIIi0.mp4'
print(f"Video: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB")

with open(video_path, 'rb') as f:
    video_bytes = f.read()

print("Calling Gemini 3 Pro Preview...")
try:
    response = client.models.generate_content(
        model='models/gemini-3-pro-preview',
        contents=[
            types.Part.from_bytes(data=video_bytes, mime_type='video/mp4'),
            'Describe this video briefly in 2 sentences.'
        ]
    )
    print("SUCCESS!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
