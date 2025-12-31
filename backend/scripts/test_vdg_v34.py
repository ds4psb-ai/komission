"""
Test VDG v3.4 schema with Gemini 3 Pro
"""
import google.genai as genai
from google.genai import types
from app.config import settings
from app.schemas.vdg_v34 import VDGv34
import os

print("Testing VDG v3.4 schema...")
print(f"Total fields in main model: {len(VDGv34.model_fields)}")

client = genai.Client(api_key=settings.GEMINI_API_KEY)

video_path = '/var/folders/dx/3ncv415x2bz4x54ydrcn4hsh0000gn/T/FjTVH7gIIi0.mp4'
print(f"Video: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB")

with open(video_path, 'rb') as f:
    video_bytes = f.read()

VDG_PROMPT = """
이 바이럴 영상을 VDG (Video Data Graph) v3.4 형식으로 분석하세요.

분석할 내용:
1. 영상 메타데이터 (제목, 길이, 플랫폼)
2. 훅 분석 (0-3초, 주의를 끄는 방법)
3. 씬 분해 (각 장면의 카메라, 조명, 내러티브)
4. 심리 분석 (도파민 레이더, 감정 아크)
5. 바이럴 신호 및 리믹스 제안
6. 상업적 요소 (제품 언급 여부)

한국어로 분석하되, 영어 필드명을 그대로 사용하세요.
"""

print("Calling Gemini with VDG v3.4 schema...")
try:
    response = client.models.generate_content(
        model='models/gemini-3-pro-preview',
        contents=[
            types.Part.from_bytes(data=video_bytes, mime_type='video/mp4'),
            VDG_PROMPT
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VDGv34.model_json_schema()
        )
    )
    print("SUCCESS with VDG v3.4!")
    print(f"Response length: {len(response.text)} chars")
    print(f"Response preview: {response.text[:800]}...")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
