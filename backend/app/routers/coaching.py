"""
Audio Coach API Router

DirectorPack 기반 실시간 오디오 코칭 세션 관리

Endpoints:
- POST /coaching/sessions - 새 코칭 세션 생성 (with control group assignment)
- GET /coaching/sessions/{session_id} - 세션 상태 조회
- DELETE /coaching/sessions/{session_id} - 세션 종료
- POST /coaching/sessions/{session_id}/feedback - 사용자 피드백
- POST /coaching/sessions/{session_id}/events - 이벤트 로깅 (P1)
- GET /coaching/sessions/{session_id}/events - 이벤트 조회 (P1)
- GET /coaching/sessions/{session_id}/summary - 세션 요약 (P1)
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.schemas.director_pack import DirectorPack
from app.schemas.session_events import (
    RuleEvaluatedEvent,
    InterventionEvent,
    OutcomeEvent,
    SessionEventSummary,
)
from app.schemas.vdg_v4 import CoachingIntervention, CoachingOutcome
from app.services.audio_coach import AudioCoach
from app.services.coaching_router import get_coaching_router
from app.services.session_logger import get_session_logger

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
    
    # P1: Control Group info
    assignment: str = "coached"  # "coached" | "control"
    holdout_group: bool = False


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
    P1: Control Group (10%) + Holdout (5%) 자동 할당
    """
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=1)  # 1시간 후 만료
    
    # DirectorPack에서 코칭 컨텍스트 생성
    pack = request.director_pack
    
    # P1: Control Group 할당 (10% control, 5% holdout)
    coaching_router = get_coaching_router()
    assignment_result = coaching_router.assign_group(session_id)
    
    # P1: SessionLogger에 세션 등록
    session_logger = get_session_logger()
    session_logger.start_session(
        session_id=session_id,
        pack_id=pack.pack_meta.pack_id if pack.pack_meta else "unknown",
        assignment=assignment_result.assignment,
        holdout_group=assignment_result.holdout_group,
    )
    
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
        # P1: Control group fields
        "assignment": assignment_result.assignment,
        "holdout_group": assignment_result.holdout_group,
    }
    
    logger.info(
        f"Created coaching session: {session_id} for pattern: {pack.pattern_id} "
        f"(assignment={assignment_result.assignment}, holdout={assignment_result.holdout_group})"
    )
    
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
        assignment=assignment_result.assignment,
        holdout_group=assignment_result.holdout_group,
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
# P1: EVENT LOGGING ENDPOINTS
# ====================

class LogRuleEvaluatedRequest(BaseModel):
    """규칙 평가 로그 요청"""
    rule_id: str
    ap_id: str
    checkpoint_id: str
    result: Literal["passed", "violated", "unknown"] = "unknown"
    result_reason: Optional[str] = None
    t_video: float = 0.0
    metric_id: Optional[str] = None
    metric_value: Optional[float] = None
    evidence_id: Optional[str] = None
    intervention_triggered: bool = False


class LogInterventionRequest(BaseModel):
    """개입 로그 요청"""
    intervention_id: str
    rule_id: str
    ap_id: Optional[str] = None
    checkpoint_id: str
    t_video: float = 0.0
    command_text: str = ""
    evidence_id: Optional[str] = None


class LogOutcomeRequest(BaseModel):
    """결과 로그 요청"""
    intervention_id: str
    compliance_detected: bool = False
    compliance_unknown_reason: Optional[str] = None
    user_response: str = "unknown"
    metric_id: Optional[str] = None
    metric_before: Optional[float] = None
    metric_after: Optional[float] = None
    upload_outcome_proxy: Optional[str] = None
    reported_views: Optional[int] = None
    reported_likes: Optional[int] = None
    reported_saves: Optional[int] = None
    outcome_unknown_reason: Optional[str] = None


