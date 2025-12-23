"""
Viral Codebook - Standardized Pattern Vocabulary for GA/RL

This codebook defines the normalized pattern codes that Gemini must use
when analyzing videos. This enables:
1. Consistent State Space for Reinforcement Learning
2. Meaningful Similarity Comparisons (Vector Embedding)
3. Pattern Confidence Tracking across videos
"""
from enum import Enum
from typing import List


class VisualPatternCode(str, Enum):
    """
    정규화된 시각 패턴 코드 (50개)
    GA/RL State Space의 Visual Dimension
    """
    # === Intro Patterns (0-9) ===
    VIS_STATIC_INTRO = "VIS_STATIC_INTRO"           # 정적 오프닝
    VIS_ZOOM_TO_FACE = "VIS_ZOOM_TO_FACE"           # 얼굴로 줌인
    VIS_DOLLY_IN = "VIS_DOLLY_IN"                   # 카메라 전진
    VIS_DOLLY_OUT = "VIS_DOLLY_OUT"                 # 카메라 후진
    VIS_TEXT_OVERLAY_INTRO = "VIS_TEXT_OVERLAY_INTRO"  # 텍스트 오프닝
    VIS_QUESTION_CARD = "VIS_QUESTION_CARD"         # 질문 자막 시작
    VIS_PRODUCT_REVEAL = "VIS_PRODUCT_REVEAL"       # 제품 등장
    VIS_PERSON_ENTRANCE = "VIS_PERSON_ENTRANCE"     # 인물 등장
    VIS_ENVIRONMENT_SWEEP = "VIS_ENVIRONMENT_SWEEP" # 환경 훑기
    VIS_COUNTDOWN = "VIS_COUNTDOWN"                 # 카운트다운
    
    # === Action Patterns (10-24) ===
    VIS_RAPID_CUT = "VIS_RAPID_CUT"                 # 빠른 컷 전환
    VIS_DANCE_MOVE = "VIS_DANCE_MOVE"               # 춤 동작
    VIS_TUTORIAL_STEP = "VIS_TUTORIAL_STEP"         # 튜토리얼 단계
    VIS_COOKING_ACTION = "VIS_COOKING_ACTION"       # 요리 동작
    VIS_UNBOXING = "VIS_UNBOXING"                   # 언박싱
    VIS_TRANSFORMATION = "VIS_TRANSFORMATION"       # 변신/변화
    VIS_SPLIT_SCREEN = "VIS_SPLIT_SCREEN"           # 화면 분할
    VIS_HANDHELD_SHAKE = "VIS_HANDHELD_SHAKE"       # 핸드헬드 흔들림
    VIS_SLOW_MOTION = "VIS_SLOW_MOTION"             # 슬로우모션
    VIS_TIME_LAPSE = "VIS_TIME_LAPSE"               # 타임랩스
    VIS_POV_SHOT = "VIS_POV_SHOT"                   # 1인칭 시점
    VIS_REACTION_SHOT = "VIS_REACTION_SHOT"         # 리액션 샷
    VIS_BEFORE_AFTER = "VIS_BEFORE_AFTER"           # 전후 비교
    VIS_SCREEN_RECORDING = "VIS_SCREEN_RECORDING"   # 화면 녹화
    VIS_VLOG_STYLE = "VIS_VLOG_STYLE"               # 브이로그 스타일
    
    # === Climax Patterns (25-34) ===
    VIS_JUMP_CUT_CLIMAX = "VIS_JUMP_CUT_CLIMAX"     # 점프컷 클라이맥스
    VIS_ZOOM_EMPHASIS = "VIS_ZOOM_EMPHASIS"         # 강조 줌
    VIS_FLASH_TRANSITION = "VIS_FLASH_TRANSITION"   # 플래시 전환
    VIS_COLOR_SHIFT = "VIS_COLOR_SHIFT"             # 색상 변화
    VIS_GLITCH_EFFECT = "VIS_GLITCH_EFFECT"         # 글리치 효과
    VIS_FREEZE_FRAME = "VIS_FREEZE_FRAME"           # 프리즈 프레임
    VIS_DRAMATIC_REVEAL = "VIS_DRAMATIC_REVEAL"     # 드라마틱 공개
    VIS_MEME_FORMAT = "VIS_MEME_FORMAT"             # 밈 포맷
    VIS_STICKER_EXPLOSION = "VIS_STICKER_EXPLOSION" # 스티커 터짐
    VIS_GREEN_SCREEN = "VIS_GREEN_SCREEN"           # 그린스크린 합성
    
    # === Outro Patterns (35-44) ===
    VIS_FADE_OUT = "VIS_FADE_OUT"                   # 페이드 아웃
    VIS_CTA_CARD = "VIS_CTA_CARD"                   # CTA 카드
    VIS_LOOP_SEAMLESS = "VIS_LOOP_SEAMLESS"         # 무한 루프
    VIS_BLOOPER = "VIS_BLOOPER"                     # NG 장면
    VIS_CREDITS_ROLL = "VIS_CREDITS_ROLL"           # 크레딧
    VIS_CLIFFHANGER = "VIS_CLIFFHANGER"             # 궁금증 유발 엔딩
    VIS_SATISFYING_END = "VIS_SATISFYING_END"       # 만족스러운 마무리
    VIS_CALLBACK_INTRO = "VIS_CALLBACK_INTRO"       # 인트로 콜백
    VIS_DUET_READY = "VIS_DUET_READY"               # 듀엣 대기 포맷
    VIS_COMMENT_BAIT = "VIS_COMMENT_BAIT"           # 댓글 유도
    
    # === Special Patterns (45-49) ===
    VIS_ASMR_CLOSE = "VIS_ASMR_CLOSE"               # ASMR 클로즈업
    VIS_MUKBANG = "VIS_MUKBANG"                     # 먹방
    VIS_OOTD = "VIS_OOTD"                           # 오오티디
    VIS_HAUL = "VIS_HAUL"                           # 하울
    VIS_OTHER = "VIS_OTHER"                         # 기타 (분류 불가)


