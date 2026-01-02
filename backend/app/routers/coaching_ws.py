"""
Real-time Audio Coaching WebSocket Router

실시간 촬영 코칭을 위한 WebSocket 엔드포인트

Messages IN (Client → Server):
- {"type": "audio", "data": "<base64 PCM>"}
- {"type": "control", "action": "start"|"pause"|"stop"}
- {"type": "metric", "rule_id": "...", "value": 0.5, "t_sec": 1.5}

Messages OUT (Server → Client):
- {"type": "feedback", "message": "...", "audio_b64": "...", "rule_id": "..."}
- {"type": "audio_response", "audio_b64": "...", "format": "pcm_24khz"}
- {"type": "rule_update", "rule_id": "...", "status": "passed"|"failed"}
- {"type": "session_status", "status": "active"|"ended", "stats": {...}}
- {"type": "error", "message": "..."}

Hardening:
- H1: Gemini audio response loop (background task)
- H2: TTS fallback (Web Speech / Google Cloud)
- H3: DirectorPack loading at session start
"""
import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

from app.services.audio_coach import AudioCoach
from app.services.coaching_session import get_coaching_service
from app.services.proof_patterns import create_proof_pack  # H3: DirectorPack fallback
from app.utils.time import utcnow

# VDG DirectorPack loading
from app.database import AsyncSessionLocal
from app.models import OutlierItem, RemixNode
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================
# H4/H7/H8: PRODUCTION STABILITY CONSTANTS
# ==================

# H4: Gemini reconnect settings
GEMINI_RECONNECT_MAX_ATTEMPTS = 3
GEMINI_RECONNECT_DELAY_SEC = 2.0

# H7: Session timeout settings
SESSION_TIMEOUT_SEC = 300  # 5 minutes of inactivity
SESSION_TIMEOUT_CHECK_INTERVAL = 30  # Check every 30 seconds

# H8: Audio send retry settings
AUDIO_SEND_MAX_RETRIES = 3
AUDIO_SEND_RETRY_DELAY_SEC = 0.5


# ==================
# ACTIVE SESSIONS MANAGER
# ==================

