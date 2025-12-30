"""
Agent Router v1.1 - 채팅형 에이전트 API

v1.1 Hardening:
- IntentClassifier: 사용자 의도 분류
- ChatContext: 대화 컨텍스트 관리
- ActionExecutor: 실행 가능 액션 시스템
- 재시도 로직 + Rate limiting

Strategic Pivot P0:
- 기술 언어 → 크리에이터 언어
- 자연어 기반 콘텐츠 전략 에이전트

Endpoints:
- POST /api/v1/agent/chat - 채팅 메시지 처리
- GET /api/v1/agent/suggestions - 추천 프롬프트
- POST /api/v1/agent/action - 액션 실행
"""
import os
import re
import logging
from typing import List, Optional, Literal, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from app.services.genai_client import get_genai_client, DEFAULT_MODEL_FLASH

from app.routers.auth import get_current_user
from app.services.proof_patterns import (
    TOP_3_PROOF_PATTERNS, get_pattern_by_id, create_proof_pack,
    get_metric_evaluator
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


# ====================
# INTENT CLASSIFICATION
# ====================

class Intent(str, Enum):
    """사용자 의도 분류"""
    ANALYZE_TREND = "analyze_trend"      # 트렌드 분석
    CREATE_HOOK = "create_hook"          # 훅 아이디어 생성
    GET_COACHING = "get_coaching"        # 촬영 코칭
    EXPLAIN_RULE = "explain_rule"        # 규칙 설명
    REMIX_GUIDE = "remix_guide"          # 변주 가이드
    CAMPAIGN_HELP = "campaign_help"      # 캠페인 도움
    GENERAL_CHAT = "general_chat"        # 일반 대화


@dataclass
class ClassifiedIntent:
    """분류된 인텐트 결과"""
    intent: Intent
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)


class IntentClassifier:
    """
    규칙 기반 인텐트 분류기
    
    Usage:
        classifier = IntentClassifier()
        result = classifier.classify("3초 훅 아이디어 만들어줘")
        # result.intent == Intent.CREATE_HOOK
    """
    
    # 키워드 → 인텐트 매핑
    INTENT_PATTERNS = {
        Intent.ANALYZE_TREND: ["트렌드", "분석", "인기", "핫한", "요즘", "최근"],
        Intent.CREATE_HOOK: ["훅", "아이디어", "만들어", "생성", "추천해", "3초"],
        Intent.GET_COACHING: ["촬영", "코칭", "팁", "조언", "어떻게", "방법"],
        Intent.EXPLAIN_RULE: ["규칙", "뭐야", "설명", "알려줘", "핵심", "불변"],
        Intent.REMIX_GUIDE: ["변주", "리믹스", "따라", "참고", "원본"],
        Intent.CAMPAIGN_HELP: ["캠페인", "체험단", "브랜드", "광고", "협찬"],
    }
    
    def classify(self, message: str) -> ClassifiedIntent:
        """메시지 인텐트 분류"""
        message_lower = message.lower()
        
        # 각 인텐트별 점수 계산
        scores: Dict[Intent, float] = {}
        matched_keywords: Dict[Intent, List[str]] = {}
        
        for intent, keywords in self.INTENT_PATTERNS.items():
            score = 0.0
            matches = []
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1.0
                    matches.append(keyword)
            if score > 0:
                scores[intent] = score / len(keywords)
                matched_keywords[intent] = matches
        
        # 최고 점수 인텐트 선택
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = min(1.0, scores[best_intent] * 2)  # 0.5 이상이면 확신
            return ClassifiedIntent(
                intent=best_intent,
                confidence=confidence,
                keywords=matched_keywords.get(best_intent, [])
            )
        
        # 기본: 일반 대화
        return ClassifiedIntent(
            intent=Intent.GENERAL_CHAT,
            confidence=0.5
        )


# ====================
# CHAT CONTEXT
# ====================