class AudioPatternCode(str, Enum):
    """
    정규화된 오디오 패턴 코드 (30개)
    GA/RL State Space의 Audio Dimension
    """
    # === Build-up (0-9) ===
    AUD_SILENCE_BUILD = "AUD_SILENCE_BUILD"         # 침묵 → 빌드업
    AUD_RISING_TENSION = "AUD_RISING_TENSION"       # 긴장 고조
    AUD_VOICEOVER_INTRO = "AUD_VOICEOVER_INTRO"     # 보이스오버 시작
    AUD_DIALOGUE_HOOK = "AUD_DIALOGUE_HOOK"         # 대사 훅
    AUD_SOUND_EFFECT_PUNCH = "AUD_SOUND_EFFECT_PUNCH"  # 효과음 펀치
    AUD_WHISPER_ASMR = "AUD_WHISPER_ASMR"           # 속삭임 ASMR
    AUD_AMBIENT_INTRO = "AUD_AMBIENT_INTRO"         # 환경음 시작
    AUD_TRENDING_SOUND = "AUD_TRENDING_SOUND"       # 트렌딩 사운드
    AUD_ORIGINAL_AUDIO = "AUD_ORIGINAL_AUDIO"       # 오리지널 오디오
    AUD_COVER_REMIX = "AUD_COVER_REMIX"             # 커버/리믹스
    
    # === Drop/Climax (10-19) ===
    AUD_BASS_DROP = "AUD_BASS_DROP"                 # 베이스 드롭
    AUD_BEAT_SWITCH = "AUD_BEAT_SWITCH"             # 비트 전환
    AUD_VOCAL_HOOK = "AUD_VOCAL_HOOK"               # 보컬 훅
    AUD_INSTRUMENTAL_PEAK = "AUD_INSTRUMENTAL_PEAK" # 악기 피크
    AUD_CHORUS_HIT = "AUD_CHORUS_HIT"               # 코러스 진입
    AUD_SYNC_MOMENT = "AUD_SYNC_MOMENT"             # 싱크 포인트
    AUD_DRAMATIC_PAUSE = "AUD_DRAMATIC_PAUSE"       # 드라마틱 멈춤
    AUD_CRASH_CYMBAL = "AUD_CRASH_CYMBAL"           # 심벌 크래시
    AUD_RECORD_SCRATCH = "AUD_RECORD_SCRATCH"       # 레코드 스크래치
    AUD_MEME_SOUND = "AUD_MEME_SOUND"               # 밈 사운드
    
    # === Sustain/Outro (20-29) ===
    AUD_FADE_OUT = "AUD_FADE_OUT"                   # 페이드 아웃
    AUD_LOOP_POINT = "AUD_LOOP_POINT"               # 루프 포인트
    AUD_SPEECH_ENDING = "AUD_SPEECH_ENDING"         # 대사 마무리
    AUD_NOTIFICATION_SFX = "AUD_NOTIFICATION_SFX"   # 알림음
    AUD_APPLAUSE = "AUD_APPLAUSE"                   # 박수
    AUD_LAUGH_TRACK = "AUD_LAUGH_TRACK"             # 웃음 트랙
    AUD_GASP_REACTION = "AUD_GASP_REACTION"         # 헐 리액션
    AUD_DING_SFX = "AUD_DING_SFX"                   # 딩 효과음
    AUD_WHOOSH = "AUD_WHOOSH"                       # 휙 효과음
    AUD_OTHER = "AUD_OTHER"                         # 기타 (분류 불가)


