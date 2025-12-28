"""
Gemini Pipeline - VDG (Video Data Graph) v3.0 (PEGL v1.0)
Uses Gemini 3.0 Pro to extract the 'Brain' of the viral video.

PEGL v1.0: 스키마 검증 적용
- 출력 스키마 버전 검증
- 필수 필드 검증
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
from app.validators.schema_validator import validate_vdg_analysis_schema, SchemaValidationError

logger = logging.getLogger(__name__)

VDG_PROMPT = """
당신은 바이럴 영상 전문가 AI (Gemini 3.0 Pro)입니다.
이 바이럴 영상을 **VDG (Video Data Graph) v3.3** 형식으로 분석하세요.

## 중요: 한글로 분석
- 모든 텍스트 출력은 **한글**로 작성
- summary, dialogue, location, hook_script 등 모두 한글
- 영어 번역 필드는 생략

## ANALYSIS GOALS

### 1. HOOK ANALYSIS (0-5초)
- **Microbeats**: 훅을 start→build→punch 비트로 분해
- **Virality Analysis**: 왜 스크롤을 멈추게 하는가?
  - curiosity_gap: 어떤 궁금증을 유발하는가?
  - meme_potential: remixable_action | catchphrase | reaction_face | dance | low
  - engagement_pattern: watch_in_loop | share_trigger | comment_bait | scroll_stop

### 2. NARRATIVE STRUCTURE (scenes)
각 씬에서 식별:
- **Dialogue**: 전체 대사 (원본 언어 그대로, 외국어면 한글 번역 포함)
- **Rhetoric**: sarcasm, rhetorical_question, ad_hominem, hyperbole, irony
- **Comedic Device**: expectation_subversion, anticlimax, juxtaposition, callback, slapstick
- **Shots**: 카메라 워크 (샷 타입, 앵글, 무브먼트)

### 3. FOCUS WINDOWS (RL용)
시청자 주의 집중 구간 3-5개:
- **Hotspot scores**: hook (0-1), interest (0-1), boundary (0-1)
- **Mise-en-scène**: composition, lighting, lens, camera_move
- **Entities**: 캐릭터/오브젝트 (pose, emotion, outfit)
- **Tags**: narrative_roles (SETUP, TURN, REVEAL, PUNCHLINE)

### 4. CROSS-SCENE ANALYSIS (패턴 합성)
- **Consistent elements**: 씬 간 일관된 요소
- **Evolving elements**: 변화하는 요소
- **Director intent**: 연출 의도

### 5. SENTIMENT ARC
감정 변화 추적:
- start_sentiment, end_sentiment, trajectory

### 6. ASR/OCR EXTRACTION
- **asr_transcript**: 음성 전사 (한글로)
- **ocr_text**: 화면 텍스트 (한글로)

### 7. PSYCHOLOGICAL AUDIT
- **Irony Analysis**: 기대 vs 현실 갭
- **Dopamine Radar**: 0-10 점수

### 8. PRODUCT PLACEMENT (O2O)
제품/브랜드 등장 시:
- product_mentions: 이름, 브랜드, 카테고리
- cta_types: link_bio, swipe_up, discount_code

### 9. AUDIENCE REACTION
- viral_signal: 바이럴 핵심 이유 (한글)
- overall_sentiment: positive/negative/mixed

### 10. REPLICATION GUIDE (capsule_brief)
- hook_script: 훅 재현 방법 (한글)
- shotlist: [{seq, duration, action, shot}]
- do_not: 하지 말아야 할 것들 (한글)

### 11. REMIX SUGGESTIONS (변주 제안) - 필수 2개 이상
각 변주 제안에는:
- target_niche: 어떤 크리에이터가 활용할 수 있는가 (예: "뷰티 리뷰어", "먹방 크리에이터")
- concept: 변주 컨셉 (예: "이 포맷에 화장품 리뷰를 입히면...")
- template_type: re_enact | mashup | parody | product_placement
- viral_element_to_keep: 반드시 유지해야 할 바이럴 요소
- variable_elements: 변경 가능한 요소들

### 12. PRODUCT PLACEMENT GUIDE (체험단 변주용)
제품/브랜드를 자연스럽게 삽입하려면:
- recommended_timing: 제품 등장 추천 시점 (예: "중반 3-5초")
- invariant_elements: 반드시 유지할 요소 (Hook 구조 등)
- variable_elements: 변주 가능한 요소 (소재, 인물 등)
- product_slot: 제품 삽입 위치 (예: "소품 자리에 제품 대체")

