
import asyncio
import json
import os
import sys
from google import genai
from google.genai import types

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.video_downloader import video_downloader

api_key = 'AIzaSyDb5LT4hWlq0P7gmriQACWpJxYeE8KbkaQ'
client = genai.Client(api_key=api_key)

async def test_vdg_v2():
    print('🎥 Downloading video...')
    video_url = 'https://www.youtube.com/shorts/d_ScVrX_ulI'
    file_path, _ = await video_downloader.download(video_url)
    print(f'✅ Downloaded: {file_path}')

    print('⬆️ Uploading to Gemini...')
    video_file = client.files.upload(file=file_path)
    
    import time
    while True:
        info = client.files.get(name=video_file.name)
        if info.state.name == 'ACTIVE':
            break
        print('⏳ Waiting for processing...')
        time.sleep(2)

    prompt = """
    You are a Viral Video Director & Psychologist AI (Gemini 3.0 Pro).
    Your goal is to deconstruct this video into a "Video Data Graph (VDG)" so that a creator can replicate its viral success.
    
    Analyze the video deeply in one pass. Focus on:
    1. **Hook Genome**: The DNA of the first 3 seconds.
    2. **Deep Intent**: "Why" it went viral (psychological triggers).
    3. **Production Recipe**: "How" to shoot it (shot list, audio cues).
    4. **Remix Potential**: How to adapt this for other niches.

    ### Output Schema (JSON Only)
    {
      "meta_info": {
        "duration": "float (seconds)",
        "platform": "youtube|tiktok|instagram",
        "dominant_lang": "code (en, ko)"
      },
      "hook_genome": {
        "pattern": "problem_solution|pattern_break|question|proof|other",
        "delivery": "dialogue|voiceover|text_overlay|visual_gag|sfx_only",
        "strength_score": "0.0-1.0",
        "hook_summary": "One sentence summary of the hook"
      },
      "intent_analysis": {
        "hook_trigger": "curiosity_gap|empathy|shock|visual_satisfaction|educational",
        "hook_trigger_reason": "Deep explanation of why this hook grabs attention",
        "emotional_journey": [
            {"time": "range (e.g. 0-3s)", "emotion": "string", "intensity": "0.0-1.0"}
        ],
        "retention_strategy": "How the video keeps viewers watching until the end"
      },
      "production_recipe": {
        "visual_style": "cinematic|vlog|lo-fi|studio",
        "shot_list": [
            {
                "id": "int",
                "time_range": [0.0, 0.0],
                "shot_size": "CU|MS|WS|ECU",
                "action": "Detailed description of action",
                "camera_movement": "static|pan|tilt|dolly|handheld",
                "reference_energy": "low|medium|high"
            }
        ],
        "audio_cues": [
            {"time": 0.0, "type": "speech|bgm|sfx", "description": "string"}
        ],
        "visual_rhythm": {
            "bpm_feel": "int",
            "cut_density": "low|medium|high",
            "sync_points": [0.0]
        }
      },
      "remix_potentials": [
        {
            "target_niche": "string (e.g. office, student, parenting)",
            "concept": "Specific idea for remixing this video"
        }
      ]
    }
    """

    print('🧠 Analyzing with Gemini 3 Pro (VDG v2.0)...')
    response = client.models.generate_content(
        model='gemini-3-pro-preview',
        contents=[video_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type='application/json'
        )
    )

    print('\n✅ VDG v2.0 RESULT:')
    print(response.text)
    
    os.remove(file_path)

if __name__ == "__main__":
    asyncio.run(test_vdg_v2())
