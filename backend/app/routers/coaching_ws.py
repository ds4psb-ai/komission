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
):
    """
    실시간 오디오 코칭 WebSocket
    
    Connection:
        ws://localhost:8000/api/v1/ws/coaching/{session_id}?video_id=123&voice_style=friendly
        ws://localhost:8000/api/v1/ws/coaching/{session_id}?outlier_id=uuid&voice_style=friendly
    
    Parameters:
        - video_id: RemixNode.node_id (메인에 게시된 카드)
        - outlier_id: OutlierItem.id (승격된 아웃라이어)
        - 둘 다 없으면 기본 proof patterns 사용
    
    Flow:
        1. Connect → server sends session_status
        2. Client sends control.start → coaching begins
        3. Client sends audio chunks → server processes
        4. Server sends feedback → client plays TTS
        5. Client sends control.stop → session ends
    """
    # 1. Accept connection
    if not await manager.connect(websocket, session_id):
        return
    
    try:
        # 2. Initialize AudioCoach
        coach = AudioCoach()
        session = manager.create_session(session_id, coach, voice_style)
        
        # Store video/outlier IDs for DirectorPack loading
        session["video_id"] = video_id
        session["outlier_id"] = outlier_id
        
        # 3. Send initial status
        await manager.send_message(session_id, {
            "type": "session_status",
            "session_id": session_id,
            "status": "connected",
            "language": language,
            "voice_style": voice_style,
            "video_id": video_id,
            "outlier_id": outlier_id,
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
                
                elif msg_type == "ping":
                    await manager.send_message(session_id, {
                        "type": "pong",
                        "timestamp": utcnow().isoformat(),
                    })
                
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
            if node and node.gemini_analysis:
                analysis = node.gemini_analysis
                
                # VDG v4 필수 필드 확인
                if "hook_genome" not in analysis and "scenes" not in analysis:
                    logger.warning(f"VDG v4 analysis not available for node: {node.node_id}")
                    return None
                
                vdg_v4 = VDGv4(
                    content_id=node.node_id,
                    duration_sec=analysis.get("duration_sec", 0),
                    **{k: v for k, v in analysis.items()
                       if k not in ["content_id", "duration_sec"]}
                )
                
                pack = compile_director_pack(vdg_v4)
                logger.info(f"DirectorPack loaded from VDG: {node.node_id}, {len(pack.dna_invariants)} rules")
                return pack
                
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
# H2: TTS FALLBACK UTILITIES
# ==================

async def generate_tts_fallback(text: str, lang: str = "ko") -> Optional[str]:
    """
    H2: TTS Fallback using gTTS (Google Text-to-Speech)
    
    Returns base64-encoded MP3 audio, or None if failed.
    Frontend will use Web Speech API if None.
    """
    if not text or len(text) < 2:
        return None
    
    try:
        # Try gTTS (free, no API key)
        from gtts import gTTS
        import io
        
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        audio_b64 = base64.b64encode(audio_buffer.read()).decode()
        logger.debug(f"TTS generated: {len(text)} chars -> {len(audio_b64)} bytes")
        return audio_b64
        
    except ImportError:
        logger.warning("gTTS not installed, falling back to Web Speech API on client")
        return None
    except Exception as e:
        logger.warning(f"gTTS failed: {e}")
        return None


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
        
        # DirectorPack 로드: VDG 우선, 없으면 기본 proof patterns
        pack = None
        video_id = session.get("video_id")
        outlier_id = session.get("outlier_id")
        
        try:
            # 1. 비디오/아웃라이어의 VDG에서 DirectorPack 로드
            if video_id or outlier_id:
                pack = await load_director_pack_from_video(
                    video_id=video_id,
                    outlier_id=outlier_id,
                )
            
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
            "rules_count": len(coach._director_pack.dna_invariants) if coach._director_pack else 0,
            "checkpoint_evaluation": True,  # Indicate checkpoint loop is active
            "timestamp": utcnow().isoformat(),
        })
        
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