@dataclass
class ChatContext:
    """대화 컨텍스트 관리"""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_intent: Optional[Intent] = None
    topic_stack: List[str] = field(default_factory=list)
    mentioned_patterns: List[str] = field(default_factory=list)
    action_history: List[dict] = field(default_factory=list)
    
    def push_topic(self, topic: str):
        """토픽 스택에 추가"""
        if topic not in self.topic_stack:
            self.topic_stack.append(topic)
            if len(self.topic_stack) > 5:
                self.topic_stack.pop(0)
    
    def get_context_summary(self) -> str:
        """컨텍스트 요약 생성"""
        parts = []
        if self.topic_stack:
            parts.append(f"최근 토픽: {', '.join(self.topic_stack[-3:])}")
        if self.mentioned_patterns:
            parts.append(f"언급된 패턴: {', '.join(self.mentioned_patterns)}")
        return " | ".join(parts) if parts else "새 대화"


# Chat context storage (in-memory, should be Redis in production)
_chat_contexts: Dict[str, ChatContext] = {}


def get_or_create_context(session_id: str, user_id: str) -> ChatContext:
    """세션별 컨텍스트 가져오기 또는 생성"""
    key = f"{user_id}:{session_id}"
    if key not in _chat_contexts:
        _chat_contexts[key] = ChatContext(session_id=session_id, user_id=user_id)
    return _chat_contexts[key]


# ====================
# ACTION EXECUTOR
# ====================

@dataclass
class ActionResult:
    """액션 실행 결과"""
    success: bool
    action_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


class ActionExecutor:
    """
    실행 가능 액션 처리
    
    Actions:
    - create_pack: 촬영 가이드 팩 생성
    - analyze_video: 영상 분석 시작
    - start_coaching: 코칭 세션 시작
    """
    
    AVAILABLE_ACTIONS = {
        "create_pack": "촬영 가이드 팩 생성",
        "explain_patterns": "핵심 규칙 설명",
        "start_coaching": "코칭 세션 시작",
    }
    
    def execute(self, action_type: str, params: Dict[str, Any]) -> ActionResult:
        """액션 실행"""
        if action_type == "create_pack":
            return self._create_pack(params)
        elif action_type == "explain_patterns":
            return self._explain_patterns(params)
        elif action_type == "start_coaching":
            return self._start_coaching(params)
        else:
            return ActionResult(
                success=False,
                action_type=action_type,
                message=f"Unknown action: {action_type}"
            )
    
    def _create_pack(self, params: Dict) -> ActionResult:
        """촬영 가이드 팩 생성"""
        try:
            pack = create_proof_pack()
            return ActionResult(
                success=True,
                action_type="create_pack",
                data={"pack_id": pack.pack_meta.pack_id},
                message=f"촬영 가이드 '{pack.pack_meta.pack_id}' 생성 완료!"
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type="create_pack",
                message=str(e)
            )
    
    def _explain_patterns(self, params: Dict) -> ActionResult:
        """핵심 규칙 설명"""
        patterns = []
        for p in TOP_3_PROOF_PATTERNS:
            patterns.append({
                "id": p.rule_id,
                "hint": p.check_hint,
                "coaching": p.coach_line_templates.friendly
            })
        return ActionResult(
            success=True,
            action_type="explain_patterns",
            data={"patterns": patterns}
        )
    
    def _start_coaching(self, params: Dict) -> ActionResult:
        """코칭 세션 시작 (placeholder)"""
        return ActionResult(
            success=True,
            action_type="start_coaching",
            data={"redirect": "/session/shoot"},
            message="촬영 코칭 페이지로 이동합니다!"
        )


# Singleton instances
_intent_classifier = IntentClassifier()
_action_executor = ActionExecutor()


# ====================
# SCHEMAS
# ====================

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[str] = None  # outlier_id, pattern_id 등
    history: List[ChatMessage] = Field(default_factory=list)
    stream: bool = False


class ChatResponse(BaseModel):
    message: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    suggestions: List[str] = Field(default_factory=list)
    actions: List[dict] = Field(default_factory=list)