## OUTPUT SCHEMA (JSON Only)
{
  "content_id": "video_id",
  "platform": "youtube|tiktok|instagram",
  "title": "추론된 제목 (한글)",
  "duration_sec": 8.0,
  "upload_date": null,
  "summary": "2문장 한글 요약",
  
  "metrics": {
    "view_count": 0, "like_count": 0, "comment_count": 0,
    "hashtags": ["#funny", "#viral"]
  },
  
  "hook_genome": {
    "start_sec": 0.0, "end_sec": 3.0,
    "pattern": "subversion|problem_solution|question|pattern_break",
    "delivery": "dialogue|visual_gag|voiceover",
    "strength": 0.85,
    "hook_summary": "한 문장 설명 (한글)",
    "microbeats": [
      {"t": 0.5, "role": "start", "cue": "audio", "note": "손님이 정중하게 질문"},
      {"t": 2.1, "role": "build", "cue": "audio", "note": "사장이 비꼬는 답변"},
      {"t": 4.2, "role": "punch", "cue": "audio", "note": "직접적인 욕설 투척"}
    ],
    "virality_analysis": {
      "curiosity_gap": "손님이 어떻게 반응할까?",
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
      "summary": "한글 요약",
      "dialogue": "대사 원본 (외국어면 한글 번역)",
      "dialogue_lang": "ko",
      "rhetoric": ["sarcasm", "rhetorical_question"],
      "comedic_device": ["expectation_subversion", "anticlimax"]
    },
    "setting": {
      "location": "식당",
      "visual_style": {"lighting": "Natural", "edit_pace": "slow"},
      "audio_style": {"audio_events": []}
    },
    "shots": [{"shot_id": "S01_01", "start": 0.0, "end": 8.0, "camera": {"shot": "MS", "angle": "eye", "move": "static"}}]
  }],
  
  "focus_windows": [
    {
      "window_id": "W00",
      "t_window": [0, 3.5],
      "hotspot": {
        "reasons": ["hook", "cv_change"],
        "scores": {"hook": 0.9, "interest": 0.8, "boundary": 0.6},
        "confidence": 0.9
      },
      "mise_en_scene": {
        "composition": {"grid": "center", "subject_size": "CU"},
        "lighting": {"type": "soft_light"},
        "lens": {"fov_class": "medium", "dof": "shallow"},
        "camera_move": "static"
      },
      "entities": [
        {"label": "주인공", "traits": {"pose": "앉아있음", "emotion": "무표정"}, "role_in_window": "SUBJECT"}
      ],
      "parent_scene_id": "S01",
      "tags": {"narrative_roles": ["SETUP"], "cinematic": ["STATIC_SHOT", "CLOSE_UP"]}
    }
  ],
  
  "cross_scene_analysis": {
    "global_summary": "셋업부터 펀치라인까지 완결된 서사 구조 (한글)",
    "consistent_elements": [
      {"aspect": "composition", "evidence": "중앙 프레이밍 유지", "scenes": ["S01"]}
    ],
    "evolving_elements": [
      {"dimension": "emotion_arc", "description": "무표정 → 긴장 → 웃음", "evidence": "표정 변화", "pattern": "escalating"}
    ],
    "director_intent": [
      {"technique": "slow_long_take", "intended_effect": "comedic_timing", "rationale": "대사에 집중", "evidence": {"scenes": ["S01"], "cues": ["no cuts"]}}
    ],
    "entity_state_changes": [
      {"entity_id": "손님", "initial_state": "정중한 손님", "final_state": "당당한 소비자", "triggering_event": "사장의 욕설", "scene_id": "S01", "time_span": [4.2, 7.8]}
    ]
  },
  
  "asr_transcript": {
    "lang": "ko",
    "transcript": "음성 전사 (한글)"
  },
  
  "ocr_text": [
    {"text": "자막 텍스트", "lang": "ko", "timestamp": 2.5}
  ],
  
  "intent_layer": {
    "hook_trigger": "shock",
    "hook_trigger_reason": "한글 설명",
    "retention_strategy": "한글 설명",
    "irony_analysis": {"setup": "한글", "twist": "한글", "gap_type": "expectation_subversion"},
    "dopamine_radar": {"visual_spectacle": 3, "audio_stimulation": 5, "narrative_intrigue": 8, "emotional_resonance": 6, "comedy_shock": 10},
    "sentiment_arc": {
      "start_sentiment": "neutral",
      "end_sentiment": "amused",
      "micro_shifts": [
        {"t": 2.1, "from_emotion": "neutral", "to_emotion": "tense", "cue": "비꼬는 답변"}
      ],
      "trajectory": "긴장감 상승 후 유머로 전환"
    }
  },
  
  "commerce": {
    "product_mentions": [],
    "service_mentions": [],
    "cta_types": [],
    "has_sponsored_content": false
  },
  
  "remix_suggestions": [
    {
      "target_niche": "뷰티 리뷰어",
      "concept": "이 리액션 포맷에 화장품 사용 전후 비교를 입히면 자연스럽게 바이럴 가능",
      "template_type": "product_placement",
      "viral_element_to_keep": "무표정 → 놀람 → 만족 감정 변화 구조",
      "variable_elements": ["소재를 뷰티 제품으로 교체", "배경을 화장대로 변경"]
    },
    {
      "target_niche": "먹방 크리에이터",
      "concept": "음식 리뷰에 이 서프라이즈 포맷 적용",
      "template_type": "re_enact",
      "viral_element_to_keep": "3초 내 호기심 유발 Hook",
      "variable_elements": ["인물 교체", "음식으로 소재 변경"]
    }
  ],
  
  "capsule_brief": {
    "hook_script": "훅 재현 방법 (한글)",
    "shotlist": [{"seq": 1, "duration": 3.0, "action": "한글 액션", "shot": "MS"}],
    "constraints": {"min_actors": 2, "locations": ["식당"], "props": [], "difficulty": "쉬움", "primary_challenge": "코믹 타이밍"},
    "do_not": ["캐릭터 깨지 말 것"],
    "product_placement_guide": {
      "recommended_timing": "중반 3-5초 사이 자연스럽게",
      "invariant_elements": ["Hook 구조 (처음 3초)", "감정 변화 패턴"],
      "variable_elements": ["소재/제품", "촬영 장소", "인물"],
      "product_slot": "소품 자리에 제품 대체"
    }
  },
  
  "audience_reaction": {
    "analysis": "시청자가 왜 이렇게 반응했는지 분석 (한글)",
    "common_reactions": ["웃음", "빈정거림 공감", "공감"],
    "overall_sentiment": "positive",
    "viral_signal": "바이럴 핵심 이유 한 줄 (한글)"
  }
}
"""


class GeminiPipeline:
    def __init__(self):
        self.model = settings.GEMINI_MODEL
        # Prefer GEMINI_API_KEY first (GOOGLE_API_KEY was leaked)
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        if api_key:
            if settings.GEMINI_API_KEY and settings.GOOGLE_API_KEY:
                logger.info("Using GEMINI_API_KEY (preferred)")
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logger.warning("No API key set. GeminiPipeline will use mock data.")

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
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[video_file, enhanced_prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            except Exception as e:
                # Some environments expect fully-qualified model names (models/...)
                if "NOT_FOUND" in str(e) and not self.model.startswith("models/"):
                    fallback_model = f"models/{self.model}"
                    logger.warning(f"Model not found. Retrying with {fallback_model}")
                    response = self.client.models.generate_content(
                        model=fallback_model,
                        contents=[video_file, enhanced_prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                else:
                    raise


            # 4. Parse Response
            try:
                result_json = json.loads(response.text)
                result_json = self._sanitize_vdg_payload(result_json)
                result_json["content_id"] = node_id
                
                # PEGL v1.0: 스키마 버전 추가 (없으면)
                if "schema_version" not in result_json:
                    result_json["schema_version"] = "v3.2"
                
                # PEGL v1.0: 스키마 검증 (실패 시 명시적 예외)
                try:
                    validate_vdg_analysis_schema(result_json)
                except SchemaValidationError as e:
                    logger.error(f"Schema validation failed: {e}")
                    # 검증 실패해도 계속 진행하되 경고 로그
                    # 프로덕션에서는 raise로 변경 가능
                    logger.warning(f"Continuing despite schema validation failure for {node_id}")
                
                # Create VDG object
                vdg = VDG(**result_json)
                
                # === ADAPTER: Populate Legacy Fields ===
                self._populate_legacy_fields(vdg)
                
                # === VDG Quality Validation ===
                try:
                    from app.validators.vdg_quality_validator import validate_vdg_quality
                    quality_result = validate_vdg_quality(result_json)
                    
                    if quality_result.is_valid:
                        logger.info(f"✅ VDG quality check PASSED (score: {quality_result.score})")
                    else:
                        logger.warning(
                            f"⚠️ VDG quality check FAILED (score: {quality_result.score})\n"
                            f"   Issues: {quality_result.issues[:3]}"
                        )
                    
                    # 품질 메타데이터 첨부 (result_json에 추가)
                    result_json["_quality_score"] = quality_result.score
                    result_json["_quality_valid"] = quality_result.is_valid
                    result_json["_quality_issues"] = quality_result.issues[:5]
                    
                except Exception as e:
                    logger.warning(f"VDG quality validation skipped: {e}")
                
                logger.info(f"✅ VDG analysis complete for {node_id}")
                return vdg

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Raw response: {response.text[:500]}...")
                raise SchemaValidationError(f"Invalid JSON from Gemini: {e}", context="gemini_response")
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

        # === Localization Check: Detect English-only fields ===
        # If scene summary is English-only, add summary_ko = None for frontend fallback
        for scene in scenes:
            nu = scene.get("narrative_unit", {})
            summary = nu.get("summary", "")
            if summary:
                # Check if summary contains Korean characters
                has_korean = any('\uac00' <= c <= '\ud7a3' for c in summary)
                if not has_korean:
                    # English-only summary detected - mark for frontend
                    nu["summary_ko"] = None
                    logger.warning(
                        f"Scene {scene.get('scene_id', '?')} has English-only summary: "
                        f"{summary[:50]}... (will show [EN] in UI)"
                    )
                else:
                    # Korean summary - copy to summary_ko for explicit handling
                    nu["summary_ko"] = summary
                scene["narrative_unit"] = nu

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
