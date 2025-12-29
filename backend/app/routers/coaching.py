"""
Audio Coach API Router

DirectorPack 기반 실시간 오디오 코칭 세션 관리

Endpoints:
- POST /coaching/sessions - 새 코칭 세션 생성
- GET /coaching/sessions/{session_id} - 세션 상태 조회
- DELETE /coaching/sessions/{session_id} - 세션 종료
- POST /coaching/sessions/{session_id}/feedback - 사용자 피드백
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.schemas.director_pack import DirectorPack
from app.services.audio_coach import AudioCoach

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/coaching", tags=["coaching"])


# ====================
# SCHEMAS
# ====================

class CreateSessionRequest(BaseModel):
    """세션 생성 요청"""
    director_pack: DirectorPack
    language: str = "ko"
    voice_style: Literal["strict", "friendly", "neutral"] = "friendly"


class SessionResponse(BaseModel):
    """세션 응답"""
    session_id: str
    status: Literal["created", "active", "ended", "error"]
    websocket_url: str
    created_at: str
    expires_at: str
    pattern_id: str
    goal: Optional[str] = None


class SessionListResponse(BaseModel):
    """세션 목록"""
    sessions: List[SessionResponse]
    total: int


class FeedbackRequest(BaseModel):
    """사용자 피드백"""
    rule_id: str
    feedback_type: Literal["helpful", "not_helpful", "too_early", "too_late"]
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    recorded: bool
    message: str


# ====================
# IN-MEMORY SESSION STORE (MVP)
# ====================

# Production에서는 Redis 사용 권장
_sessions: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str) -> Dict[str, Any]:
    """세션 조회"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return _sessions[session_id]


# ====================
# ENDPOINTS
# ====================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
):
    """
    새 코칭 세션 생성
    
    DirectorPack을 기반으로 Gemini Live 세션을 준비합니다.
    실제 연결은 WebSocket을 통해 이루어집니다.
    """
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=1)  # 1시간 후 만료
    
    # DirectorPack에서 코칭 컨텍스트 생성
    pack = request.director_pack
    
    # 세션 저장
    _sessions[session_id] = {
        "session_id": session_id,
        "status": "created",
        "director_pack": pack.model_dump(),
        "language": request.language,
        "voice_style": request.voice_style,
        "created_at": now.isoformat() + "Z",
        "expires_at": expires_at.isoformat() + "Z",
        "pattern_id": pack.pattern_id,
        "goal": pack.goal,
        "feedbacks": [],
    }
    
    logger.info(f"Created coaching session: {session_id} for pattern: {pack.pattern_id}")
    
    # WebSocket URL 생성 (실제 환경에서는 도메인 설정 필요)
    websocket_url = f"wss://api.komission.ai/v1/coaching/sessions/{session_id}/ws"
    
    return SessionResponse(
        session_id=session_id,
        status="created",
        websocket_url=websocket_url,
        created_at=now.isoformat() + "Z",
        expires_at=expires_at.isoformat() + "Z",
        pattern_id=pack.pattern_id,
        goal=pack.goal,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_status(session_id: str):
    """세션 상태 조회"""
    session = get_session(session_id)
    
    return SessionResponse(
        session_id=session["session_id"],
        status=session["status"],
        websocket_url=f"wss://api.komission.ai/v1/coaching/sessions/{session_id}/ws",
        created_at=session["created_at"],
        expires_at=session["expires_at"],
        pattern_id=session["pattern_id"],
        goal=session.get("goal"),
    )


@router.delete("/sessions/{session_id}")
async def end_session(session_id: str):
    """세션 종료"""
    session = get_session(session_id)
    session["status"] = "ended"
    
    logger.info(f"Ended coaching session: {session_id}")
    
    return {"ended": True, "session_id": session_id}


@router.post("/sessions/{session_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(session_id: str, request: FeedbackRequest):
    """
    사용자 피드백 제출
    
    코칭 품질 개선을 위한 피드백 수집
    """
    session = get_session(session_id)
    
    feedback = {
        "rule_id": request.rule_id,
        "feedback_type": request.feedback_type,
        "comment": request.comment,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    session["feedbacks"].append(feedback)
    
    logger.info(f"Feedback recorded for session {session_id}: {request.feedback_type}")
    
    return FeedbackResponse(
        recorded=True,
        message="피드백이 기록되었습니다. 감사합니다!",
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    status: Optional[Literal["created", "active", "ended"]] = None,
    limit: int = 20,
):
    """활성 세션 목록 조회 (관리용)"""
    sessions = list(_sessions.values())
    
    if status:
        sessions = [s for s in sessions if s["status"] == status]
    
    # 최신순 정렬
    sessions.sort(key=lambda s: s["created_at"], reverse=True)
    sessions = sessions[:limit]
    
    return SessionListResponse(
        sessions=[
            SessionResponse(
                session_id=s["session_id"],
                status=s["status"],
                websocket_url=f"wss://api.komission.ai/v1/coaching/sessions/{s['session_id']}/ws",
                created_at=s["created_at"],
                expires_at=s["expires_at"],
                pattern_id=s["pattern_id"],
                goal=s.get("goal"),
            )
            for s in sessions
        ],
        total=len(_sessions),
    )


# ====================
# HELPER: DIRECTOR PACK → SYSTEM PROMPT
# ====================

def build_system_prompt(pack: DirectorPack, voice_style: str = "friendly") -> str:
    """
    DirectorPack → 코칭 시스템 프롬프트 변환
    
    DNAInvariant 규칙들을 자연어 코칭 가이드로 변환
    """
    lines = [
        "너는 숏폼 촬영 코치야.",
        f"패턴: {pack.pattern_id}",
        f"목표: {pack.goal or '최적의 촬영 결과 달성'}",
        "",
        "=== 핵심 규칙 ===",
    ]
    
    # DNAInvariant 규칙 추가
    for rule in pack.dna_invariants[:5]:  # 최대 5개
        priority_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "⚪",
        }.get(rule.priority, "")
        
        # 코칭 대사 선택
        if voice_style == "strict" and rule.coach_line_templates.strict:
            coach_line = rule.coach_line_templates.strict
        elif voice_style == "friendly" and rule.coach_line_templates.friendly:
            coach_line = rule.coach_line_templates.friendly
        else:
            coach_line = rule.coach_line_templates.neutral or rule.check_hint or ""
        
        lines.append(f"{priority_emoji} [{rule.domain}] {coach_line}")
    
    # 금기 사항
    if pack.forbidden_mutations:
        lines.append("\n=== 하지 말아야 할 것 ===")
        for fm in pack.forbidden_mutations[:3]:
            lines.append(f"❌ {fm.reason}")
    
    # 정책
    lines.extend([
        "",
        "=== 응답 스타일 ===",
        f"- 쿨다운: 명령 후 {pack.policy.cooldown_sec}초 대기",
        "- 짧고 명확하게 (1-2문장)",
        "- 한국어로 자연스럽게",
    ])
    
    return "\n".join(lines)