class CoachingSessionManager:
    """실시간 코칭 세션 관리자"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.websockets: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """WebSocket 연결"""
        await websocket.accept()
        self.websockets[session_id] = websocket
        logger.info(f"✅ Coaching WS connected: {session_id}")
        return True
    
    def disconnect(self, session_id: str):
        """연결 해제"""
        if session_id in self.websockets:
            del self.websockets[session_id]
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        logger.info(f"❌ Coaching WS disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """메시지 전송"""
        if session_id in self.websockets:
            try:
                await self.websockets[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        return self.active_sessions.get(session_id)
    
    def create_session(self, session_id: str, coach: AudioCoach, voice_style: str = "friendly") -> Dict[str, Any]:
        """세션 생성"""
        now = utcnow()
        session = {
            "session_id": session_id,
            "coach": coach,
            "started_at": now,
            "status": "idle",
            "recording_time": 0.0,
            "rules_evaluated": 0,
            "interventions_sent": 0,
            # H1: Gemini response loop task
            "response_task": None,
            # H3: Voice style for TTS
            "voice_style": voice_style,
            # H4: Gemini reconnect tracking
            "gemini_connected": False,
            "gemini_reconnect_attempts": 0,
            # H7: Session timeout tracking
            "last_activity": now,
            "timeout_task": None,
            # H8: Audio error tracking
            "audio_errors_count": 0,
        }
        self.active_sessions[session_id] = session
        return session


manager = CoachingSessionManager()


# ==================
# WEBSOCKET ENDPOINT
# ==================

@router.websocket("/ws/coaching/{session_id}")
async def coaching_websocket(
    websocket: WebSocket,
    session_id: str,
    language: str = Query(default="ko"),
    voice_style: str = Query(default="friendly"),
    video_id: Optional[str] = Query(default=None),  # RemixNode.node_id
    outlier_id: Optional[str] = Query(default=None),  # OutlierItem.id (promoted)
    # Phase 1: 출력 모드 + 페르소나
    output_mode: str = Query(default="graphic"),  # graphic | text | audio | graphic_audio
    persona: str = Query(default="calm_mentor"),  # strict_pd | close_friend | calm_mentor | energetic
):
    """
    실시간 오디오 코칭 WebSocket
    
    Connection:
        ws://localhost:8000/api/v1/ws/coaching/{session_id}?output_mode=graphic&persona=calm_mentor
    
    Parameters:
        - video_id: RemixNode.node_id (메인에 게시된 카드)
        - outlier_id: OutlierItem.id (승격된 아웃라이어)
        - output_mode: graphic(디폴트) | text | audio | graphic_audio
        - persona: strict_pd | close_friend | calm_mentor(디폴트) | energetic
    
    Flow:
        1. Connect → server sends session_status
        2. Client sends control.start → coaching begins
        3. Client sends audio chunks → server processes (if audio mode)
        4. Server sends feedback → graphic/text/audio based on output_mode
        5. Client sends control.stop → session ends
    """
    # 1. Accept connection
    if not await manager.connect(websocket, session_id):
        return
    
    try:
        # 2. Initialize AudioCoach
        coach = AudioCoach()
        session = manager.create_session(session_id, coach, voice_style)
        
        # Merge data from POST session (coaching.py._sessions) if exists
        # This ensures video_id, director_pack, etc. from POST are available
        try:
            from app.routers.coaching import _sessions as post_sessions
            post_session_data = post_sessions.get(session_id, {})
            if post_session_data:
                # Merge important fields from POST session
                session["video_id"] = post_session_data.get("video_id") or video_id
                session["outlier_id"] = post_session_data.get("outlier_id") or outlier_id
                session["director_pack"] = post_session_data.get("director_pack")
                session["pattern_id"] = post_session_data.get("pattern_id")
                session["assignment"] = post_session_data.get("assignment", "coached")
                session["holdout_group"] = post_session_data.get("holdout_group", False)
                # H9: 크레딧 관련 필드
                session["user_id"] = post_session_data.get("user_id", "anonymous")
                session["coaching_tier"] = post_session_data.get("coaching_tier", "pro")
                session["effective_tier"] = session["coaching_tier"]  # 초기값
                session["tier_downgraded"] = False
                logger.info(f"Merged POST session data: video_id={session.get('video_id')}, tier={session.get('coaching_tier')}")
            else:
                # Fallback to query parameters
                session["video_id"] = video_id
                session["outlier_id"] = outlier_id
                session["coaching_tier"] = "pro"  # 디폴트 Pro
                session["effective_tier"] = "pro"
                session["tier_downgraded"] = False
                logger.info(f"No POST session found, using query params: video_id={video_id}")
        except ImportError:
            session["video_id"] = video_id
            session["outlier_id"] = outlier_id
        
        # Phase 1: 출력 모드 + 페르소나 저장
        session["output_mode"] = output_mode  # graphic | text | audio | graphic_audio
        session["persona"] = persona  # strict_pd | close_friend | calm_mentor | energetic
        
        # 3. Send initial status
        await manager.send_message(session_id, {
            "type": "session_status",
            "session_id": session_id,
            "status": "connected",
            "language": language,
            "voice_style": voice_style,
            "video_id": video_id,
            "outlier_id": outlier_id,
            # Phase 1: 출력 모드 + 페르소나
            "output_mode": output_mode,
            "persona": persona,
            "timestamp": utcnow().isoformat(),
        })
        
        # 4. Message handling loop
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                
                if msg_type == "control":
                    await handle_control(session_id, session, message)
                
                elif msg_type == "audio":
                    await handle_audio(session_id, session, message)
                
                elif msg_type == "metric":
                    await handle_metric(session_id, session, message, voice_style)
                
                elif msg_type == "video_frame":
                    # P3: 실시간 비디오 프레임 분석
                    await handle_video_frame(session_id, session, message, voice_style)
                
                elif msg_type == "ping":
                    # Phase 2: Include client timestamp for latency measurement
                    await manager.send_message(session_id, {
                        "type": "pong",
                        "client_t": message.get("t"),  # Echo back client timestamp
                        "timestamp": utcnow().isoformat(),
                    })
                
                # Phase 3: 적응형 코칭 - 사용자 피드백 처리
                elif msg_type == "user_feedback":
                    await handle_user_feedback(session_id, session, message)
                
                else:
                    await manager.send_message(session_id, {
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })
                    
            except json.JSONDecodeError:
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": "Invalid JSON",
                })
                
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_message(session_id, {
            "type": "error",
            "message": str(e),
        })
    finally:
        # Cleanup
        session = manager.get_session(session_id)
        if session and session.get("coach"):
            # H1: Cancel response task if running
            response_task = session.get("response_task")
            if response_task and not response_task.done():
                response_task.cancel()
            try:
                await session["coach"].disconnect()
            except:
                pass
        manager.disconnect(session_id)


# ==================
# VDG DIRECTOR PACK LOADING
# ==================

async def load_director_pack_from_video(
    video_id: Optional[str] = None,
    outlier_id: Optional[str] = None,
) -> Optional[Any]:
    """
    비디오/아웃라이어의 VDG 분석에서 DirectorPack 로드
    
    Args:
        video_id: RemixNode.node_id (게시된 카드)
        outlier_id: OutlierItem.id (승격된 아웃라이어)
    
    Returns:
        DirectorPack if found, None otherwise (fallback to proof_pack)
    """
    from app.services.vdg_2pass.director_compiler import compile_director_pack
    from app.schemas.vdg_v4 import VDGv4
    
    try:
        async with AsyncSessionLocal() as db:
            node = None
            
            # 1. video_id로 RemixNode 조회
            if video_id:
                result = await db.execute(
                    select(RemixNode).where(RemixNode.node_id == video_id)
                )
                node = result.scalar_one_or_none()
                
                # Fallback: video_id가 UUID 형식이면 OutlierItem 확인
                if not node:
                    from uuid import UUID
                    try:
                        uuid_val = UUID(video_id)
                        outlier_result = await db.execute(
                            select(OutlierItem).where(OutlierItem.id == uuid_val)
                        )
                        outlier = outlier_result.scalar_one_or_none()
                        
                        if outlier:
                            logger.info(f"🔍 Found OutlierItem: {outlier.id}, promoted={outlier.promoted_to_node_id is not None}")
                            if outlier.promoted_to_node_id:
                                node_result = await db.execute(
                                    select(RemixNode).where(RemixNode.id == outlier.promoted_to_node_id)
                                )
                                node = node_result.scalar_one_or_none()
                            else:
                                # OutlierItem은 있지만 승격되지 않았음 - VDG 없음
                                logger.warning(f"⚠️ OutlierItem {video_id} not promoted, no VDG analysis available")
                    except (ValueError, TypeError):
                        pass  # Not a valid UUID, skip
                
            # 2. outlier_id로 승격된 RemixNode 조회
            elif outlier_id:
                result = await db.execute(
                    select(OutlierItem).where(OutlierItem.id == outlier_id)
                )
                outlier = result.scalar_one_or_none()
                
                if outlier and outlier.promoted_to_node_id:
                    node_result = await db.execute(
                        select(RemixNode).where(RemixNode.id == outlier.promoted_to_node_id)
                    )
                    node = node_result.scalar_one_or_none()
            
            # 3. VDG 분석이 있으면 DirectorPack 컴파일
            logger.info(f"🔍 VDG Load: node={node is not None}, video_id={video_id}")
            
            if node and node.gemini_analysis:
                analysis = node.gemini_analysis
                logger.info(f"🔍 VDG Load: gemini_analysis keys={list(analysis.keys())[:5]}...")
                
                # VDG v4 필수 필드 확인 (flat 또는 nested 구조)
                has_hook = "hook_genome" in analysis or analysis.get("semantic", {}).get("hook_genome")
                has_scenes = "scenes" in analysis or analysis.get("semantic", {}).get("scenes")
                
                if not has_hook and not has_scenes:
                    logger.warning(f"VDG analysis not available for node: {node.node_id}")
                    return None
                
                # Legacy Flat → VDGv4 Nested 변환
                if "semantic" not in analysis:
                    # 기존 flat 데이터를 VDGv4 구조로 변환
                    semantic_fields = ["scenes", "hook_genome", "intent_layer", "asr_transcript", 
                                       "ocr_text", "audience_reaction", "capsule_brief", "commerce"]
                    semantic = {}
                    for field in semantic_fields:
                        if field in analysis:
                            semantic[field] = analysis[field]
                    analysis["semantic"] = semantic
                    logger.info(f"Converted flat VDG to nested structure for: {node.node_id}")
                
                # Fix: visual.analysis_results List → Dict 변환
                if "visual" in analysis and "analysis_results" in analysis.get("visual", {}):
                    ar = analysis["visual"]["analysis_results"]
                    if isinstance(ar, list):
                        # Convert list to dict with ap_id as key
                        analysis["visual"]["analysis_results"] = {
                            item.get("ap_id", f"ap_{i}"): item 
                            for i, item in enumerate(ar)
                        }
                        logger.info(f"Converted analysis_results list→dict for: {node.node_id}")
                
                try:
                    vdg_v4 = VDGv4(
                        content_id=node.node_id,
                        duration_sec=analysis.get("duration_sec", 0),
                        **{k: v for k, v in analysis.items()
                           if k not in ["content_id", "duration_sec"]}
                    )
                    
                    pack = compile_director_pack(vdg_v4)
                    logger.info(f"DirectorPack loaded from VDG: {node.node_id}, {len(pack.dna_invariants)} rules")
                    return pack
                except Exception as compile_err:
                    logger.warning(f"DirectorPack compile failed: {compile_err}")
                    import traceback
                    logger.debug(f"Compile error details: {traceback.format_exc()}")
                    return None
                
    except Exception as e:
        logger.error(f"Failed to load DirectorPack from video: {e}")
    
    return None


# ==================
# H4: GEMINI RECONNECT HELPER
# ==================

async def try_reconnect_gemini(session_id: str, session: dict) -> bool:
    """
    H4: Gemini 연결 실패 시 재연결 시도
    
    Returns True if reconnected, False if all attempts failed.
    """
    coach: AudioCoach = session["coach"]
    
    for attempt in range(GEMINI_RECONNECT_MAX_ATTEMPTS):
        try:
            session["gemini_reconnect_attempts"] = attempt + 1
            logger.info(f"Gemini reconnect attempt {attempt + 1}/{GEMINI_RECONNECT_MAX_ATTEMPTS}: {session_id}")
            
            await coach.connect()
            session["gemini_connected"] = True
            session["gemini_reconnect_attempts"] = 0
            
            # H9: 재연결 성공 시 tier 복원
            if session.get("tier_downgraded"):
                session["effective_tier"] = session.get("coaching_tier", "pro")
                session["tier_downgraded"] = False
                logger.info(f"H9: Tier restored to {session['effective_tier']}: {session_id}")
            
            # Restart response loop
            if session.get("response_task") and not session["response_task"].done():
                session["response_task"].cancel()
            
            session["response_task"] = asyncio.create_task(
                run_audio_response_loop(session_id, session)
            )
            
            await manager.send_message(session_id, {
                "type": "session_status",
                "status": "reconnected",
                "gemini_connected": True,
                # H9: tier 정보
                "effective_tier": session.get("effective_tier", "pro"),
                "tier_downgraded": False,
                "timestamp": utcnow().isoformat(),
            })
            
            logger.info(f"Gemini reconnected successfully: {session_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Gemini reconnect failed ({attempt + 1}): {e}")
            if attempt < GEMINI_RECONNECT_MAX_ATTEMPTS - 1:
                await asyncio.sleep(GEMINI_RECONNECT_DELAY_SEC * (attempt + 1))
    
    # All attempts failed
    session["gemini_connected"] = False
    await manager.send_message(session_id, {
        "type": "session_status",
        "status": "recording",
        "gemini_connected": False,
        "fallback_mode": True,
        "message": "Gemini 연결 실패, 로컬 모드로 전환",
        "timestamp": utcnow().isoformat(),
    })
    return False


# ==================
# H7: SESSION TIMEOUT MONITOR
# ==================

async def run_session_timeout_monitor(session_id: str, session: dict):
    """
    H7: 세션 타임아웃 모니터
    
    5분간 활동이 없으면 자동으로 세션 종료
    """
    try:
        while session.get("status") in ("idle", "recording", "paused"):
            await asyncio.sleep(SESSION_TIMEOUT_CHECK_INTERVAL)
            
            last_activity = session.get("last_activity")
            if not last_activity:
                continue
            
            elapsed = (utcnow() - last_activity).total_seconds()
            
            if elapsed > SESSION_TIMEOUT_SEC:
                logger.warning(f"Session timeout ({elapsed:.0f}s): {session_id}")
                
                # Clean up
                session["status"] = "timeout"
                
                response_task = session.get("response_task")
                if response_task and not response_task.done():
                    response_task.cancel()
                
                coach = session.get("coach")
                if coach:
                    try:
                        await coach.disconnect()
                    except:
                        pass
                
                await manager.send_message(session_id, {
                    "type": "session_status",
                    "status": "timeout",
                    "message": f"세션 타임아웃 ({SESSION_TIMEOUT_SEC // 60}분 비활성)",
                    "timestamp": utcnow().isoformat(),
                })
                break
                
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Timeout monitor error: {e}")


# ==================
# CHECKPOINT EVALUATION LOOP
# ==================

# Checkpoint evaluation interval
CHECKPOINT_EVAL_INTERVAL_SEC = 1.0


async def run_checkpoint_evaluation_loop(session_id: str, session: dict):
    """
    시간 기반 체크포인트 평가 루프
    
    녹화 시간에 따라 get_next_command()를 호출하고 TTS 피드백 전송
    
    Flow:
    1. 매 1초마다 현재 녹화 시간 계산
    2. coach.get_next_command(current_time) 호출
    3. 명령이 있으면 TTS 생성 후 전송
    """
    logger.info(f"Checkpoint evaluation loop started: {session_id}")
    
    try:
        while session.get("status") == "recording":
            await asyncio.sleep(CHECKPOINT_EVAL_INTERVAL_SEC)
            
            # Skip if paused
            if session.get("status") != "recording":
                continue
            
            # Get current recording time
            current_time = session.get("recording_time", 0.0)
            
            # Get coaching command
            coach: AudioCoach = session.get("coach")
            if not coach:
                continue
            
            command = coach.get_next_command(current_time)
            
            if command:
                logger.info(f"⏱️ Checkpoint coaching @ {current_time:.1f}s: {command[:40]}...")
                
                # Update session stats
                session["interventions_sent"] = session.get("interventions_sent", 0) + 1
                
                # Generate TTS and send feedback
                audio_b64 = await generate_tts_fallback(command, lang="ko")
                
                await manager.send_message(session_id, {
                    "type": "feedback",
                    "message": command,
                    "audio_b64": audio_b64,  # May be None if TTS failed
                    "audio_format": "mp3" if audio_b64 else None,
                    "checkpoint_time": current_time,
                    "timestamp": utcnow().isoformat(),
                })
                
    except asyncio.CancelledError:
        logger.info(f"Checkpoint evaluation loop cancelled: {session_id}")
    except Exception as e:
        logger.error(f"Checkpoint evaluation loop error: {e}")
    finally:
        logger.info(f"Checkpoint evaluation loop ended: {session_id}")


# ==================
# H8: AUDIO SEND WITH RETRY
# ==================

async def send_audio_with_retry(session_id: str, session: dict, pcm_data: bytes) -> bool:
    """
    H8: 오디오 전송 + 재시도 로직
    
    Returns True if sent successfully, False otherwise.
    """
    coach: AudioCoach = session["coach"]
    
    for attempt in range(AUDIO_SEND_MAX_RETRIES):
        try:
            await coach.send_audio(pcm_data)
            session["audio_errors_count"] = 0  # Reset on success
            return True
            
        except RuntimeError as e:
            # Session not connected
            logger.warning(f"Audio send failed (not connected): {e}")
            
            if session.get("gemini_connected"):
                session["gemini_connected"] = False
                # Try to reconnect
                if await try_reconnect_gemini(session_id, session):
                    continue  # Retry send after reconnect
            
            break  # Don't retry if not connected
            
        except Exception as e:
            session["audio_errors_count"] = session.get("audio_errors_count", 0) + 1
            logger.warning(f"Audio send error ({attempt + 1}/{AUDIO_SEND_MAX_RETRIES}): {e}")
            
            if attempt < AUDIO_SEND_MAX_RETRIES - 1:
                await asyncio.sleep(AUDIO_SEND_RETRY_DELAY_SEC)
    
    # All retries failed
    if session["audio_errors_count"] > 10:
        logger.error(f"Too many audio errors, consider fallback: {session_id}")
        
    return False


# ==================
# Phase 3: USER FEEDBACK HANDLER (적응형 코칭)
# ==================

async def handle_user_feedback(session_id: str, session: dict, message: dict):
    """
    Phase 3: 사용자 피드백 처리 - 적응형 코칭
    
    사용자가 "못해요" / "대신 이건 어때요?" 등의 피드백을 보내면
    DNAInvariant를 검증하여 허용/거절 + 대안 제시
    """
    feedback_text = message.get("text", "")
    if not feedback_text:
        await manager.send_message(session_id, {
            "type": "adaptive_response",
            "error": "피드백 텍스트가 비어있습니다.",
            "timestamp": utcnow().isoformat(),
        })
        return
    
    coach: AudioCoach = session.get("coach")
    if not coach or not coach._director_pack:
        # DirectorPack 없으면 모든 피드백 허용
        await manager.send_message(session_id, {
            "type": "adaptive_response",
            "accepted": True,
            "message": "네, 그렇게 해볼까요!",
            "timestamp": utcnow().isoformat(),
        })
        return
    
    try:
        from app.services.adaptive_coaching import AdaptiveCoachingService
        
        # AdaptiveCoachingService 생성/재사용 (LLM 클라이언트 연동)
        if "adaptive_service" not in session:
            # Gemini 클라이언트 가져오기 (코칭 세션용)
            llm_client = None
            try:
                import google.generativeai as genai
                llm_client = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                logger.warning(f"Gemini client not available, using fallback: {e}")
            
            session["adaptive_service"] = AdaptiveCoachingService(
                director_pack=coach._director_pack,
                llm_client=llm_client,
                use_llm=llm_client is not None,
            )
        
        adaptive_service: AdaptiveCoachingService = session["adaptive_service"]
        
        # 피드백 처리 (LLM 비동기 호출)
        response = await adaptive_service.process_feedback(feedback_text)
        
        # 응답 전송
        response_data = {
            "type": "adaptive_response",
            "accepted": response.accepted,
            "message": response.message,
            "timestamp": utcnow().isoformat(),
        }
        
        if response.alternative:
            response_data["alternative"] = response.alternative
        if response.affected_rule_id:
            response_data["affected_rule_id"] = response.affected_rule_id
        if response.reason:
            response_data["reason"] = response.reason
        if response.coaching_adjustment:
            response_data["coaching_adjustment"] = response.coaching_adjustment
        
        await manager.send_message(session_id, response_data)
        
        # 출력 모드에 따라 추가 피드백
        output_mode = session.get("output_mode", "graphic")
        persona = session.get("persona", "calm_mentor")
        
        if not response.accepted and output_mode in ["audio", "graphic_audio"]:
            # 거절 시 대안도 음성으로 안내
            full_message = response.message
            if response.alternative:
                full_message += f" {response.alternative}"
            
            await send_coaching_feedback(
                session_id=session_id,
                session=session,
                rule_id=response.affected_rule_id or "adaptive",
                domain="adaptive",
                priority="high",
                message=full_message,
            )
        
        # Phase 5: A→B Migration - 적응형 코칭 결과 세션에 저장
        if "adaptive_outcomes" not in session:
            session["adaptive_outcomes"] = []
        
        session["adaptive_outcomes"].append({
            "accepted": response.accepted,
            "domain": feedback.affected_domain,
            "proposed_change": feedback.proposed_change,
            "rule_id": response.affected_rule_id,
            "timestamp": utcnow().isoformat(),
        })
        
        logger.info(f"🎯 Adaptive coaching: {session_id} accepted={response.accepted}")
        
    except Exception as e:
        logger.error(f"Adaptive coaching error: {e}")
        await manager.send_message(session_id, {
            "type": "adaptive_response",
            "error": str(e),
            "timestamp": utcnow().isoformat(),
        })


# ==================
# Phase 5+: ADVANCED AUTO-LEARNING
# ==================

async def track_session_outcomes(session_id: str, session: dict):
    """
    Phase 5+: 세션 종료 시 고급 자동학습 시스템 실행
    
    1. CoachingIntervention/Outcome 기록 (metric_before/after)
    2. WeightedSignal 업데이트 (3-Axis)
    3. Canary 그룹 성과 비교
    4. Negative Evidence 탐지
    5. 자동 승격 체크
    """
    try:
        from app.services.advanced_analyzer import get_advanced_analyzer
        from app.services.evidence_updater import get_signal_tracker
        
        analyzer = get_advanced_analyzer()
        base_tracker = get_signal_tracker()
        
        video_id = session.get("video_id", "unknown")
        coach: AudioCoach = session.get("coach")
        persona = session.get("persona", "chill_guide")
        cluster_id = session.get("cluster_id")  # 클러스터 다양성 추적
        
        # 세션 할당 결정 (coached vs control)
        assignment = analyzer.get_assignment(session_id)
        session["assignment"] = assignment
        
        # 1. 코칭 개입 결과 기록 (CoachingIntervention + Outcome)
        coaching_log = session.get("coaching_log", [])
        
        for entry in coaching_log:
            # Record intervention
            intervention = analyzer.record_intervention(
                session_id=session_id,
                rule_id=entry.get("rule_id", "unknown"),
                domain=entry.get("domain", "unknown"),
                priority=entry.get("priority", "medium"),
                message=entry.get("message", ""),
                t_sec=entry.get("t_sec", 0),
                metric_id=entry.get("metric_id"),
                metric_before=entry.get("metric_before"),
                assignment=assignment,
                persona=persona,
            )
            
            # Record outcome
            analyzer.record_outcome(
                intervention_id=intervention.intervention_id,
                user_response=entry.get("user_response", "unknown"),
                compliance_detected=entry.get("compliance", False),
                metric_after=entry.get("metric_after"),
                metric_before=entry.get("metric_before"),
                is_negative_evidence=entry.get("is_negative", False),
                negative_reason=entry.get("negative_reason"),
                cluster_id=cluster_id,
                persona=persona,
            )
        
        # 2. DNAInvariant 준수 결과 기록 (기존 로직 유지)
        if coach and coach._director_pack:
            violation_log = getattr(coach, '_violation_log', [])
            
            for invariant in coach._director_pack.dna_invariants:
                domain = invariant.domain
                rule_id = invariant.rule_id
                was_violated = any(rule_id in str(v) for v in violation_log)
                
                base_tracker.track_outcome(
                    element=domain,
                    value=rule_id.split("_")[-1] if "_" in rule_id else rule_id,
                    success=not was_violated,
                    content_id=video_id,
                    sentiment="positive" if invariant.priority in ["critical", "high"] else "neutral",
                )
        
        # 3. 적응형 코칭 결과 기록
        adaptive_outcomes = session.get("adaptive_outcomes", [])
        for outcome in adaptive_outcomes:
            base_tracker.track_outcome(
                element=outcome.get("domain", "adaptive"),
                value=outcome.get("proposed_change", "alternative")[:20] if outcome.get("proposed_change") else "accepted",
                success=outcome.get("accepted", True),
                content_id=video_id,
            )
        
        # 4. 3-Axis 메트릭 계산
        axis_metrics = analyzer.calculate_axis_metrics()
        
        # 5. 자동 승격 체크
        promotion_ready = analyzer.check_promotions()
        base_candidates = base_tracker.check_promotions()
        
        all_promotions = len(promotion_ready) + len(base_candidates)
        
        if all_promotions > 0:
            logger.info(f"🎉 {all_promotions} signals ready for promotion!")
            
            # 승격 알림 전송
            await manager.send_message(session_id, {
                "type": "signal_promotion",
                "new_candidates": all_promotions,
                "axis_metrics": {
                    "compliance_lift": f"{axis_metrics.compliance_lift:.1%}",
                    "outcome_lift": f"{axis_metrics.outcome_lift:.1%}",
                    "cluster_count": axis_metrics.cluster_count,
                    "persona_count": axis_metrics.persona_count,
                    "negative_rate": f"{axis_metrics.negative_evidence_rate:.1%}",
                    "is_ready": axis_metrics.is_promotion_ready,
                },
                "failing_axes": axis_metrics.failing_axes,
                "candidates": [
                    {"signal_key": sk, "metrics": m.__dict__}
                    for sk, m in promotion_ready
                ],
                "timestamp": utcnow().isoformat(),
            })
        
        # 통계 세션에 저장
        stats = analyzer.get_stats()
        session["tracking_stats"] = {
            "signals_tracked": stats["signals_tracked"],
            "outcomes_recorded": stats["outcomes_recorded"],
            "promotion_ready": stats["promotion_ready"],
            "axis_metrics": axis_metrics.__dict__,
            "assignment": assignment,
        }
        
        logger.info(
            f"📊 Advanced session analysis: {session_id}, "
            f"signals={stats['signals_tracked']}, "
            f"compliance_lift={axis_metrics.compliance_lift:.1%}, "
            f"ready={axis_metrics.is_promotion_ready}"
        )
        
    except Exception as e:
        logger.warning(f"Failed to track session outcomes: {e}")
        import traceback
        logger.debug(traceback.format_exc())


# ==================
# H2: TTS FALLBACK UTILITIES
# ==================

# Phase 4: 페르소나별 TTS 속도 설정 (힙한 네이밍)
PERSONA_TTS_CONFIG = {
    "drill_sergeant": {"slow": False, "speed_multiplier": 1.2},  # 빡센 디렉터
    "bestie": {"slow": False, "speed_multiplier": 1.0},  # 찐친
    "chill_guide": {"slow": True, "speed_multiplier": 0.9},  # 릴렉스 가이드 (디폴트)
    "hype_coach": {"slow": False, "speed_multiplier": 1.1},  # 하이퍼 부스터
}


async def generate_tts_fallback(
    text: str,
    lang: str = "ko",
    persona: str = "calm_mentor",  # Phase 4: 페르소나 파라미터
) -> Optional[str]:
    """
    H2: TTS Fallback using gTTS (Google Text-to-Speech)
    
    Phase 4: 페르소나별 음성 톤 지원
    - strict_pd: 빠르고 단호
    - close_friend: 자연스러운 속도
    - calm_mentor: 차분하고 여유 (디폴트)
    - energetic: 활기찬 톤
    
    Returns base64-encoded MP3 audio, or None if failed.
    Frontend will use Web Speech API if None.
    """
    if not text or len(text) < 2:
        return None
    
    # Phase 4: 페르소나별 TTS 설정
    persona_config = PERSONA_TTS_CONFIG.get(persona, PERSONA_TTS_CONFIG["calm_mentor"])
    slow = persona_config.get("slow", False)
    
    try:
        # Try gTTS (free, no API key)
        from gtts import gTTS
        import io
        
        tts = gTTS(text=text, lang=lang, slow=slow)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        audio_b64 = base64.b64encode(audio_buffer.read()).decode()
        logger.debug(f"TTS generated ({persona}): {len(text)} chars -> {len(audio_b64)} bytes")
        return audio_b64
        
    except ImportError:
        logger.warning("gTTS not installed, falling back to Web Speech API on client")
        return None
    except Exception as e:
        logger.warning(f"gTTS failed: {e}")
        return None


# ==================
# Phase 1: GRAPHIC GUIDE GENERATION
# ==================

def generate_graphic_guide(
    rule_id: str,
    domain: str,
    priority: str,
    message: str,
    target_position: Optional[list] = None,
) -> dict:
    """
    Phase 1: 그래픽 코칭 가이드 생성
    
    DNAInvariant → GraphicGuide 변환
    """
    # 도메인별 가이드 타입 결정
    if domain == "composition":
        guide_type = "composition"
        grid_type = "center"
        arrow_direction = None
        
        # 타겟 위치 기반 화살표 방향 결정
        if target_position:
            dx = 0.5 - target_position[0]
            dy = 0.5 - target_position[1]
            if abs(dx) > abs(dy):
                arrow_direction = "right" if dx > 0 else "left"
            else:
                arrow_direction = "down" if dy > 0 else "up"
                
    elif domain == "timing":
        guide_type = "timing"
        grid_type = None
        arrow_direction = None
        
    else:
        guide_type = "action"
        grid_type = None
        arrow_direction = None
    
    # 액션 아이콘 결정
    action_icon = None
    if "중앙" in message or "center" in message.lower():
        action_icon = "look_camera"
    elif "빨리" in message or "fast" in message.lower():
        action_icon = "action_now"
    elif "유지" in message or "hold" in message.lower():
        action_icon = "hold"
    
    return {
        "type": "graphic_guide",
        "guide_type": guide_type,
        "rule_id": rule_id,
        "priority": priority,
        "target_position": target_position or [0.5, 0.5],
        "grid_type": grid_type,
        "arrow_direction": arrow_direction,
        "action_icon": action_icon,
        "message": message,
        "message_duration_ms": 3000 if priority == "critical" else 2000,
        "timestamp": utcnow().isoformat(),
    }


async def send_coaching_feedback(
    session_id: str,
    session: dict,
    rule_id: str,
    domain: str,
    priority: str,
    message: str,
    target_position: Optional[list] = None,
):
    """
    Phase 1: 출력 모드에 따른 코칭 피드백 전송
    
    - graphic: GraphicGuide JSON 전송
    - text: TextCoach JSON 전송
    - audio: TTS 오디오 전송
    - graphic_audio: 둘 다 전송
    """
    output_mode = session.get("output_mode", "graphic")
    persona = session.get("persona", "calm_mentor")
    
    if output_mode in ["graphic", "graphic_audio"]:
        # 그래픽 가이드 전송
        guide = generate_graphic_guide(
            rule_id=rule_id,
            domain=domain,
            priority=priority,
            message=message,
            target_position=target_position,
        )
        await manager.send_message(session_id, guide)
    
    if output_mode == "text":
        # 텍스트 코칭 전송
        await manager.send_message(session_id, {
            "type": "text_coach",
            "message": message,
            "priority": priority,
            "persona": persona,
            "duration_ms": 3000 if priority == "critical" else 2000,
            "timestamp": utcnow().isoformat(),
        })
    
    if output_mode in ["audio", "graphic_audio"]:
        # TTS 오디오 전송 (Phase 4: 페르소나별 톤)
        audio_b64 = await generate_tts_fallback(message, persona=persona)
        await manager.send_message(session_id, {
            "type": "audio_feedback",
            "text": message,
            "audio": audio_b64,
            "persona": persona,  # Phase 4: 페르소나 정보 전달
            "source": "gtts_fallback",
            "timestamp": utcnow().isoformat(),
        })


# ==================
# H1: GEMINI AUDIO RESPONSE LOOP
# ==================

async def run_audio_response_loop(session_id: str, session: dict):
    """
    H1: Gemini Live 오디오 응답 수신 백그라운드 루프
    
    Gemini가 음성 응답을 생성하면 클라이언트로 스트리밍
    """
    coach: AudioCoach = session["coach"]
    
    if not coach._session:
        logger.warning(f"No Gemini session for audio response loop: {session_id}")
        return
    
    try:
        while session.get("status") == "recording":
            try:
                # Receive from Gemini Live
                turn = coach._session.receive()
                async for response in turn:
                    if session.get("status") != "recording":
                        break
                    
                    # Extract audio from server response
                    if response.server_content and response.server_content.model_turn:
                        for part in response.server_content.model_turn.parts:
                            if part.inline_data and isinstance(part.inline_data.data, bytes):
                                audio_data = part.inline_data.data
                                audio_b64 = base64.b64encode(audio_data).decode()
                                
                                # Send to client
                                await manager.send_message(session_id, {
                                    "type": "audio_response",
                                    "audio_b64": audio_b64,
                                    "format": "pcm_24khz",  # Gemini outputs 24kHz PCM
                                    "size_bytes": len(audio_data),
                                    "timestamp": utcnow().isoformat(),
                                })
                                
                                session["audio_responses_sent"] = session.get("audio_responses_sent", 0) + 1
                                
                            # Extract text if present
                            if hasattr(part, 'text') and part.text:
                                await manager.send_message(session_id, {
                                    "type": "feedback",
                                    "message": part.text,
                                    "timestamp": utcnow().isoformat(),
                                })
                    
                    # Check for turn end
                    if response.server_content and response.server_content.turn_complete:
                        logger.debug(f"Gemini turn complete: {session_id}")
                        
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"Audio response loop iteration error: {e}")
                await asyncio.sleep(0.1)  # Brief pause before retry
                
    except asyncio.CancelledError:
        logger.info(f"Audio response loop cancelled: {session_id}")
    except Exception as e:
        logger.error(f"Audio response loop fatal error: {e}")
    finally:
        logger.info(f"Audio response loop ended: {session_id}")


# ==================
# MESSAGE HANDLERS
# ==================

async def handle_control(session_id: str, session: dict, message: dict):
    """Control 메시지 처리 (start/pause/stop)"""
    action = message.get("action")
    
    if action == "start":
        session["status"] = "recording"
        session["recording_started_at"] = utcnow()
        
        coach: AudioCoach = session["coach"]
        voice_style = session.get("voice_style", "friendly")
        
        # DirectorPack 로드: 세션에 저장된 pack 우선, 없으면 VDG/fallback
        pack = None
        video_id = session.get("video_id")
        outlier_id = session.get("outlier_id")
        
        try:
            # 0. 세션에 이미 저장된 DirectorPack 사용 (POST에서 로드됨)
            stored_pack_data = session.get("director_pack")
            if stored_pack_data:
                from app.schemas.director_pack import DirectorPack
                pack = DirectorPack(**stored_pack_data)
                
                # Fallback 규칙 감지: rule_id가 "fallback_"로 시작하면 VDG에서 다시 로드
                has_fallback_rules = any(
                    r.rule_id.startswith("fallback_") for r in pack.dna_invariants
                )
                if has_fallback_rules and (video_id or outlier_id):
                    logger.info(f"Stored pack has fallback rules, reloading from VDG...")
                    pack = None  # VDG에서 다시 로드하도록 설정
                else:
                    logger.info(f"Using stored DirectorPack from session: {pack.pattern_id}, {len(pack.dna_invariants)} rules")
            
            # 1. 저장된 pack 없거나 fallback이면 VDG에서 로드
            if pack is None and (video_id or outlier_id):
                pack = await load_director_pack_from_video(
                    video_id=video_id,
                    outlier_id=outlier_id,
                )
                if pack:
                    logger.info(f"Loaded DirectorPack from VDG: {pack.pattern_id}, {len(pack.dna_invariants)} rules")
            
            # 2. VDG 없으면 기본 proof patterns 사용 (fallback)
            if pack is None:
                pack = create_proof_pack()
                logger.info(f"Using fallback proof_pack: {len(pack.dna_invariants)} rules")
            
            # 3. AudioCoach에 컨텍스트 설정
            coach.set_coaching_context(pack, tone=voice_style)
            logger.info(f"DirectorPack applied: {len(pack.dna_invariants)} rules, video_id={video_id}")
            
        except Exception as e:
            logger.warning(f"DirectorPack load failed: {e}")
        
        # Gemini Live 연결 시도
        gemini_connected = False
        try:
            await coach.connect()
            gemini_connected = True
            session["gemini_connected"] = True  # H4: Track connection state
            logger.info(f"Gemini Live connected: {session_id}")
            
            # H1: 백그라운드 응답 수신 루프 시작
            response_task = asyncio.create_task(
                run_audio_response_loop(session_id, session)
            )
            session["response_task"] = response_task
            
        except Exception as e:
            session["gemini_connected"] = False
            # H9: Pro 모드인데 Gemini 실패 시 Basic으로 다운그레이드 (비용 절감)
            if session.get("coaching_tier") == "pro":
                session["effective_tier"] = "basic"
                session["tier_downgraded"] = True
                logger.warning(f"H9: Gemini failed, tier downgraded to basic: {session_id}")
            logger.warning(f"Gemini Live connection failed, using fallback: {e}")
        
        # H7: 세션 타임아웃 모니터 시작
        timeout_task = asyncio.create_task(
            run_session_timeout_monitor(session_id, session)
        )
        session["timeout_task"] = timeout_task
        
        # 시간 기반 체크포인트 평가 루프 시작
        checkpoint_task = asyncio.create_task(
            run_checkpoint_evaluation_loop(session_id, session)
        )
        session["checkpoint_task"] = checkpoint_task
        
        await manager.send_message(session_id, {
            "type": "session_status",
            "status": "recording",
            "gemini_connected": gemini_connected,
            "fallback_mode": not gemini_connected,
            # H9: 크레딧 관련 정보
            "coaching_tier": session.get("coaching_tier", "pro"),
            "effective_tier": session.get("effective_tier", "pro"),
            "tier_downgraded": session.get("tier_downgraded", False),
            "rules_count": len(coach._director_pack.dna_invariants) if coach._director_pack else 0,
            "checkpoint_evaluation": True,  # Indicate checkpoint loop is active
            # Phase 1: 출력 모드 + 페르소나
            "output_mode": session.get("output_mode", "graphic"),
            "persona": session.get("persona", "calm_mentor"),
            "timestamp": utcnow().isoformat(),
        })
        
        # Phase 2.5: VDG 데이터 전송 (shotlist, kicks, mise_en_scene)
        if coach._director_pack:
            extensions = getattr(coach._director_pack, 'extensions', None)
            if extensions and "phase2_vdg_data" in extensions:
                phase2_data = extensions["phase2_vdg_data"]
                await manager.send_message(session_id, {
                    "type": "vdg_coaching_data",
                    "shotlist_sequence": phase2_data.get("shotlist_sequence", []),
                    "kick_timings": phase2_data.get("kick_timings", []),
                    "mise_en_scene_guides": phase2_data.get("mise_en_scene_guides", []),
                    "timestamp": utcnow().isoformat(),
                })
                logger.info(f"📋 Phase 2 VDG data sent: shots={len(phase2_data.get('shotlist_sequence', []))}, kicks={len(phase2_data.get('kick_timings', []))}")
        
        logger.info(f"Recording started: {session_id}, gemini={gemini_connected}, checkpoints=active")
    
    elif action == "pause":
        session["status"] = "paused"
        await manager.send_message(session_id, {
            "type": "session_status",
            "status": "paused",
            "timestamp": utcnow().isoformat(),
        })
    
    elif action == "stop":
        session["status"] = "ended"
        
        # H1: 응답 수신 루프 정리
        response_task = session.get("response_task")
        if response_task and not response_task.done():
            response_task.cancel()
            try:
                await response_task
            except asyncio.CancelledError:
                pass
            logger.info(f"Audio response loop stopped: {session_id}")
        
        # H7: 타임아웃 모니터 정리
        timeout_task = session.get("timeout_task")
        if timeout_task and not timeout_task.done():
            timeout_task.cancel()
        
        # 체크포인트 평가 루프 정리
        checkpoint_task = session.get("checkpoint_task")
        if checkpoint_task and not checkpoint_task.done():
            checkpoint_task.cancel()
        
        # =========================================
        # Phase 5: A→B Migration - 코칭 결과 학습
        # =========================================
        await track_session_outcomes(session_id, session)
        
        # 세션 통계 계산
        stats = {
            "total_time": session.get("recording_time", 0),
            "rules_evaluated": session.get("rules_evaluated", 0),
            "interventions_sent": session.get("interventions_sent", 0),
            "ended_at": utcnow().isoformat(),
        }
        
        # Coach 통계 추가
        coach: AudioCoach = session["coach"]
        coach_stats = coach.get_session_stats()
        stats.update(coach_stats)
        
        await manager.send_message(session_id, {
            "type": "session_status",
            "status": "ended",
            "stats": stats,
            "timestamp": utcnow().isoformat(),
        })
        
        logger.info(f"Recording ended: {session_id}, stats={stats}")


async def handle_audio(session_id: str, session: dict, message: dict):
    """Audio 청크 처리 (H7: 활동 추적, H8: 재시도 로직)"""
    if session.get("status") != "recording":
        return
    
    audio_b64 = message.get("data")
    if not audio_b64:
        return
    
    # H7: Update last activity
    session["last_activity"] = utcnow()
    
    try:
        # Base64 → PCM bytes
        pcm_data = base64.b64decode(audio_b64)
        
        # H8: AudioCoach에 전달 (재시도 로직 포함)
        if session.get("gemini_connected"):
            await send_audio_with_retry(session_id, session, pcm_data)
        # Note: If not connected, audio is still tracked but not sent
        
        # 녹화 시간 업데이트 (16kHz, 16-bit mono 기준)
        duration_sec = len(pcm_data) / (16000 * 2)
        session["recording_time"] = session.get("recording_time", 0) + duration_sec
        
    except Exception as e:
        logger.error(f"Audio processing error: {e}")


async def handle_metric(session_id: str, session: dict, message: dict, voice_style: str):
    """
    Metric 메시지 처리 (프론트엔드에서 측정한 값)
    
    이 메시지는 프론트엔드가 비전 분석 등으로 측정한 메트릭을 전달할 때 사용
    예: 카메라 중앙 여부, 얼굴 감지 등
    """
    rule_id = message.get("rule_id")
    metric_value = message.get("value")
    t_sec = message.get("t_sec", session.get("recording_time", 0))
    
    if not rule_id or metric_value is None:
        return
    
    session["rules_evaluated"] = session.get("rules_evaluated", 0) + 1
    
    # AudioCoach에서 다음 명령 조회
    coach: AudioCoach = session["coach"]
    command = coach.get_next_command(t_sec)
    
    if command:
        session["interventions_sent"] = session.get("interventions_sent", 0) + 1
        
        # H2: TTS 생성 (Gemini not available -> use fallback)
        audio_b64 = None
        command_text = command.get("text") if isinstance(command, dict) else str(command)
        
        try:
            audio_b64 = await generate_tts_fallback(command_text)
        except Exception as e:
            logger.warning(f"TTS generation failed: {e}")
        
        await manager.send_message(session_id, {
            "type": "feedback",
            "rule_id": command.get("rule_id"),
            "message": command.get("text"),
            "priority": command.get("priority"),
            "audio_b64": audio_b64,  # None이면 프론트엔드에서 Web Speech API 사용
            "t_sec": t_sec,
            "timestamp": utcnow().isoformat(),
        })
        
        # 규칙 상태 업데이트
        await manager.send_message(session_id, {
            "type": "rule_update",
            "rule_id": rule_id,
            "status": "pending",  # 코칭 후 대기
            "t_sec": t_sec,
        })
        
        logger.info(f"Feedback sent: {session_id}, rule={rule_id}, msg={command.get('text')[:30]}...")
    
    else:
        # 위반 없음 - 통과 처리
        await manager.send_message(session_id, {
            "type": "rule_update",
            "rule_id": rule_id,
            "status": "passed",
            "t_sec": t_sec,
        })


# ==================
# P3: VIDEO FRAME ANALYSIS
# ==================

async def handle_video_frame(session_id: str, session: dict, message: dict, voice_style: str):
    """
    P3: 실시간 비디오 프레임 분석
    
    프론트엔드에서 1fps로 전송되는 프레임을 분석하여
    DNAInvariant 규칙 준수 여부를 실시간으로 평가하고 피드백을 제공합니다.
    
    Message format:
        {
            "type": "video_frame",
            "frame_b64": "base64_encoded_jpeg",
            "t_sec": 2.5
        }
    """
    from app.services.frame_analyzer import get_frame_analyzer
    
    frame_b64 = message.get("frame_b64")
    t_sec = message.get("t_sec", 0.0)
    t_ms = message.get("t_ms")  # Phase 2: Client timestamp for latency tracking
    codec = message.get("codec", "jpeg")  # Phase 2: H.264 or JPEG
    quality_hint = message.get("quality_hint")  # Phase 2: low/medium/high
    
    if not frame_b64:
        await manager.send_message(session_id, {
            "type": "error",
            "message": "frame_b64 is required",
        })
        return
    
    session["frames_received"] = session.get("frames_received", 0) + 1
    
    # Phase 2: Send frame_ack for latency measurement
    if t_ms:
        await manager.send_message(session_id, {
            "type": "frame_ack",
            "frame_t": t_ms,
            "codec": codec,
            "timestamp": utcnow().isoformat(),
        })
    
    # AudioCoach에서 현재 활성 규칙 가져오기
    coach: AudioCoach = session["coach"]
    pack = coach._director_pack  # Fixed: correct attribute name
    
    if not pack or not hasattr(pack, 'dna_invariants'):
        logger.debug("No DirectorPack available for frame analysis")
        return
    
    # 현재 시간에 활성화된 규칙만 추출
    active_rules = []
    for rule in pack.dna_invariants:
        t_window = rule.time_scope.t_window if rule.time_scope else [0, 999]
        if t_window[0] <= t_sec <= t_window[1]:
            active_rules.append(rule)
    
    if not active_rules:
        return
    
    # FrameAnalyzer로 프레임 분석
    try:
        analyzer = get_frame_analyzer()
        results = await analyzer.analyze_frame(
            frame_base64=frame_b64,
            rules=active_rules,
            current_time=t_sec
        )
        
        # 위반 규칙이 있으면 피드백 전송
        for rule_id, result in results.items():
            if not result.is_compliant:
                # 해당 규칙 찾기
                rule = next((r for r in active_rules if r.rule_id == rule_id), None)
                if not rule:
                    continue
                
                # 중복 방지 (4초 cooldown)
                import time
                now = time.time()
                if now - coach._last_command_time < coach._cooldown_sec:
                    continue
                coach._last_command_time = now
                
                # 피드백 메시지 생성
                feedback_msg = result.message or coach._format_command(rule)
                
                # TTS 생성
                audio_b64 = None
                try:
                    audio_b64 = await generate_tts_fallback(feedback_msg)
                except Exception as e:
                    logger.warning(f"TTS generation failed: {e}")
                
                # 피드백 전송
                await manager.send_message(session_id, {
                    "type": "feedback",
                    "source": "video_analysis",
                    "rule_id": rule_id,
                    "message": feedback_msg,
                    "priority": rule.priority,
                    "confidence": result.confidence,
                    "measured_value": result.measured_value,
                    "audio_b64": audio_b64,
                    "t_sec": t_sec,
                    "timestamp": utcnow().isoformat(),
                })
                
                # 위반 기록
                coach.report_violation(rule_id, t_sec, severity="warning")
                session["interventions_sent"] = session.get("interventions_sent", 0) + 1
                
                logger.info(f"Video analysis feedback: {session_id}, rule={rule_id}, conf={result.confidence:.2f}")
                
                # One-command policy: 한 번에 하나만
                break
                
    except Exception as e:
        logger.error(f"Frame analysis failed: {e}")


# ==================
# UTILITY ENDPOINTS
# ==================

@router.get("/coaching/ws/health")
async def coaching_ws_health():
    """WebSocket 상태 확인"""
    return {
        "status": "ok",
        "active_sessions": len(manager.active_sessions),
        "connected_websockets": len(manager.websockets),
        "timestamp": utcnow().isoformat(),
    }


@router.get("/coaching/ws/sessions")
async def list_ws_sessions():
    """활성 WebSocket 세션 목록"""
    sessions = []
    for sid, session in manager.active_sessions.items():
        sessions.append({
            "session_id": sid,
            "status": session.get("status"),
            "recording_time": session.get("recording_time", 0),
            "started_at": session.get("started_at").isoformat() if session.get("started_at") else None,
        })
    
    return {
        "sessions": sessions,
        "total": len(sessions),
    }