class ActionRequest(BaseModel):
    action_type: str
    params: Dict[str, Any] = Field(default_factory=dict)


class ActionResponse(BaseModel):
    success: bool
    action_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


class SuggestionResponse(BaseModel):
    suggestions: List[dict] = Field(default_factory=list)


# ====================
# SYSTEM PROMPT
# ====================

AGENT_SYSTEM_PROMPT = """당신은 "코미션 에이전트"입니다. 바이럴 숏폼 콘텐츠 전문가로서 크리에이터를 돕습니다.

## 핵심 역할
1. 바이럴 콘텐츠 분석 및 인사이트 제공
2. 촬영 코칭 (3대 핵심 규칙)
3. 트렌드 기반 콘텐츠 전략 제안

## 3대 핵심 규칙 (불변)
1. **2초 훅**: 시작 2초 내 강한 펀치 필수
2. **중앙 앵커**: 훅 구간 피사체 중앙 고정 (±12%)
3. **밝기 바닥선**: 화면 밝기 55% 이상 유지

## 응답 스타일
- 친근하고 프로페셔널하게
- 실행 가능한 구체적 조언
- 복잡한 기술 용어 금지
- 이모지 적절히 사용

## 용어 변환 (기술 → 크리에이터)
- VDG → 바이럴 DNA
- Evidence Loop → 성공 근거
- Parent/Kid → 원본/변주
- Pack → 촬영 가이드
- Invariant → 핵심 규칙

## 현재 패턴 정보
{pattern_context}
"""

def get_pattern_context() -> str:
    """현재 활성 패턴 정보 생성"""
    lines = ["### 활성 패턴"]
    for p in TOP_3_PROOF_PATTERNS:
        lines.append(f"- **{p.rule_id}**: {p.check_hint}")
        if p.coach_line_templates.friendly:
            lines.append(f"  - 코칭: \"{p.coach_line_templates.friendly}\"")
    return "\n".join(lines)


