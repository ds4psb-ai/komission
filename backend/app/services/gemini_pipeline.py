"""
Gemini Pipeline - Video Analysis using Google Gemini 3.0 Pro
Uses the new google-genai package (replaces deprecated google-generativeai)
"""
import os
import tempfile
import json
import httpx
from google import genai
from google.genai import types
from app.config import settings
from app.schemas.analysis import GeminiAnalysisResult


class GeminiPipeline:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model = "gemini-2.0-flash" 
        else:
            print("Warning: GEMINI_API_KEY not set")
            self.client = None

    async def _download_video(self, url: str) -> str:
        """Download video from URL to a temporary file"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            
            # Create temp file
            processed_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            processed_file.write(resp.content)
            processed_file.close()
            return processed_file.name

    async def analyze_video(self, video_url: str, video_id: str) -> GeminiAnalysisResult:
        """
        Analyzes a video using Gemini Vision.
        Downloads the video if it's a URL, then uploads to Gemini.
        """
        if not self.client:
            # Fallback for development if no key
            print("⚠️ Gemini API Key missing, returning mock data.")
            return self._get_mock_data(video_id)

        temp_path = None
        try:
            # 1. Prepare Video File
            if video_url.startswith("http"):
                print(f"📥 Downloading video from {video_url}...")
                temp_path = await self._download_video(video_url)
                video_source = temp_path
            else:
                video_source = video_url # Assume local path

            # 2. Upload to Gemini
            print(f"⬆️ Uploading execution for {video_id}...")
            video_file = self.client.files.upload(file=video_source)
            print(f"✅ Upload complete: {video_file.name}")

            # 3. Analyze
            prompt = """
            Analyze this video content for a viral meme factory platform. 
            Extract the following structured data in JSON format:

            1. Audio Metadata: Identify music title, artist, estimate BPM, and list highlight timestamps (drops).
            2. Visual DNA: Describe the setting, camera movement, lighting, and color palette.
            3. Commerce Context: What product category fits this video? (beauty, fitness, food, etc.). Give keywords.
            4. Meme DNA: What is the key action? Is there a catchphrase? What is the humor point?

            Output must strictly follow this JSON structure:
            {
                "metadata": {
                    "title": "str",
                    "artist": "str",
                    "bpm": int,
                    "music_drop_timestamps": [float],
                    "mood": "str"
                },
                "visual_dna": {
                    "setting_description": "str",
                    "camera_movement": "str",
                    "lighting": "str",
                    "color_palette": ["str"]
                },
                "commerce_context": {
                    "primary_category": "str",
                    "keywords": ["str"],
                    "suitable_products": ["str"]
                },
                "meme_dna": {
                    "catchphrase": "str" or null,
                    "key_action": "str",
                    "humor_point": "str"
                }
            }
            """

            print(f"🧠 analyzing {video_id} with {self.model}...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=[video_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            data = json.loads(response.text)
            return GeminiAnalysisResult(video_id=video_id, **data)

        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")
            # In production, might want to re-raise or return error
            # For robustness, we fallback to mock or raise
            raise e
        finally:
            # Cleanup temp file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def _get_mock_data(self, video_id: str) -> GeminiAnalysisResult:
        """Return mock data when API is unavailable"""
        mock_data = {
            "metadata": {
                "title": "Viral Beat",
                "artist": "Unknown",
                "bpm": 128,
                "music_drop_timestamps": [2.5, 6.0, 10.5],
                "mood": "Energetic"
            },
            "visual_dna": {
                "setting_description": "Indoor gym",
                "camera_movement": "Static with zoom in",
                "lighting": "Bright fluorescent",
                "color_palette": ["#FF0000", "#FFFFFF"]
            },
            "commerce_context": {
                "primary_category": "fitness",
                "keywords": ["gym", "workout", "protein"],
                "suitable_products": ["Protein Shake", "Gym Wear"]
            },
            "meme_dna": {
                "catchphrase": None,
                "key_action": "Squat Dance",
                "humor_point": "Unexpected drop at the end"
            }
        }
        return GeminiAnalysisResult(video_id=video_id, **mock_data)


gemini_pipeline = GeminiPipeline()
