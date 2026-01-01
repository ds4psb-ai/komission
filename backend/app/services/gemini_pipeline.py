"""
Gemini Pipeline - VDG (Video Data Graph) v5.0 (Unified Pass + CV)
Uses Gemini 3.0 Pro 1-Pass + CV deterministic measurement.

v5.0: Unified Pipeline
- Pass 1: Gemini 3.0 Pro (의미/인과/Plan Seed)
- Pass 2: CV deterministic measurement (수치/좌표)
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types
from app.config import settings
from app.services.vdg_2pass.vdg_unified_pipeline import VDGUnifiedPipeline, analyze_video as unified_analyze
from app.services.vdg_2pass.director_compiler import DirectorCompiler
from app.schemas.vdg_v4 import VDGv4
from app.schemas.vdg import VDG
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


def _get_analysis_depth_hints(duration_sec: float) -> str:
    """영상 길이에 따른 분석 깊이 지침 생성 (v3.6)"""
    
    if duration_sec <= 15:
        # 8-15초 초단편 (가장 세밀하게)
        return """
## 🎯 초단편 영상 분석 지침 (≤15초)
이 영상은 매우 짧으므로 **극도로 세밀한 분석**이 필요합니다.

### 필수 요구사항:
- **Microbeats**: 최소 5개 (0.3~0.5초 단위)
  - 모든 비트에 `t`, `role`, `cue`, `note` 상세 기술
  - role: start → build → build → punch → end 순서 권장
- **Keyframes**: 샷당 2-3개 (주요 동작/표정 변화 포인트)
  - 각 keyframe에 `role`, `desc`, `t_rel_shot` 필수
- **Focus Windows**: 4-5개 (2-3초 단위 구간)
  - 시청자 주의 집중 순간마다 hotspot 분석
- **Scenes**: 1-2개만 (너무 많이 나누지 말 것)
- **Shots per Scene**: 1-3개 (컷 전환점 기준)
"""
    elif duration_sec <= 30:
        # 15-30초 단편
        return """
## 🎯 단편 영상 분석 지침 (15-30초)

### 필수 요구사항:
- **Microbeats**: 최소 4개 (0.5~1초 단위)
- **Keyframes**: 샷당 1-2개
- **Focus Windows**: 4-6개 (3-5초 단위)
- **Scenes**: 2-3개
- **Shots per Scene**: 2-4개
"""
    elif duration_sec <= 60:
        # 30-60초 표준 숏폼
        return """
## 🎯 표준 숏폼 분석 지침 (30-60초)

### 필수 요구사항:
- **Microbeats**: 최소 3개
- **Keyframes**: 샷당 1-2개
- **Focus Windows**: 5-8개 (5-10초 단위)
- **Scenes**: 3-5개
- **Shots per Scene**: 2-5개
"""
    else:
        # 60초+ 롱폼
        return """
## ⚠️ 롱폼 영상 분석 지침 (>60초)
이 영상은 숏폼 분석에 최적화되지 않습니다.
주요 하이라이트 구간(훅, 클라이맥스, 엔딩)만 상세 분석하세요.
"""


def _build_enhanced_prompt(
    duration_sec: float,
    audience_comments: Optional[List[Dict[str, Any]]] = None
) -> str:
    """영상 길이와 댓글 기반 동적 프롬프트 생성 (v3.6)"""
    
    # 1. Duration-based depth hints
    depth_hints = _get_analysis_depth_hints(duration_sec)
    
    # 2. Comments context (if available)
    comments_section = ""
    if audience_comments:
        comments_text = "\n".join([
            f"- [{c.get('likes', 0)} likes] {c.get('text', '')[:200]}"
            for c in audience_comments[:10]
        ])
        comments_section = f"""
## 📝 시청자 반응 컨텍스트 (Top Comments)
실제 시청자들의 반응입니다. 이를 참고하여 viral_signal, audience_reaction을 분석하세요:

{comments_text}
"""
    
    # 3. Assemble final prompt
    return f"""
{depth_hints}
{comments_section}

---