# ====================
# ENDPOINTS
# ====================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user = Depends(get_current_user)
):
    """
    채팅 메시지 처리 (v1.1)
    
    1. 인텐트 분류
    2. 컨텍스트 업데이트
    3. Gemini 응답 생성
    4. 액션 제안
    """
    user_id = user.get("uid", "anonymous")
    session_id = request.session_id or "default"
    
    try:
        # 1. 인텐트 분류
        classified = _intent_classifier.classify(request.message)
        logger.info(f"Intent: {classified.intent.value} (conf={classified.confidence:.2f})")
        
        # 2. 컨텍스트 관리
        context = get_or_create_context(session_id, user_id)
        context.last_intent = classified.intent
        if classified.keywords:
            context.push_topic(classified.keywords[0])
        
        # 3. 컨텍스트 구성
        pattern_context = get_pattern_context()
        context_summary = context.get_context_summary()
        system_prompt = AGENT_SYSTEM_PROMPT.format(pattern_context=pattern_context)
        if context_summary != "새 대화":
            system_prompt += f"\n\n## 대화 컨텍스트\n{context_summary}"
        
        # 4. 대화 히스토리 구성
        history_contents = []
        for msg in request.history:
            role = "user" if msg.role == "user" else "model"
            history_contents.append({"role": role, "parts": [{"text": msg.content}]})
        
        # 5. 현재 메시지 추가
        history_contents.append({"role": "user", "parts": [{"text": request.message}]})
        
        # 6. Gemini 생성 (새 SDK)
        client = get_genai_client()
        response = client.models.generate_content(
            model=DEFAULT_MODEL_FLASH,
            contents=history_contents,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7,
                "max_output_tokens": 4096,
            }
        )
        
        # 7. 인텐트 기반 추천 + 액션 생성
        suggestions = _generate_suggestions_by_intent(classified)
        actions = _generate_actions_by_intent(classified)
        
        return ChatResponse(
            message=response.text,
            intent=classified.intent.value,
            confidence=classified.confidence,
            suggestions=suggestions,
            actions=actions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action", response_model=ActionResponse)
async def execute_action(
    request: ActionRequest,
    user = Depends(get_current_user)
):
    """
    액션 실행
    
    가능한 액션:
    - create_pack: 촬영 가이드 팩 생성
    - explain_patterns: 핵심 규칙 설명
    - start_coaching: 코칭 세션 시작
    """
    try:
        result = _action_executor.execute(request.action_type, request.params)
        return ActionResponse(
            success=result.success,
            action_type=result.action_type,
            data=result.data,
            message=result.message
        )
    except Exception as e:
        logger.error(f"Action error: {e}")
        return ActionResponse(
            success=False,
            action_type=request.action_type,
            message=str(e)
        )


@router.get("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    user = Depends(get_current_user)
):
    """추천 프롬프트 목록"""
    return SuggestionResponse(
        suggestions=[
            {"id": "analyze_trend", "text": "지난주 뷰티 트렌드 분석해줘", "category": "분석"},
            {"id": "hook_ideas", "text": "3초 훅 아이디어 3개 만들어줘", "category": "창작"},
            {"id": "coaching_tips", "text": "촬영할 때 주의할 점 알려줘", "category": "코칭"},
            {"id": "pattern_explain", "text": "핵심 규칙 3가지가 뭐야?", "category": "학습"},
            {"id": "remix_guide", "text": "이 영상 변주하는 법 알려줘", "category": "창작"},
            {"id": "o2o_campaign", "text": "체험단 캠페인 준비하려면?", "category": "비즈니스"}
        ]
    )


@router.get("/actions")
async def list_available_actions(
    user = Depends(get_current_user)
):
    """사용 가능한 액션 목록"""
    return {
        "actions": [
            {"type": k, "description": v} 
            for k, v in _action_executor.AVAILABLE_ACTIONS.items()
        ]
    }


# ====================
# HELPER FUNCTIONS
# ====================

def _generate_suggestions_by_intent(classified: ClassifiedIntent) -> List[str]:
    """인텐트 기반 추천 생성"""
    intent_suggestions = {
        Intent.ANALYZE_TREND: ["이번 주 핫한 포맷은?", "뷰티 외 다른 카테고리는?", "경쟁자 분석해줘"],
        Intent.CREATE_HOOK: ["더 강한 훅 아이디어 보여줘", "다른 스타일 훅은?", "성공 사례 보여줘"],
        Intent.GET_COACHING: ["조명 팁도 알려줘", "음성 녹음 팁은?", "편집 팁도 알려줘"],
        Intent.EXPLAIN_RULE: ["실제 예시 보여줘", "규칙 어기면 어떻게 돼?", "연습 방법 알려줘"],
        Intent.REMIX_GUIDE: ["원본 영상 추천해줘", "어떤 부분을 바꿔야 해?", "변주 성공 사례는?"],
        Intent.CAMPAIGN_HELP: ["어떤 브랜드가 좋을까?", "단가는 어느 정도?", "계약서 팁 알려줘"],
        Intent.GENERAL_CHAT: ["무엇을 도와드릴까요?", "사용법 알려줘", "핵심 기능이 뭐야?"],
    }
    
    return intent_suggestions.get(classified.intent, ["더 자세히 설명해줘"])[:3]


def _generate_actions_by_intent(classified: ClassifiedIntent) -> List[dict]:
    """인텐트 기반 액션 제안"""
    intent_actions = {
        Intent.GET_COACHING: [
            {"type": "start_coaching", "label": "🎬 촬영 시작하기"},
            {"type": "create_pack", "label": "📦 촬영 가이드 받기"}
        ],
        Intent.EXPLAIN_RULE: [
            {"type": "explain_patterns", "label": "📋 규칙 상세보기"}
        ],
        Intent.CREATE_HOOK: [
            {"type": "create_pack", "label": "📦 훅 가이드 생성"}
        ],
    }
    
    return intent_actions.get(classified.intent, [])

