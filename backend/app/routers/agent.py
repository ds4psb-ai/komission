"""
Agent Router - 채팅형 에이전트 API

Strategic Pivot P0:
- 기술 언어 → 크리에이터 언어
- 자연어 기반 콘텐츠 전략 에이전트

Endpoints:
- POST /api/v1/agent/chat - 채팅 메시지 처리
- GET /api/v1/agent/suggestions - 추천 프롬프트
"""
import os
import logging
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import google.generativeai as genai

from app.routers.auth import require_auth
from app.services.proof_patterns import (
    TOP_3_PROOF_PATTERNS, get_pattern_by_id, create_proof_pack
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


# ====================
# SCHEMAS
# ====================

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None  # outlier_id, pattern_id 등
    history: List[ChatMessage] = Field(default_factory=list)
    stream: bool = False


class ChatResponse(BaseModel):
    message: str
    suggestions: List[str] = Field(default_factory=list)
    actions: List[dict] = Field(default_factory=list)  # 실행 가능 액션


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
    user: dict = Depends(require_auth)
):
    """
    채팅 메시지 처리
    
    자연어로 질문하면 바이럴 콘텐츠 전략을 제안합니다.
    """
    try:
        # API 키 체크
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        
        # 시스템 프롬프트 구성
        pattern_context = get_pattern_context()
        system_prompt = AGENT_SYSTEM_PROMPT.format(pattern_context=pattern_context)
        
        # 대화 히스토리 구성
        history = []
        for msg in request.history:
            history.append({
                "role": msg.role if msg.role != "assistant" else "model",
                "parts": [msg.content]
            })
        
        # Gemini 모델 생성
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system_prompt
        )
        
        # 채팅 시작
        chat = model.start_chat(history=history)
        
        # 응답 생성
        response = chat.send_message(request.message)
        
        # 추천 액션 생성
        suggestions = _generate_suggestions(request.message)
        
        return ChatResponse(
            message=response.text,
            suggestions=suggestions,
            actions=[]
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    user: dict = Depends(require_auth)
):
    """추천 프롬프트 목록"""
    return SuggestionResponse(
        suggestions=[
            {
                "id": "analyze_trend",
                "text": "지난주 뷰티 트렌드 분석해줘",
                "category": "분석"
            },
            {
                "id": "hook_ideas",
                "text": "3초 훅 아이디어 3개 만들어줘",
                "category": "창작"
            },
            {
                "id": "coaching_tips",
                "text": "촬영할 때 주의할 점 알려줘",
                "category": "코칭"
            },
            {
                "id": "pattern_explain",
                "text": "핵심 규칙 3가지가 뭐야?",
                "category": "학습"
            },
            {
                "id": "remix_guide",
                "text": "이 영상 변주하는 법 알려줘",
                "category": "창작"
            },
            {
                "id": "o2o_campaign",
                "text": "체험단 캠페인 준비하려면?",
                "category": "비즈니스"
            }
        ]
    )


def _generate_suggestions(user_message: str) -> List[str]:
    """메시지 기반 추천 생성"""
    suggestions = []
    
    if "훅" in user_message or "시작" in user_message:
        suggestions.append("더 강한 훅 아이디어 보여줘")
    if "촬영" in user_message or "코칭" in user_message:
        suggestions.append("조명 팁도 알려줘")
    if "트렌드" in user_message or "분석" in user_message:
        suggestions.append("이번 주 핫한 포맷은?")
    
    # 기본 추천
    if not suggestions:
        suggestions = [
            "실제 예시 보여줘",
            "더 자세히 설명해줘"
        ]
    
    return suggestions[:3]
