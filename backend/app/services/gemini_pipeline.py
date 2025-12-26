"""
Gemini Pipeline - VDG (Video Data Graph) v3.0
Uses Gemini 3.0 Pro to extract the 'Brain' of the viral video.
"""
import os
import json
import logging
import time
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types
from app.config import settings
from app.schemas.vdg import VDG, Scene, Shot, Keyframe, CapsuleBrief, ShotlistItem
from app.services.video_downloader import video_downloader

logger = logging.getLogger(__name__)

VDG_PROMPT = """
You are a Viral Video Director & Psychologist AI (Gemini 3.0 Pro).
Your task is to deconstruct this viral video into a **VDG (Video Data Graph) v3.2**.

## ANALYSIS GOALS

### 1. HOOK ANALYSIS (0-5 seconds)
- **Microbeats**: Break down the hook into start→build→punch beats with timestamps
- **Virality Analysis**: Why does this make people stop scrolling?
  - curiosity_gap: What question does this raise?
  - meme_potential: Is it remixable? (remixable_action, catchphrase, reaction_face)
  - engagement_pattern: watch_in_loop, share_trigger, comment_bait

### 2. NARRATIVE STRUCTURE
For each scene, identify:
- **Dialogue**: Full transcript + language + English translation
- **Rhetoric**: sarcasm, rhetorical_question, ad_hominem, hyperbole
- **Comedic Device**: expectation_subversion, anticlimax, juxtaposition, callback

### 3. SENTIMENT ARC
Track micro-shifts in emotional tone:
- Example: Neutral→Tense (at 2.1s, due to "sarcastic response")

### 4. PRODUCT PLACEMENT (for O2O)
If ANY product, brand, or sponsored item appears:
- product_mentions: name, brand, category, timestamp
- cta_types: link_bio, swipe_up, discount_code
- has_sponsored_content: true/false

### 5. PSYCHOLOGICAL AUDIT
- **Irony Analysis**: Expectation vs Reality gap
- **Dopamine Radar**: 0-10 scores for Visual, Audio, Narrative, Emotion, Comedy

### 6. REPLICATION GUIDE
- Production constraints, shooting script, and do-not-do list

## OUTPUT SCHEMA (JSON Only)
{
  "content_id": "video_id",
  "platform": "youtube|tiktok|instagram",
  "title": "Inferred Title",
  "duration_sec": 8.0,
  "summary": "2 sentence summary",
  
  "metrics": {
    "view_count": 0, "like_count": 0, "comment_count": 0,
    "hashtags": ["#funny", "#viral"]
  },
  
  "hook_genome": {
    "start_sec": 0.0, "end_sec": 3.0,
    "pattern": "subversion|problem_solution|question|pattern_break",
    "delivery": "dialogue|visual_gag|voiceover",
    "strength": 0.85,
    "hook_summary": "One sentence description",
    "microbeats": [
      {"t": 0.5, "role": "start", "cue": "audio", "note": "Customer asks polite question"},
      {"t": 2.1, "role": "build", "cue": "audio", "note": "Owner gives sarcastic response"},
      {"t": 4.2, "role": "punch", "cue": "audio", "note": "Direct insult delivered"}
    ],
    "virality_analysis": {
      "curiosity_gap": "How will the customer react to being insulted?",
      "meme_potential": "remixable_action",
      "relatability_factor": "surprise_reveal",
      "engagement_pattern": "watch_in_loop"
    },
    "information_density": "low"
  },
  
  "scenes": [{
    "scene_id": "S01",
    "time_start": 0.0, "time_end": 8.0, "duration_sec": 8.0,
    "narrative_unit": {
      "role": "Hook",
      "summary": "...",
      "dialogue": "할머니 뭘 넣었길래...",
      "dialogue_lang": "ko",
      "dialogue_translation_en": "Grandma, what did you put in...",
      "rhetoric": ["sarcasm", "rhetorical_question"],
      "comedic_device": ["expectation_subversion", "anticlimax"]
    },
    "setting": {
      "location": "Restaurant",
      "visual_style": {"lighting": "Natural", "edit_pace": "slow"},
      "audio_style": {"audio_events": []}
    },
    "shots": [{"shot_id": "S01_01", "start": 0.0, "end": 8.0, "camera": {"shot": "MS", "angle": "eye", "move": "static"}}]
  }],
  
  "intent_layer": {
    "hook_trigger": "shock",
    "hook_trigger_reason": "...",
    "retention_strategy": "...",
    "irony_analysis": {"setup": "...", "twist": "...", "gap_type": "expectation_subversion"},
    "dopamine_radar": {"visual_spectacle": 3, "audio_stimulation": 5, "narrative_intrigue": 8, "emotional_resonance": 6, "comedy_shock": 10},
    "sentiment_arc": {
      "start_sentiment": "neutral",
      "end_sentiment": "amused",
      "micro_shifts": [
        {"t": 2.1, "from_emotion": "neutral", "to_emotion": "tense", "cue": "Sarcastic response"},
        {"t": 5.6, "from_emotion": "tense", "to_emotion": "comedic_relief", "cue": "Calm retort"}
      ],
      "trajectory": "Builds tension then pivots to humor via subversion"
    }
  },
  
  "commerce": {
    "product_mentions": [{"name": "Product X", "brand": "Brand Y", "category": "food", "timestamp": 3.5, "mention_type": "visual"}],
    "service_mentions": [],
    "cta_types": [],
    "has_sponsored_content": false
  },
  
  "capsule_brief": {
    "hook_script": "...",
    "shotlist": [{"seq": 1, "duration": 3.0, "action": "...", "shot": "MS"}],
    "constraints": {"min_actors": 2, "locations": ["Restaurant"], "props": [], "difficulty": "Easy", "primary_challenge": "Comedic timing"},
    "do_not": ["Break character"]
  },
  
  "audience_reaction": {
    "analysis": "Overall audience interpretation...",
    "common_reactions": ["Humor", "Sarcasm appreciation", "Relatability"],
    "overall_sentiment": "positive",
    "viral_signal": "The calm bureaucratic threat contrasts with escalating insults"
  }
}
"""