{VDG_PROMPT}
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
            logger.warning(f"📥 Downloading video from {video_url}...")
            temp_path, metadata = await video_downloader.download(video_url)
            try:
                size_mb = os.path.getsize(temp_path) / (1024 * 1024)
                logger.warning(f"📦 Downloaded size: {size_mb:.2f} MB ({temp_path})")
            except Exception as e:
                logger.warning(f"📦 Downloaded size unavailable: {e}")
            
            # 2. Build inline video part (base64)
            try:
                with open(temp_path, "rb") as video_fp:
                    video_bytes = video_fp.read()
            except Exception as e:
                raise Exception(f"Failed to read downloaded video: {e}") from e

            if not video_bytes:
                raise Exception("Downloaded video is empty")

            size_mb = len(video_bytes) / (1024 * 1024)
            if size_mb > 20:
                logger.warning(
                    f"⚠️ Inline video size is {size_mb:.2f} MB (>20MB). "
                    "Gemini API may reject inline uploads."
                )
            logger.warning(f"📦 Inline video bytes: {len(video_bytes)}")

            video_part = types.Part(
                inline_data=types.Blob(
                    data=video_bytes,
                    mime_type="video/mp4"
                )
            )

            # 3. Build duration-aware prompt (v3.6)
            duration_sec = metadata.duration or 60.0  # Default to 60s if unknown
            enhanced_prompt = _build_enhanced_prompt(
                duration_sec=duration_sec,
                audience_comments=audience_comments
            )
            logger.info(f"📏 Duration: {duration_sec}s → using depth-optimized prompt")
            if audience_comments:
                logger.info(f"📝 Including {len(audience_comments)} audience comments in analysis")

            # 4. Generate Analysis
            logger.warning(f"🧠 Analyzing {node_id} with {self.model} (VDG v3.6)...")

            def _build_config(use_schema: bool) -> types.GenerateContentConfig:
                if use_schema:
                    return types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=VDG.model_json_schema()
                    )
                return types.GenerateContentConfig(response_mime_type="application/json")

            def _looks_like_schema_error(message: str) -> bool:
                msg = message.lower()
                return (
                    "schema" in msg
                    or "response_json_schema" in msg
                    or "invalid_argument" in msg
                    or "invalid argument" in msg
                )

            def _generate(model_name: str, use_schema: bool):
                logger.warning(f"📦 Generate with model={model_name} inline=True schema={use_schema}")
                return self.client.models.generate_content(
                    model=model_name,
                    contents=[video_part, enhanced_prompt],
                    config=_build_config(use_schema)
                )

            use_schema = True
            last_err: Optional[Exception] = None
            response = None

            models_to_try = [self.model]
            if not self.model.startswith("models/"):
                models_to_try.append(f"models/{self.model}")

            for model_name in models_to_try:
                try:
                    response = _generate(model_name, use_schema)
                    break
                except Exception as e:
                    if use_schema and _looks_like_schema_error(str(e)):
                        logger.warning("⚠️ Response schema rejected, retrying without schema")
                        use_schema = False
                        try:
                            response = _generate(model_name, use_schema)
                            break
                        except Exception as retry_err:
                            last_err = retry_err
                            logger.warning(f"❌ Model retry failed: {retry_err}")
                            continue
                    last_err = e
                    logger.warning(f"❌ Model failed: {model_name} error={e}")
                    continue

            if response is None and last_err is not None:
                raise last_err


            # 4. Parse Response
            try:
                result_json = json.loads(response.text)
                result_json = self._sanitize_vdg_payload(result_json)
                result_json["content_id"] = node_id
                
                # === v3.6: Merge accurate metadata from yt-dlp ===
                # Duration (accurate from yt-dlp)
                if metadata.duration > 0:
                    result_json["duration_sec"] = metadata.duration
                
                # Upload date (format YYYYMMDD → YYYY-MM-DD)
                if metadata.upload_date and len(metadata.upload_date) == 8:
                    ud = metadata.upload_date
                    result_json["upload_date"] = f"{ud[:4]}-{ud[4:6]}-{ud[6:8]}"
                
                # Metrics (real API values override Gemini guesses)
                if "metrics" not in result_json:
                    result_json["metrics"] = {}
                if metadata.view_count > 0:
                    result_json["metrics"]["view_count"] = metadata.view_count
                if metadata.like_count > 0:
                    result_json["metrics"]["like_count"] = metadata.like_count
                if metadata.comment_count:
                    result_json["metrics"]["comment_count"] = metadata.comment_count
                if metadata.share_count:
                    result_json["metrics"]["share_count"] = metadata.share_count
                if metadata.hashtags:
                    result_json["metrics"]["hashtags"] = metadata.hashtags
                
                # Platform (accurate from URL)
                result_json["platform"] = metadata.platform
                
                logger.info(f"📊 Merged metadata: duration={metadata.duration}s, upload={metadata.upload_date}, views={metadata.view_count}")
                
                # PEGL v1.0: 스키마 버전 추가 (없으면)
                if "schema_version" not in result_json:
                    result_json["schema_version"] = "v3.6"
                
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
                
                # Note: VDG doesn't have legacy fields (global_context, scene_frames)
                # Legacy field population skipped for v3.5
                
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

    async def analyze_video_v4(
        self,
        video_url: str,
        node_id: str,
        audience_comments: Optional[List[Dict[str, Any]]] = None
    ) -> VDGv4:
        """
        VDG v5.0 Unified Pipeline Execution
        
        Pass 1: Gemini 3.0 Pro 1회 호출 (의미/인과/Plan Seed)
        Pass 2: CV 결정론적 측정 (수치/좌표)
        
        ** Redis Cache 지원: 동일 영상+댓글 조합은 24시간 캐시 **
        """
        import asyncio
        import hashlib
        from app.services.cache import cache
        
        # Generate comments hash for cache key
        comments_str = json.dumps(audience_comments or [], sort_keys=True)
        comments_hash = hashlib.md5(comments_str.encode()).hexdigest()
        
        # 0. Check cache first
        try:
            await cache.connect()
            cached_data = await cache.get_vdg_v4(video_url, comments_hash)
            if cached_data:
                logger.info(f"✅ [v5] Cache HIT for {video_url[:50]}...")
                return VDGv4.model_validate(cached_data)
        except Exception as e:
            logger.warning(f"Cache check failed (continuing without cache): {e}")
        
        temp_path = None
        try:
            # 1. Download
            logger.info(f"📥 [v5] Downloading {video_url}...")
            temp_path, metadata = await video_downloader.download(video_url)
            
            duration_sec = metadata.duration or 0.0
            if duration_sec == 0.0:
                # Fallback: ffprobe로 측정
                from app.services.vdg_2pass.unified_pass import get_video_duration_ms
                duration_ms = get_video_duration_ms(temp_path)
                duration_sec = duration_ms / 1000.0 if duration_ms > 0 else 60.0

            platform = "youtube" 
            if "tiktok.com" in video_url: platform = "tiktok"
            elif "instagram.com" in video_url: platform = "instagram"
            elif "shorts" in video_url: platform = "youtube"

            # 2. Extract comments text
            top_comments = []
            if audience_comments:
                top_comments = [
                    c.get("text", "")[:200] for c in audience_comments[:20]
                    if c.get("text")
                ]

            # 3. Run unified pipeline (sync, but wrapped in executor for async context)
            logger.info("🚀 [v5] Running VDG Unified Pipeline...")
            
            def _run_sync():
                pipeline = VDGUnifiedPipeline()
                return pipeline.run(
                    video_path=temp_path,
                    platform=platform,
                    top_comments=top_comments,
                )
            
            # Run sync pipeline in thread pool
            loop = asyncio.get_event_loop()
            unified_result = await loop.run_in_executor(None, _run_sync)
            
            logger.info(
                f"✅ [v5] Pipeline complete: "
                f"pass1={unified_result.pass1_latency_ms}ms, "
                f"pass2={unified_result.pass2_latency_ms}ms"
            )
            
            # 4. Convert UnifiedResult to VDGv4 format
            vdg = self._convert_unified_to_vdg_v4(
                unified_result=unified_result,
                content_id=node_id,
                video_url=video_url,
                platform=platform,
                duration_sec=duration_sec,
            )
            
            # 4.5 P0-1: Quality Gate validation
            from app.services.vdg_2pass.quality_gate import proof_grade_gate
            proof_ready, quality_issues = proof_grade_gate.validate(
                vdg.model_dump(), 
                int(duration_sec * 1000)
            )
            
            # Update VDG meta with quality gate results
            vdg.meta = {
                "proof_ready": proof_ready,
                "quality_issues": quality_issues if quality_issues else None,
                "prompt_version": "v4.2",
                "model_id": "gemini-3.0-pro",
                "schema_version": vdg.vdg_version,
            }
            
            if proof_ready:
                logger.info(f"✅ [v5] Quality Gate PASSED")
            else:
                logger.warning(f"⚠️ [v5] Quality Gate FAILED: {quality_issues[:3]}")
            
            # Get final vdg_data for cache
            vdg_data = vdg.model_dump()
            
            # 5. Save to cache (24 hours)
            try:
                await cache.cache_vdg_v4(
                    video_url=video_url,
                    comments_hash=comments_hash,
                    vdg_data=vdg_data,
                )
                logger.info(f"💾 [v5] Cache SAVED for {video_url[:50]}...")
            except Exception as e:
                logger.warning(f"Cache save failed (result still returned): {e}")
            
            return vdg

        except Exception as e:
            logger.error(f"❌ VDG v5 Pipeline Failed: {e}")
            raise e
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def _convert_unified_to_vdg_v4(
        self,
        unified_result,
        content_id: str,
        video_url: str,
        platform: str,
        duration_sec: float,
    ) -> VDGv4:
        """UnifiedResult를 VDGv4 포맷으로 변환"""
        from app.schemas.vdg_v4 import (
            VDGv4, HookGenome, Scene, Microbeat,
            IntentLayer, MiseEnSceneSignal, AudienceReaction,
            SemanticPassResult, SemanticPassProvenance,
            VisualPassResult, AnalysisPlan, AnalysisPoint,
            MediaSpec, MetricResult
        )
        
        llm = unified_result.llm_output
        cv = unified_result.cv_result
        
        # Role mapping from UnifiedPass to VDGv4
        role_map = {
            'start': 'start', 'setup': 'start', 'hook': 'start',
            'punch': 'punch', 'reveal': 'punch', 'twist': 'punch',
            'build': 'build', 'demo': 'build',
            'end': 'end', 'cta': 'end', 'loop': 'end', 'payoff': 'end',
        }
        
        # Hook genome 변환
        microbeats = []
        for m in (llm.hook_genome.microbeats or []):
            mb_role = role_map.get(m.role, 'start')
            microbeats.append(Microbeat(
                t=m.t_ms / 1000.0,  # ms → seconds
                role=mb_role,
                cue='visual',
                note=m.description[:50] if m.description else '',
            ))
        
        hook = HookGenome(
            hook_start_ms=llm.hook_genome.hook_start_ms,
            hook_end_ms=llm.hook_genome.hook_end_ms,
            strength=llm.hook_genome.strength,
            spoken_hook=llm.hook_genome.spoken_hook,
            on_screen_text=llm.hook_genome.on_screen_text,
            microbeats=microbeats,
        )
        
        # Scenes 변환
        scenes = [
            Scene(
                scene_id=f"S{s.idx:02d}",
                time_start_ms=s.window.start_ms,
                time_end_ms=s.window.end_ms,
                label=s.label,
                summary=s.summary,
            )
            for s in llm.scenes
        ]
        
        # Intent layer 변환
        intent = IntentLayer(
            creator_intent=llm.intent_layer.creator_intent,
            audience_trigger=llm.intent_layer.audience_trigger,
            novelty=llm.intent_layer.novelty,
            clarity=llm.intent_layer.clarity,
        )
        
        # Mise-en-scene signals 변환
        # Element mapping from UnifiedPass to VDGv4
        element_map = {
            'prop': 'props', 'composition': 'setting', 'color': 'outfit_color',
            'wardrobe': 'outfit_color', 'camera': 'setting', 'editing': 'setting',
            'audio': 'setting', 'text': 'setting',
        }
        valid_elements = {'outfit_color', 'background', 'lighting', 'props', 'makeup', 'setting'}
        
        mise_signals = []
        for m in llm.mise_en_scene_signals:
            element = element_map.get(m.type, m.type)
            if element not in valid_elements:
                element = 'setting'  # default fallback
            mise_signals.append(MiseEnSceneSignal(
                element=element,
                value=m.description[:50],
                sentiment="positive",
                source_comment="",
                likes=0,
            ))
        
        # Comment evidence를 audience_reaction으로 변환
        best_comments = [
            {
                "rank": c.comment_rank,
                "text": c.quote,
                "signal_type": c.signal_type,
                "why_it_matters": c.why_it_matters,
                "anchor_ms": getattr(c, 'anchor_ms', None),
            }
            for c in llm.comment_evidence_top5
        ]
        
        # Viral kicks 변환
        viral_kicks = [
            {
                "kick_index": k.kick_index,
                "t_start_ms": k.window.start_ms,
                "t_end_ms": k.window.end_ms,
                "title": k.title,
                "mechanism": k.mechanism,
                "creator_instruction": k.creator_instruction,
                "evidence_comment_ranks": k.evidence_comment_ranks,
                "evidence_cues": k.evidence_cues,
            }
            for k in llm.viral_kicks
        ]
        
        audience = AudienceReaction(
            best_comments=best_comments,
            sentiment_distribution={},
            top_themes=[],
        )
        
        # Semantic pass result
        semantic_provenance = SemanticPassProvenance(
            model_id=unified_result.llm_provenance.model_id,
            prompt_version=unified_result.llm_provenance.prompt_version,
            run_at=unified_result.llm_provenance.run_at,
        )
        
        semantic = SemanticPassResult(
            scenes=scenes,
            hook_genome=hook,
            intent_layer=intent,
            audience_reaction=audience,
            mise_en_scene_signals=mise_signals,
            summary=llm.causal_reasoning.why_viral_one_liner if llm.causal_reasoning else "",
            provenance=semantic_provenance,
        )
        
        # Analysis plan 변환
        analysis_points = []
        if llm.analysis_plan and llm.analysis_plan.points:
            # Reason mapping from UnifiedPass to VDGv4
            reason_map = {
                'critical': 'hook_punch', 'high': 'key_dialogue',
                'medium': 'scene_boundary', 'low': 'text_appear',
            }
            valid_reasons = {
                'hook_punch', 'hook_start', 'hook_build', 'hook_end',
                'scene_boundary', 'sentiment_shift', 'product_mention',
                'key_dialogue', 'text_appear', 'comment_mise_en_scene', 'comment_evidence'
            }
            for i, p in enumerate(llm.analysis_plan.points):
                # Map reason to valid enum or use priority-based mapping
                llm_reason = getattr(p, 'reason', '')
                if llm_reason in valid_reasons:
                    mapped_reason = llm_reason
                else:
                    mapped_reason = reason_map.get(p.priority, 'key_dialogue')
                
                t_start = (p.t_center_ms - p.t_window_ms // 2) / 1000.0
                t_end = (p.t_center_ms + p.t_window_ms // 2) / 1000.0
                
                point = AnalysisPoint(
                    id=f"AP_{i:02d}",
                    t_center=p.t_center_ms / 1000.0,
                    t_window=[t_start, t_end],
                    priority=p.priority,
                    reason=mapped_reason,
                    source_ref=f"llm_plan_{i}",
                )
                analysis_points.append(point)
        
        analysis_plan = AnalysisPlan(
            points=analysis_points,
        )
        
        # Visual pass result (CV measurements)
        visual = VisualPassResult()
        if unified_result.analysis_points:
            from app.schemas.vdg_v4 import AnalysisPointResult
            analysis_results = []
            for ap in unified_result.analysis_points:
                metrics_dict = {}
                for mid, mr in ap.metrics.items():
                    # Infer value_type from value
                    val = mr.value
                    if isinstance(val, bool):
                        value_type = "bool"
                    elif isinstance(val, (list, tuple)):
                        value_type = "vector2"
                    elif isinstance(val, float):
                        value_type = "scalar"
                    else:
                        value_type = "scalar"
                    
                    metrics_dict[mid] = MetricResult(
                        metric_id=mid,
                        value_type=value_type,
                        confidence=mr.confidence,
                    )
                
                analysis_results.append(AnalysisPointResult(
                    ap_id=ap.ap_id,
                    t_center_ms=ap.t_center_ms,
                    t_window_ms=ap.t_window_ms,
                    metrics=metrics_dict,
                ))
            visual.analysis_results = analysis_results
        
        # Media spec
        media = MediaSpec(
            duration_ms=int(duration_sec * 1000),
        )
        
        return VDGv4(
            content_id=content_id,
            platform=platform,
            duration_sec=duration_sec,
            media=media,
            semantic=semantic,
            analysis_plan=analysis_plan,
            visual=visual,
            mise_en_scene_signals=mise_signals,
            provenance={
                "pipeline_version": "v5.0_unified",
                "pass1_model": unified_result.llm_provenance.model_id,
                "pass2_version": unified_result.cv_provenance.version if cv else None,
                "viral_kicks": viral_kicks,
                "causal_reasoning": {
                    "why_viral_one_liner": llm.causal_reasoning.why_viral_one_liner,
                    "causal_chain": llm.causal_reasoning.causal_chain,
                    "replication_recipe": llm.causal_reasoning.replication_recipe,
                } if llm.causal_reasoning else {},
            },
        )


    def _sanitize_vdg_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce known schema edge-cases from LLM output before Pydantic validation."""
        scenes = payload.get("scenes") or []
        if not isinstance(scenes, list):
            scenes = []
        scenes = [scene for scene in scenes if isinstance(scene, dict)]
        payload["scenes"] = scenes
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

        commerce = payload.get("commerce")
        if not isinstance(commerce, dict):
            commerce = {}
            payload["commerce"] = commerce
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
