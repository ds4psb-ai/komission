"""
Real-time Audio Coaching WebSocket Router

실시간 촬영 코칭을 위한 WebSocket 엔드포인트

Messages IN (Client → Server):
- {"type": "audio", "data": "<base64 PCM>"}
- {"type": "control", "action": "start"|"pause"|"stop"}
- {"type": "metric", "rule_id": "...", "value": 0.5, "t_sec": 1.5}

Messages OUT (Server → Client):
- {"type": "feedback", "message": "...", "audio_b64": "...", "rule_id": "..."}
- {"type": "rule_update", "rule_id": "...", "status": "passed"|"failed"}
- {"type": "session_status", "status": "active"|"ended", "stats": {...}}
- {"type": "error", "message": "..."}
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
from app.utils.time import utcnow

logger = logging.getLogger(__name__)
router = APIRouter()


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
    
    def create_session(self, session_id: str, coach: AudioCoach) -> Dict[str, Any]:
        """세션 생성"""
        session = {
            "session_id": session_id,
            "coach": coach,
            "started_at": utcnow(),
            "status": "idle",
            "recording_time": 0.0,
            "rules_evaluated": 0,
            "interventions_sent": 0,
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
):
    """
    실시간 오디오 코칭 WebSocket
    
    Connection:
        ws://localhost:8000/api/v1/ws/coaching/{session_id}?language=ko&voice_style=friendly
    
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
        session = manager.create_session(session_id, coach)
        
        # 3. Send initial status
        await manager.send_message(session_id, {
            "type": "session_status",
            "session_id": session_id,
            "status": "connected",
            "language": language,
            "voice_style": voice_style,
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
            try:
                await session["coach"].disconnect()
            except:
                pass
        manager.disconnect(session_id)


# ==================
# MESSAGE HANDLERS
# ==================

async def handle_control(session_id: str, session: dict, message: dict):
    """Control 메시지 처리 (start/pause/stop)"""
    action = message.get("action")
    
    if action == "start":
        session["status"] = "recording"
        session["recording_started_at"] = utcnow()
        
        # Gemini Live 연결 시도
        coach: AudioCoach = session["coach"]
        try:
            await coach.connect()
            
            await manager.send_message(session_id, {
                "type": "session_status",
                "status": "recording",
                "gemini_connected": True,
                "timestamp": utcnow().isoformat(),
            })
            
            logger.info(f"Recording started: {session_id}")
            
        except Exception as e:
            logger.warning(f"Gemini Live connection failed, using fallback: {e}")
            
            await manager.send_message(session_id, {
                "type": "session_status",
                "status": "recording",
                "gemini_connected": False,
                "fallback_mode": True,
                "timestamp": utcnow().isoformat(),
            })
    
    elif action == "pause":
        session["status"] = "paused"
        await manager.send_message(session_id, {
            "type": "session_status",
            "status": "paused",
            "timestamp": utcnow().isoformat(),
        })
    
    elif action == "stop":
        session["status"] = "ended"
        
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
    """Audio 청크 처리"""
    if session.get("status") != "recording":
        return
    
    audio_b64 = message.get("data")
    if not audio_b64:
        return
    
    try:
        # Base64 → PCM bytes
        pcm_data = base64.b64decode(audio_b64)
        
        # AudioCoach에 전달
        coach: AudioCoach = session["coach"]
        await coach.send_audio(pcm_data)
        
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
        
        # TTS 생성 (fallback: 텍스트만)
        audio_b64 = None
        try:
            # TODO: Google Cloud TTS 또는 Gemini TTS 연동
            # audio_bytes = await generate_tts(command["text"], voice_style)
            # audio_b64 = base64.b64encode(audio_bytes).decode()
            pass
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