class GeminiPipeline:
    def __init__(self):
        self.model = settings.GEMINI_MODEL
        api_key = settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logger.warning("GOOGLE_API_KEY is not set. GeminiPipeline will use mock data.")

    async def analyze_video(
        self, 
        video_url: str, 
        node_id: str,
        audience_comments: Optional[List[Dict[str, Any]]] = None
    ) -> VDG:
        """
        Full pipeline: Download -> Upload -> Analyze (VDG) -> Parse -> Return
        
        Args:
            video_url: Video URL to analyze
            node_id: Node ID for tracking
            audience_comments: Optional list of best comments for context
                [{"text": "...", "likes": 123, "lang": "en"}, ...]
        """
        if not self.client:
            logger.info("No API key, returning mock VDG data.")
            return self._get_mock_data(node_id)

        temp_path = None
        try:
            # 1. Download Video
            logger.info(f"📥 Downloading video from {video_url}...")
            temp_path, metadata = await video_downloader.download(video_url)
            
            # 2. Upload to Gemini
            logger.info(f"⬆️ Uploading for {node_id}...")
            video_file = self.client.files.upload(file=temp_path)
            
            # Wait for processing
            max_wait = 60
            elapsed = 0
            while elapsed < max_wait:
                file_info = self.client.files.get(name=video_file.name)
                if file_info.state.name == "ACTIVE":
                    logger.info(f"✅ File ACTIVE: {video_file.name}")
                    break
                logger.info(f"⏳ Waiting... ({elapsed}s)")
                time.sleep(2)
                elapsed += 2
            else:
                raise Exception(f"File did not become ACTIVE within {max_wait}s")

            # 3. Build prompt with audience comments context
            enhanced_prompt = VDG_PROMPT
            if audience_comments:
                comments_text = "\n".join([
                    f"- [{c.get('likes', 0)} likes] {c.get('text', '')[:200]}"
                    for c in audience_comments[:10]
                ])
                enhanced_prompt = f"""
## AUDIENCE REACTIONS (Best Comments by Likes)
The following are the top comments from real viewers. Use these to understand WHY this video went viral:

{comments_text}

Consider these reactions when analyzing the hook effectiveness, emotional impact, and virality factors.

---

{VDG_PROMPT}
"""
                logger.info(f"📝 Including {len(audience_comments)} audience comments in analysis")

            # 4. Generate Analysis
            logger.info(f"🧠 Analyzing {node_id} with {self.model} (VDG v3.0)...")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[video_file, enhanced_prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )


            # 4. Parse Response
            try:
                result_json = json.loads(response.text)
                result_json = self._sanitize_vdg_payload(result_json)
                result_json["content_id"] = node_id
                
                # Create VDG object
                vdg = VDG(**result_json)
                
                # === ADAPTER: Populate Legacy Fields ===
                self._populate_legacy_fields(vdg)
                
                logger.info(f"✅ VDG analysis complete for {node_id}")
                return vdg

            except Exception as e:
                logger.error(f"Failed to parse Gemini response: {e}")
                logger.error(f"Raw response: {response.text[:500]}...")
                raise e

        except Exception as e:
            logger.error(f"❌ Gemini analysis failed: {e}")
            raise e
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def _sanitize_vdg_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce known schema edge-cases from LLM output before Pydantic validation."""
        scenes = payload.get("scenes", [])
        for scene in scenes:
            setting = scene.get("setting") or {}
            audio_style = setting.get("audio_style") or {}
            audio_events = audio_style.get("audio_events")
            if isinstance(audio_events, list):
                normalized = []
                for idx, event in enumerate(audio_events):
                    if isinstance(event, dict):
                        normalized.append(event)
                    elif isinstance(event, str):
                        normalized.append(
                            {
                                "timestamp": 0.0,
                                "event": "note",
                                "description": event,
                                "intensity": "medium",
                            }
                        )
                audio_style["audio_events"] = normalized
                setting["audio_style"] = audio_style
                scene["setting"] = setting

        commerce = payload.get("commerce") or {}
        service_mentions = commerce.get("service_mentions")
        if isinstance(service_mentions, list):
            normalized_services = []
            for item in service_mentions:
                if isinstance(item, str):
                    normalized_services.append(item)
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("brand") or item.get("category")
                    normalized_services.append(name or str(item))
                else:
                    normalized_services.append(str(item))
            commerce["service_mentions"] = normalized_services
            payload["commerce"] = commerce

        return payload

    def _populate_legacy_fields(self, vdg: VDG) -> None:
        """Populate legacy compatibility fields for frontend"""
        # global_context
        hook = vdg.hook_genome
        intent = vdg.intent_layer
        
        vdg.global_context = {
            "title": vdg.title[:100] if vdg.title else "Analyzed Video",
            "mood": "dynamic", # simplified
            "keywords": ["viral", vdg.platform, intent.hook_trigger],
            "hashtags": [],
            "video_id": vdg.content_id,
            "hook_pattern": hook.pattern,
            "hook_delivery": hook.delivery,
            "hook_strength_score": hook.strength,
            "viral_hook_summary": hook.hook_summary,
            "key_action_description": intent.hook_trigger_reason
        }
        
        # scene_frames (simplified from scenes)
        frames = []
        for scene in vdg.scenes:
            for shot in scene.shots:
                frame = {
                    "timestamp": shot.start,
                    "duration": shot.end - shot.start,
                    "description": shot.keyframes[0].desc if shot.keyframes else scene.narrative_unit.summary,
                    "camera": {
                        "type": shot.camera.move,
                        "shot_size": shot.camera.shot,
                        "angle": shot.camera.angle
                    }
                }
                frames.append(frame)
        vdg.scene_frames = frames

    def _get_mock_data(self, video_id: str) -> VDG:
        """Return mock VDG data when API key is not available"""
        # (Mock implementation simplified for brevity)
        return VDG(
            content_id=video_id,
            title="Mock Video",
            duration_sec=15.0,
            summary="Mock summary",
            hook_genome=dict(hook_summary="Mock hook", strength=0.8),
            scenes=[],
            intent_layer=dict(
                hook_trigger="shock", 
                irony_analysis=dict(setup="A", twist="B"),
                dopamine_radar=dict(visual_spectacle=5, audio_stimulation=5, narrative_intrigue=5, emotional_resonance=5, comedy_shock=5)
            ),
            remix_suggestions=[],
            capsule_brief=dict(hook_script="Mock script", constraints=dict(primary_challenge="Mock challenge"))
        )

gemini_pipeline = GeminiPipeline()
