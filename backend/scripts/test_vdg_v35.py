"""
Test VDG v3.5 - Full schema with all Dict replaced
"""
import google.genai as genai
from google.genai import types
from app.config import settings
from app.schemas.vdg_v35 import VDGv35
import os
import json

print("Testing VDG v3.5 (Full schema, no Dict)")
print(f"Total fields in main model: {len(VDGv35.model_fields)}")

client = genai.Client(api_key=settings.GEMINI_API_KEY)

video_path = '/var/folders/dx/3ncv415x2bz4x54ydrcn4hsh0000gn/T/FjTVH7gIIi0.mp4'
print(f"Video: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB")

with open(video_path, 'rb') as f:
    video_bytes = f.read()

VDG_PROMPT = """
이 바이럴 영상을 VDG (Video Data Graph) v3.5 형식으로 완전히 분석하세요.

분석할 내용:
1. 영상 메타데이터 (제목, 길이, 플랫폼, 메트릭스)
2. 훅 분석 (0-3초, microbeats, virality_analysis)
3. 씬 분해 (각 장면의 카메라, 조명, 내러티브, shots)
4. 심리 분석 (dopamine_radar, irony_analysis, sentiment_arc)
5. Focus Windows (주목 구간 3-5개, hotspot scores, mise_en_scene)
6. Cross-Scene Analysis (일관된 요소, 변화하는 요소, 연출 의도)
7. ASR/OCR (음성 전사, 화면 텍스트)
8. 리믹스 제안 (최소 2개)
9. Capsule Brief (shotlist, 제작 가이드)
10. 상업적 요소 (제품 언급 여부)
11. 시청자 반응 분석

한국어로 분석하되, 영어 필드명을 그대로 사용하세요.
"""

print("Calling Gemini with VDG v3.5 full schema...")
try:
    response = client.models.generate_content(
        model='models/gemini-3-pro-preview',
        contents=[
            types.Part.from_bytes(data=video_bytes, mime_type='video/mp4'),
            VDG_PROMPT
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VDGv35.model_json_schema()
        )
    )
    print("✅ SUCCESS with VDG v3.5!")
    print(f"Response length: {len(response.text)} chars")
    
    # Parse and validate
    data = json.loads(response.text)
    vdg = VDGv35(**data)
    print(f"\nParsed successfully!")
    print(f"  Title: {vdg.title}")
    print(f"  Scenes: {len(vdg.scenes)}")
    print(f"  Focus Windows: {len(vdg.focus_windows)}")
    print(f"  Remix Suggestions: {len(vdg.remix_suggestions)}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