class SemanticIntent(str, Enum):
    """
    시청자 심리 유도 의도 (10개)
    GA/RL State Space의 Intent Dimension
    """
    AROUSE_CURIOSITY = "AROUSE_CURIOSITY"           # 호기심 유발
    DELIVER_INFO = "DELIVER_INFO"                   # 정보 전달
    BUILD_TENSION = "BUILD_TENSION"                 # 긴장 고조
    DELIVER_PUNCHLINE = "DELIVER_PUNCHLINE"         # 펀치라인 전달
    EMOTIONAL_PEAK = "EMOTIONAL_PEAK"               # 감정 피크
    PROVIDE_SATISFACTION = "PROVIDE_SATISFACTION"  # 만족감 제공
    TRIGGER_NOSTALGIA = "TRIGGER_NOSTALGIA"         # 향수 유발
    CREATE_FOMO = "CREATE_FOMO"                     # FOMO 생성
    CALL_TO_ACTION = "CALL_TO_ACTION"               # 행동 유도
    GENERIC_FILLER = "GENERIC_FILLER"               # 일반 채움


# === Utility Functions ===

def get_all_visual_codes() -> List[str]:
    return [code.value for code in VisualPatternCode]

def get_all_audio_codes() -> List[str]:
    return [code.value for code in AudioPatternCode]

def get_all_intent_codes() -> List[str]:
    return [code.value for code in SemanticIntent]

def get_codebook_prompt_section() -> str:
    """
    Gemini 프롬프트에 삽입할 Codebook 섹션 생성
    """
    visual_list = ", ".join([f'"{c.value}"' for c in VisualPatternCode])
    audio_list = ", ".join([f'"{c.value}"' for c in AudioPatternCode])
    intent_list = ", ".join([f'"{c.value}"' for c in SemanticIntent])
    
    return f"""
    ### IMPORTANT: Use ONLY these standardized pattern codes:
    
    **Visual Pattern Codes** (choose exactly one per segment):
    [{visual_list}]
    
    **Audio Pattern Codes** (choose exactly one per segment):
    [{audio_list}]
    
    **Semantic Intent Codes** (choose exactly one per segment):
    [{intent_list}]
    
    Do NOT invent new pattern codes. If unsure, use "*_OTHER" variants.
    """
