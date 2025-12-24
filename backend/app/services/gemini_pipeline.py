"""
Gemini Pipeline - Next-Gen Reconstructible Video Analysis (v3)
"From Summary to Simulation" + Codebook Normalization
"""
import os
import tempfile
import json
import httpx
from typing import Optional, Tuple
from google import genai
from google.genai import types
from app.config import settings
from app.schemas.analysis_v3 import ReconstructibleAnalysisResult
from app.schemas.viral_codebook import (
    VisualPatternCode, 
    AudioPatternCode, 
    SemanticIntent,
    get_codebook_prompt_section
)
from app.services.video_downloader import video_downloader, VideoMetadata

class GeminiPipeline:
    def __init__(self):
        if settings.GEMINI_MODEL != "gemini-3.0-pro":
            raise ValueError("Only gemini-3.0-pro is supported.")
        self.model = "gemini-3.0-pro"
        
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            print("Warning: GEMINI_API_KEY not set")
            self.client = None
        
        self.video_downloader = video_downloader

    async def _download_video(self, url: str) -> Tuple[str, Optional[VideoMetadata]]:
        """Download video using yt-dlp or fallback to HTTP."""
        if any(platform in url.lower() for platform in ['tiktok', 'instagram', 'youtube.com/shorts', 'youtu.be']):
            try:
                file_path, metadata = await self.video_downloader.download(url)
                print(f"✅ Downloaded via yt-dlp: {file_path}")
                return file_path, metadata
            except Exception as e:
                print(f"⚠️ yt-dlp failed: {e}, falling back to HTTP")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            
            processed_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            processed_file.write(resp.content)
            processed_file.close()
            return processed_file.name, None

    async def analyze_video(self, video_url: str, video_id: str) -> ReconstructibleAnalysisResult:
        """
        Analyzes a video using Gemini Vision (V3 Simulation Mode).
        Returns quantitative physics/scene data for reconstruction.
        """
        if not self.client:
            print("⚠️ Gemini API Key missing, returning mock data.")
            return self._get_mock_data(video_id)

        temp_path = None
        try:
            # 1. Prepare Video
            if video_url.startswith("http"):
                print(f"📥 Downloading video from {video_url}...")
                temp_path, _ = await self._download_video(video_url)
                video_source = temp_path
            else:
                video_source = video_url

            # 2. Upload to Gemini
            print(f"⬆️ Uploading execution for {video_id}...")
            video_file = self.client.files.upload(file=video_source)
            
            # 2.5 Wait for ACTIVE
            import time
            max_wait = 60
            wait_interval = 2
            elapsed = 0
            while elapsed < max_wait:
                file_info = self.client.files.get(name=video_file.name)
                if file_info.state.name == "ACTIVE":
                    print(f"✅ File is ACTIVE: {video_file.name}")
                    break
                print(f"⏳ Waiting for file to be ACTIVE... ({elapsed}s)")
                time.sleep(wait_interval)
                elapsed += wait_interval
            else:
                raise Exception(f"File did not become ACTIVE within {max_wait}s")

            # 3. Build Prompt with Codebook
            codebook_section = get_codebook_prompt_section()
            
            prompt = f"""
            You are a physics-aware video simulation engine. 
            Do not just describe the video. **Deconstruct** it into parameters that can perform a 1:1 reconstruction in a 3D engine.
            
            ### Task 1: Legacy Hook Genome Classification
            Classify the viral hook using these strict categories:
            - **Pattern**: "problem_solution" | "pattern_break" | "question" | "proof" | "other"
            - **Delivery**: "dialogue" | "voiceover" | "on_screen_text" | "visual_gag" | "sfx_only"
            - **Strength**: 0.0 to 1.0 (Hook score)

            ### Task 2: Simulation Extraction
            1. **Global Context**: Summarize the viral essence for human understanding.
            2. **Scene Frames**: Sample the video at approximately 0.5 FPS (every 2 seconds). For each frame, provide:
               - **Camera**: Move vector, FOV, focus.
               - **Lighting**: Intensity, Color Temp (Kelvin), Direction.
               - **Actors**: Key pose names, Screen Position (x,y,z), Velocity.
               - **Audio**: Physics of sound (Spectrum, RMS).
            3. **Viral Mosaic**: Identify the sequence of "Viral Patterns" for Reinforcement Learning.
            
            {codebook_section}

            ### Output Format
            Return ONLY valid JSON matching this schema:
            {{
                "video_id": "string",
                "duration": float,
                "global_context": {{
                    "title": "string",
                    "mood": "string",
                    "keywords": ["string"],
                    "viral_hook_summary": "string",
                    "key_action_description": "string",
                    "hashtags": ["string"],
                    "hook_pattern": "string",
                    "hook_delivery": "string",
                    "hook_strength_score": float
                }},
                "scene_frames": [
                    {{
                        "timestamp": float,
                        "duration": float,
                        "description": "string",
                        "camera": {{
                            "type": "static|linear_tracking|dolly_zoom|handheld",
                            "movement_vector": {{"x": 0.0, "y": 0.0, "z": 0.0}},
                            "fov_estimate": 60.0,
                            "focus_target": "string",
                            "shake_intensity": 0.1
                        }},
                        "lighting": {{
                            "intensity": 0.8,
                            "color_temp_kelvin": 6500,
                            "direction": "front",
                            "shadow_softness": 0.5
                        }},
                        "actors": [
                            {{
                                "actor_id": "string",
                                "pose_description": "string",
                                "velocity_vector": {{"x": 0.0, "y": 0.0, "z": 0.0}},
                                "screen_position_center": {{"x": 0.5, "y": 0.5, "z": 0.0}},
                                "emotion_state": "string",
                                "body_parts_engaged": ["legs", "arms"]
                            }}
                        ],
                        "audio": {{
                            "rms_intensity": 0.5,
                            "spectral_centroid": 1200.0,
                            "is_beat_hit": true,
                            "dominant_stems": ["bass"]
                        }}
                    }}
                ],
                "viral_mosaic": [
                    {{
                        "time_index": 0,
                        "start_time": 0.0,
                        "end_time": 2.0,
                        "visual_pattern_id": "VIS_STATIC_INTRO",
                        "audio_pattern_id": "AUD_SILENCE_BUILD",
                        "semantic_intent": "AROUSE_CURIOSITY",
                        "predicted_retention": 0.95
                    }}
                ]
            }}
            """

            print(f"🧠 analyzing {video_id} with {self.model} (Simulation Mode + Codebook)...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=[video_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            data = json.loads(response.text)
            # Ensure video_id consistency
            data["video_id"] = video_id
            return ReconstructibleAnalysisResult(**data)

        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")
            raise e
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def _get_mock_data(self, video_id: str) -> ReconstructibleAnalysisResult:
        """Return mock data compatible with V3 Reconstructible schema + Codebook"""
        mock_data = {
            "video_id": video_id,
            "duration": 15.0,
            "global_context": {
                "title": "Mock Reconstructible Video",
                "mood": "Hyper-Energetic",
                "keywords": ["simulation", "physics", "dance"],
                "viral_hook_summary": "Recursive visual loop with heavy bass",
                "key_action_description": "Infinite Spin",
                "hashtags": ["#simulation", "#gemini_v3"],
                "hook_pattern": "pattern_break",
                "hook_delivery": "visual_gag",
                "hook_strength_score": 0.95
            },
            "scene_frames": [
                {
                    "timestamp": 0.0,
                    "duration": 2.0,
                    "description": "Initial T-Pose calibration",
                    "camera": {
                        "type": "static",
                        "movement_vector": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "fov_estimate": 50.0,
                        "focus_target": "actor_01",
                        "shake_intensity": 0.0
                    },
                    "lighting": {
                        "intensity": 0.5,
                        "color_temp_kelvin": 4000,
                        "direction": "top_down",
                        "shadow_softness": 0.2
                    },
                    "actors": [
                        {
                            "actor_id": "actor_01",
                            "pose_description": "t-pose",
                            "velocity_vector": {"x": 0.0, "y": 0.0, "z": 0.0},
                            "screen_position_center": {"x": 0.5, "y": 0.5, "z": 0.1},
                            "emotion_state": "neutral",
                            "body_parts_engaged": ["all"]
                        }
                    ],
                    "audio": {
                        "rms_intensity": 0.1,
                        "spectral_centroid": 500.0,
                        "is_beat_hit": False,
                        "dominant_stems": ["synth"]
                    }
                }
            ],
            "viral_mosaic": [
                {
                    "time_index": 0,
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "visual_pattern_id": VisualPatternCode.VIS_STATIC_INTRO,
                    "audio_pattern_id": AudioPatternCode.AUD_SILENCE_BUILD,
                    "semantic_intent": SemanticIntent.AROUSE_CURIOSITY,
                    "predicted_retention": 0.8
                }
            ]
        }
        return ReconstructibleAnalysisResult(**mock_data)

gemini_pipeline = GeminiPipeline()