@router.post("/sessions/{session_id}/events/rule-evaluated")
async def log_rule_evaluated(session_id: str, request: LogRuleEvaluatedRequest):
    """
    P1: 규칙 평가 이벤트 로깅
    
    CRITICAL: 개입 없는 구간도 로깅해야 반사실 학습 가능
    """
    get_session(session_id)  # Verify session exists
    session_logger = get_session_logger()
    
    event = session_logger.log_rule_evaluated(
        session_id=session_id,
        rule_id=request.rule_id,
        ap_id=request.ap_id,
        checkpoint_id=request.checkpoint_id,
        result=request.result,
        result_reason=request.result_reason,
        t_video=request.t_video,
        metric_id=request.metric_id,
        metric_value=request.metric_value,
        evidence_id=request.evidence_id,
        intervention_triggered=request.intervention_triggered,
    )
    
    return {"logged": True, "event_id": event.event_id}


@router.post("/sessions/{session_id}/events/intervention")
async def log_intervention(session_id: str, request: LogInterventionRequest):
    """P1: 코칭 개입 이벤트 로깅"""
    session = get_session(session_id)
    session_logger = get_session_logger()
    
    # Build CoachingIntervention
    intervention = CoachingIntervention(
        intervention_id=request.intervention_id,
        session_id=session_id,
        pack_id=session.get("director_pack", {}).get("pack_meta", {}).get("pack_id", "unknown"),
        rule_id=request.rule_id,
        ap_id=request.ap_id,
        checkpoint_id=request.checkpoint_id,
        evidence_id=request.evidence_id,
        delivered_at=datetime.utcnow().isoformat(),
        t_video=request.t_video,
        command_text=request.command_text,
        assignment=session.get("assignment", "coached"),
        holdout_group=session.get("holdout_group", False),
    )
    
    event = session_logger.log_intervention(intervention)
    
    return {"logged": True, "event_id": event.event_id}


@router.post("/sessions/{session_id}/events/outcome")
async def log_outcome(session_id: str, request: LogOutcomeRequest):
    """P1: 결과 관측 이벤트 로깅 (자동 Negative Evidence 판단)"""
    get_session(session_id)  # Verify session exists
    session_logger = get_session_logger()
    
    # Build CoachingOutcome
    improvement = None
    if request.metric_before is not None and request.metric_after is not None:
        improvement = request.metric_after - request.metric_before
    
    outcome = CoachingOutcome(
        intervention_id=request.intervention_id,
        user_response=request.user_response,
        compliance_detected=request.compliance_detected,
        compliance_unknown_reason=request.compliance_unknown_reason,
        metric_id=request.metric_id,
        metric_before=request.metric_before,
        metric_after=request.metric_after,
        improvement=improvement,
        upload_outcome_proxy=request.upload_outcome_proxy,
        reported_views=request.reported_views,
        reported_likes=request.reported_likes,
        reported_saves=request.reported_saves,
        outcome_unknown_reason=request.outcome_unknown_reason,
    )
    
    event = session_logger.log_outcome(outcome)
    
    return {
        "logged": True,
        "event_id": event.event_id,
        "is_negative_evidence": event.is_negative_evidence,
        "negative_reason": event.negative_reason,
    }


@router.get("/sessions/{session_id}/events")
async def get_session_events(session_id: str):
    """P1: 세션의 모든 이벤트 조회"""
    get_session(session_id)  # Verify session exists
    session_logger = get_session_logger()
    
    events = session_logger.get_session_events(session_id)
    
    return {
        "session_id": session_id,
        "total_events": len(events),
        "events": [e.model_dump() for e in events],
    }


@router.get("/sessions/{session_id}/summary", response_model=SessionEventSummary)
async def get_session_summary(session_id: str):
    """P1: 세션 요약 통계 조회"""
    get_session(session_id)  # Verify session exists
    session_logger = get_session_logger()
    
    summary = session_logger.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session summary not found")
    
    return summary


@router.get("/stats/all-sessions")
async def get_all_sessions_stats():
    """P1: 전체 세션 통계 (Control Group 비율 검증용)"""
    session_logger = get_session_logger()
    return session_logger.get_all_sessions_summary()


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
