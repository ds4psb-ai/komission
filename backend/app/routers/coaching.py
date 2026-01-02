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
from datetime import timedelta
from typing import Any, Dict, List, Literal, Optional

from app.utils.time import utcnow, iso_now_z, generate_session_id
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
from app.services.credit_service import (
    get_user_credits, check_sufficient_credits, 
    CoachingCreditManager, COACHING_COSTS
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/coaching", tags=["coaching"])


# ====================
# SCHEMAS
# ====================

class CreateSessionRequest(BaseModel):
    """세션 생성 요청"""
    # User identification
    user_id: Optional[str] = None  # 크레딧 차감용
    
    # Optional: Complete DirectorPack if client has it 
    director_pack: Optional[DirectorPack] = None
    
    # Or: Just provide video_id for server-side VDG loading
    video_id: Optional[str] = None
    pack_id: Optional[str] = None
    
    language: str = "ko"
    voice_style: Literal["strict", "friendly", "neutral"] = "friendly"
    
    # Coaching tier (크레딧 비용 결정)
    coaching_tier: Literal["basic", "pro"] = "basic"


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
    
    # Credits info
    coaching_tier: Literal["basic", "pro"] = "basic"
    credits_balance: Optional[int] = None
    credits_cost_per_min: Optional[int] = None


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
    
    DirectorPack 로딩 우선순위:
    1. request.director_pack (프론트엔드 제공)
    2. VDG 분석 기반 (video_id → compile_director_pack)
    3. Fallback: create_proof_pack (TOP 3 proof patterns)
    """
    from app.services.proof_patterns import create_proof_pack
    from app.routers.coaching_ws import load_director_pack_from_video
    
    session_id = generate_session_id()
    now = utcnow()
    expires_at = now + timedelta(hours=1)  # 1시간 후 만료
    
    # 크레딧 검증 (user_id가 있는 경우)
    user_id = request.user_id or "anonymous"
    coaching_tier = request.coaching_tier
    credits_balance = None
    
    if user_id != "anonymous":
        credits_balance = get_user_credits(user_id)
        # Pro 모드는 최소 3크레딧 필요 (1분)
        min_credits = COACHING_COSTS.get(coaching_tier, 1)
        if not check_sufficient_credits(user_id, coaching_tier, 60):
            raise HTTPException(
                status_code=402,
                detail=f"크레딧이 부족합니다. 현재: {credits_balance}, 필요: {min_credits}/분"
            )
    
    # DirectorPack 결정: 3단계 우선순위
    pack = request.director_pack
    pack_source = "provided"
    
    if pack is None:
        # 2. VDG 분석 기반 DirectorPack 시도
        if request.video_id:
            try:
                pack = await load_director_pack_from_video(video_id=request.video_id)
                if pack:
                    pack_source = "vdg_analysis"
                    logger.info(f"✅ VDG DirectorPack loaded: {pack.pattern_id}, {len(pack.dna_invariants)} rules")
            except Exception as e:
                logger.warning(f"VDG pack load failed: {e}")
        
        # 3. Fallback: create_proof_pack (TOP 3 proof patterns)
        if pack is None:
            try:
                pack = create_proof_pack()
                pack_source = "proof_pack_fallback"
                logger.info(f"Using fallback proof_pack: {pack.pattern_id}")
            except Exception as e:
                logger.warning(f"Failed to create proof_pack: {e}")
                raise HTTPException(status_code=500, detail="Failed to create DirectorPack")
    
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
        # P0: video_id for WebSocket DirectorPack reload
        "video_id": request.video_id,
        # P1: Control group fields
        "assignment": assignment_result.assignment,
        "holdout_group": assignment_result.holdout_group,
        # Credits
        "user_id": user_id,
        "coaching_tier": coaching_tier,
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
        coaching_tier=coaching_tier,
        credits_balance=credits_balance,
        credits_cost_per_min=COACHING_COSTS.get(coaching_tier, 1),
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
async def end_session(
    session_id: str,
    duration_sec: float = 0,  # 코칭 시간 (초)
):
    """세션 종료 및 크레딧 차감"""
    from app.services.credit_service import deduct_coaching_credits
    
    session = get_session(session_id)
    session["status"] = "ended"
    session["duration_sec"] = duration_sec
    
    # 크레딧 차감
    credits_deducted = 0
    user_id = session.get("user_id", "anonymous")
    coaching_tier = session.get("coaching_tier", "basic")
    
    if user_id != "anonymous" and duration_sec > 0:
        from app.services.credit_service import calculate_coaching_cost
        credits_deducted = calculate_coaching_cost(coaching_tier, duration_sec)
        deduct_coaching_credits(user_id, coaching_tier, duration_sec, session_id)
        logger.info(f"Deducted {credits_deducted} credits for session {session_id}")
    
    logger.info(f"Ended coaching session: {session_id}, duration={duration_sec}s")
    
    return {
        "ended": True,
        "session_id": session_id,
        "duration_sec": duration_sec,
        "credits_deducted": credits_deducted,
        "coaching_tier": coaching_tier,
    }



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
        "timestamp": iso_now_z(),
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
        delivered_at=iso_now_z(),
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


@router.get("/quality/report")
async def get_log_quality_report():
    """
    P1: 로그 품질 검증 리포트
    
    검증 항목:
    - intervention_outcome_join_rate (≥95%)
    - compliance_unknown_rate (≤15%)
    - control_group_ratio (8-12%)
    - minimum_sessions (≥10)
    
    Returns:
        LogQualityReport with flywheel readiness status
    """
    from app.services.log_quality_validator import get_log_quality_validator
    
    validator = get_log_quality_validator()
    report = validator.validate_all_sessions()
    
    return {
        "total_sessions": report.total_sessions,
        "overall_status": report.overall_status.value,
        "is_ready_for_flywheel": report.is_ready_for_flywheel,
        "summary": report.summary,
        "checks": [
            {
                "name": c.name,
                "status": c.status.value,
                "actual_value": c.actual_value,
                "threshold": c.threshold,
                "description": c.description,
                "recommendation": c.recommendation,
            }
            for c in report.checks
        ]
    }


@router.get("/quality/session/{session_id}")
async def get_session_quality(session_id: str):
    """P1: 개별 세션 로그 품질 검증"""
    get_session(session_id)  # Verify session exists
    
    from app.services.log_quality_validator import get_log_quality_validator
    
    validator = get_log_quality_validator()
    checks = validator.validate_session(session_id)
    
    overall_pass = all(c.status.value == "pass" for c in checks)
    
    return {
        "session_id": session_id,
        "overall_pass": overall_pass,
        "checks": [
            {
                "name": c.name,
                "status": c.status.value,
                "actual_value": c.actual_value,
                "threshold": c.threshold,
                "description": c.description,
                "recommendation": c.recommendation,
            }
            for c in checks
        ]
    }


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


# ====================
# CREDITS API
# ====================

@router.get("/credits/{user_id}")
async def get_credits_balance(user_id: str):
    """사용자 크레딧 잔액 조회"""
    balance = get_user_credits(user_id)
    
    return {
        "user_id": user_id,
        "balance": balance,
        "costs": COACHING_COSTS,
    }


@router.post("/credits/{user_id}/add")
async def add_credits(
    user_id: str,
    amount: int,
    reason: str = "purchase",
):
    """크레딧 추가 (구매, 보너스 등)"""
    from app.services.credit_service import add_credits as add_user_credits
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    success = add_user_credits(user_id, amount, reason)
    balance = get_user_credits(user_id)
    
    return {
        "success": success,
        "user_id": user_id,
        "added": amount,
        "balance": balance,
    }


@router.get("/credits/{user_id}/transactions")
async def get_credits_transactions(user_id: str, limit: int = 20):
    """사용자 크레딧 트랜잭션 내역"""
    from app.services.credit_service import get_user_transactions
    
    transactions = get_user_transactions(user_id, limit)
    balance = get_user_credits(user_id)
    
    return {
        "user_id": user_id,
        "balance": balance,
        "transactions": transactions,
    }


# ====================
# CAMPAIGN CREDIT GRANT (체험단)
# ====================

class CampaignCreditGrantRequest(BaseModel):
    """체험단 크레딧 지원 요청"""
    creator_id: str
    amount: int
    granted_by: Optional[str] = None


@router.post("/campaigns/{campaign_id}/grant-credits")
async def grant_campaign_credits_to_creator(
    campaign_id: str,
    request: CampaignCreditGrantRequest,
):
    """
    체험단 캠페인에서 크리에이터에게 크레딧 지원
    
    브랜드가 선정된 크리에이터에게 Pro 코칭 비용 지원
    """
    from app.services.credit_service import grant_campaign_credits
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    success = grant_campaign_credits(
        user_id=request.creator_id,
        campaign_id=campaign_id,
        amount=request.amount,
        granted_by=request.granted_by,
    )
    
    balance = get_user_credits(request.creator_id)
    
    logger.info(f"Campaign {campaign_id} granted {request.amount} credits to {request.creator_id[:8]}...")
    
    return {
        "success": success,
        "campaign_id": campaign_id,
        "creator_id": request.creator_id,
        "granted": request.amount,
        "balance": balance,
    }

