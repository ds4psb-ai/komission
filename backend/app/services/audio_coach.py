"""
Gemini Live Audio Coach (L3: The Director)

실시간 촬영 코칭 시스템 with DirectorPack 통합

Blueprint Philosophy:
- One-Command Priority Queue: Critical DNA > Technical Fail > High Impact > Minor Fix
- Checkpoint-Based Rule Activation: time-based rule activation
- DNA Lock: 모델이 바뀌어도 제약조건은 우리가 쥔다

Hardening (H0-1 ~ H0-6):
- H0-1: API Retry + Reconnect
- H0-2: Session Lifecycle Management
- H0-3: Violation Detection Callback
- H0-4: Barge-in Handling
- H0-5: Logging + Provenance
- H0-6: Rule Dedup
"""
import asyncio
import logging
import os
import time
import random
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from app.schemas.director_pack import (
    DirectorPack,
    DNAInvariant,
    MutationSlot,
    ForbiddenMutation,
    Checkpoint,
    Policy,
    CoachLineTemplates
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 오디오 전용 Live API 모델 (2025 Latest)
LIVE_MODEL = "gemini-2.5-flash-native-audio-latest"

# Priority order for One-Command Queue
PRIORITY_ORDER = ["critical", "high", "medium", "low"]


# ==================
# H0-5: Coaching Event Log
# ==================

@dataclass
class CoachingEvent:
    """코칭 이벤트 기록 (H0-5: Provenance)"""
    rule_id: str
    command: str
    current_time: float
    timestamp: datetime
    tone: str
    priority: str
    checkpoint_id: Optional[str] = None


@dataclass  
class ViolationEvent:
    """위반 이벤트 기록 (H0-3)"""
    rule_id: str
    current_time: float
    timestamp: datetime
    severity: str = "warning"


class AudioCoach:
    """
    L3 실시간 촬영 코치 (The Director)
    
    VDG 분석 결과(DirectorPack)를 기반으로 실시간 음성 코칭 제공
    
    Blueprint:
    - One-Command Policy: 한 번에 하나의 명령만
    - Priority Queue: Critical > High > Medium > Low
    - Checkpoint-based: 시간에 따른 규칙 활성화
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not GENAI_AVAILABLE:
            raise ImportError("pip install google-genai")
        
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required")
        
        self.client = genai.Client(api_key=self.api_key)
        self._session = None
        self._director_pack: Optional[DirectorPack] = None
        self._system_prompt: Optional[str] = None
        
        # Cooldown tracking
        self._last_command_time: float = 0.0
        self._cooldown_sec: float = 4.0
        
        # Tone setting
        self._tone: str = "friendly"  # "strict" | "friendly" | "neutral"
        
        # H0-5: Logging
        self._coaching_log: List[CoachingEvent] = []
        self._violation_log: List[ViolationEvent] = []
        self._session_start_time: Optional[float] = None
        
        # H0-6: Rule Dedup
        self._delivered_rule_ids: Set[str] = set()
        
        # H0-3: Violation Callback
        self._violation_callback: Optional[Callable[[str, float], None]] = None
        
        # H0-4: Barge-in state
        self._pending_command: Optional[str] = None
        self._is_user_speaking: bool = False
    
    # ==================
    # H0-2: Session Lifecycle (Async Context Manager)
    # ==================
    
    async def connect(self):
        """세션 시작 (H0-1 + H0-2)"""
        self._session = await self._connect_with_retry()
        self._session_start_time = time.time()
        self._delivered_rule_ids.clear()
        self._coaching_log.clear()
        self._violation_log.clear()
        logger.info("✅ Live Session 연결됨")
        return self
    
    async def disconnect(self):
        """세션 종료"""
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.warning(f"세션 종료 중 오류: {e}")
            finally:
                self._session = None
                logger.info("🔌 Live Session 종료됨")
    
    async def __aenter__(self):
        return await self.connect()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False
    
    # ==================
    # H0-1: API Retry + Reconnect
    # ==================
    
    async def _connect_with_retry(self, max_retries: int = 3):
        """재시도 로직이 있는 연결 (H0-1)"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                config = {
                    "response_modalities": ["AUDIO"],
                }
                
                if self._system_prompt:
                    config["system_instruction"] = self._system_prompt
                else:
                    config["system_instruction"] = "너는 숏폼 촬영 코치야. 한국어로 짧게 답해줘."
                
                session = await self.client.aio.live.connect(
                    model=LIVE_MODEL,
                    config=config,
                )
                return session
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                is_retryable = any(x in error_str for x in [
                    "429", "rate limit", "quota",
                    "500", "502", "503", "504", "internal",
                    "timeout", "connection", "network"
                ])
                
                if is_retryable and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"⚠️ 연결 재시도 ({attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        raise last_error or Exception("연결 실패")
        
    def set_coaching_context(
        self, 
        director_pack: Union[DirectorPack, Dict[str, Any]],
        tone: str = "friendly"
    ):
        """
        DirectorPack을 코칭 컨텍스트로 설정
        """
        # Support both Pydantic and dict for backward compat
        if isinstance(director_pack, dict):
            self._director_pack = None
            self._system_prompt = self._build_prompt_legacy(director_pack)
        else:
            self._director_pack = director_pack
            self._system_prompt = self._build_prompt_from_pack(director_pack)
            
            # Apply policy
            if director_pack.policy:
                self._cooldown_sec = director_pack.policy.cooldown_sec or 4.0
        
        self._tone = tone
        # H0-6: Reset delivered rules when context changes
        self._delivered_rule_ids.clear()
        logger.info(f"✅ 코칭 컨텍스트 설정: {len(self._system_prompt)} chars, tone={tone}")
        
    def _build_prompt_from_pack(self, pack: DirectorPack) -> str:
        """DirectorPack → 시스템 프롬프트 변환 (L3 Blueprint)"""
        lines = [
            "너는 숏폼 촬영 코치야. 실시간으로 촬영 피드백을 줘.",
            "",
            "=== 핵심 원칙 (DNA Lock) ===",
            "아래 규칙은 반드시 지켜야 함. 우선순위대로 하나씩만 피드백해.",
            "",
        ]
        
        # DNA Invariants (sorted by priority)
        if pack.dna_invariants:
            lines.append("[필수 규칙 - 우선순위순]")
            for priority in PRIORITY_ORDER:
                rules = [r for r in pack.dna_invariants if r.priority == priority]
                for rule in rules[:3]:  # Top 3 per priority
                    time_hint = ""
                    if rule.time_scope:
                        t0, t1 = rule.time_scope.t_window
                        time_hint = f" ({t0:.0f}~{t1:.0f}초)"
                    lines.append(f"  [{priority.upper()}]{time_hint} {rule.check_hint}")
            lines.append("")
        
        # Mutation Slots (변수 영역)
        if pack.mutation_slots:
            lines.append("[조절 가능 영역]")
            for slot in pack.mutation_slots[:3]:
                lines.append(f"  - {slot.slot_type}: {slot.guide}")
            lines.append("")
        
        # Forbidden
        if pack.forbidden_mutations:
            lines.append("[절대 금지]")
            for fm in pack.forbidden_mutations[:3]:
                lines.append(f"  ❌ {fm.reason}")
            lines.append("")
        
        # Checkpoints
        if pack.checkpoints:
            lines.append("[시간별 체크포인트]")
            for cp in pack.checkpoints[:5]:
                t0, t1 = cp.t_window
                lines.append(f"  {t0:.0f}~{t1:.0f}초: {cp.note}")
            lines.append("")
        
        # Policy
        lines.extend([
            "=== 피드백 정책 ===",
            f"- 한 번에 하나의 피드백만 (One-Command)",
            f"- {self._cooldown_sec}초 쿨다운",
            "- 짧고 명확하게 (10단어 이내)",
            "- 한국어로",
            "",
            "사용자가 '시작' 또는 촬영을 시작하면 타이머를 시작해.",
        ])
        
        return "\n".join(lines)
    
    def _build_prompt_legacy(self, pack: Dict[str, Any]) -> str:
        """Legacy dict-based pack → prompt (backward compat)"""
        lines = [
            "너는 숏폼 촬영 코치야. 사용자의 질문에 음성으로 답해줘.",
            "",
            "=== 촬영 가이드 ===",
        ]
        
        if hook := pack.get("hook"):
            lines.extend([
                f"훅 타입: {hook.get('type', 'N/A')}",
                f"첫 {hook.get('duration_sec', 2)}초가 핵심",
            ])
        
        if shots := pack.get("shot_list"):
            lines.append("\n[샷 리스트]")
            for i, shot in enumerate(shots[:5]):
                lines.append(f"샷{i+1}: {shot.get('description', '')}")
        
        if invariants := pack.get("invariant"):
            lines.append("\n[반드시 지켜야 할 것]")
            for item in invariants[:3]:
                lines.append(f"- {item}")
        
        if donts := pack.get("do_not"):
            lines.append("\n[하지 말아야 할 것]")
            for item in donts[:3]:
                lines.append(f"- {item}")
        
        lines.extend([
            "",
            "=== 응답 스타일 ===",
            "- 짧고 명확하게 (1-2문장)",
            "- 친근하지만 전문적으로",
            "- 한국어로",
        ])
        
        return "\n".join(lines)
    
    # ==================
    # One-Command Priority Queue (with H0-5, H0-6)
    # ==================
    
    def get_next_command(self, current_time: float) -> Optional[str]:
        """
        One-Command Priority Queue: 현재 시간에 맞는 최우선 명령 반환
        
        H0-5: 명령 로깅
        H0-6: 중복 방지
        """
        if not self._director_pack:
            return None
        
        # H0-4: Check barge-in state
        if self._is_user_speaking:
            return None
        
        # Check cooldown
        now = time.time()
        if now - self._last_command_time < self._cooldown_sec:
            return None
        
        # Get active rules based on checkpoints
        active_rules = self._get_active_rules(current_time)
        
        if not active_rules:
            return None
        
        # Priority queue with H0-6 dedup
        for priority in PRIORITY_ORDER:
            for rule in active_rules:
                if rule.priority == priority:
                    # H0-6: Skip already delivered
                    if rule.rule_id in self._delivered_rule_ids:
                        continue
                    
                    self._last_command_time = now
                    cmd = self._format_command(rule)
                    
                    # H0-5: Log the event
                    self._coaching_log.append(CoachingEvent(
                        rule_id=rule.rule_id,
                        command=cmd,
                        current_time=current_time,
                        timestamp=datetime.utcnow(),
                        tone=self._tone,
                        priority=priority,
                        checkpoint_id=self._get_current_checkpoint_id(current_time)
                    ))
                    
                    # H0-6: Mark as delivered
                    self._delivered_rule_ids.add(rule.rule_id)
                    
                    logger.info(f"📣 Command @ {current_time:.1f}s [{priority}]: {cmd[:30]}...")
                    return cmd
        
        return None
    
    def _get_current_checkpoint_id(self, current_time: float) -> Optional[str]:
        """현재 checkpoint ID 반환"""
        if not self._director_pack:
            return None
        for cp in self._director_pack.checkpoints:
            if cp.t_window[0] <= current_time <= cp.t_window[1]:
                return cp.checkpoint_id
        return None
    
    def _get_active_rules(self, current_time: float) -> List[DNAInvariant]:
        """Checkpoint 기반 규칙 활성화"""
        if not self._director_pack:
            return []
        
        # Find active checkpoints
        active_checkpoints = [
            cp for cp in self._director_pack.checkpoints
            if cp.t_window[0] <= current_time <= cp.t_window[1]
        ]
        
        # Collect active rule IDs
        active_rule_ids = set()
        for cp in active_checkpoints:
            active_rule_ids.update(cp.active_rules)
        
        # If no checkpoints, use "overall" or all rules
        if not active_rule_ids:
            overall = next(
                (cp for cp in self._director_pack.checkpoints if cp.checkpoint_id == "overall"),
                None
            )
            if overall:
                active_rule_ids.update(overall.active_rules)
            else:
                # Fallback: all rules active
                return list(self._director_pack.dna_invariants)
        
        # Filter rules by active IDs
        return [
            r for r in self._director_pack.dna_invariants
            if r.rule_id in active_rule_ids
        ]
    
    def _format_command(self, rule: DNAInvariant) -> str:
        """규칙 → 코칭 명령 포맷팅"""
        templates = rule.coach_line_templates
        
        if not templates:
            return rule.check_hint or f"[{rule.rule_id}] 확인하세요"
        
        # Select by tone
        if self._tone == "strict" and templates.strict:
            return templates.strict
        elif self._tone == "friendly" and templates.friendly:
            return templates.friendly
        elif templates.neutral:
            return templates.neutral
        else:
            return rule.check_hint or templates.strict or templates.friendly or ""
    
    # ==================
    # H0-3: Violation Detection
    # ==================
    
    def register_violation_callback(self, callback: Callable[[str, float], None]):
        """위반 감지 콜백 등록 (H0-3)"""
        self._violation_callback = callback
    
    def report_violation(self, rule_id: str, current_time: float, severity: str = "warning"):
        """
        위반 보고 (H0-3)
        
        Args:
            rule_id: 위반된 규칙 ID
            current_time: 위반 시점
            severity: "warning" | "critical"
        """
        # Log violation
        self._violation_log.append(ViolationEvent(
            rule_id=rule_id,
            current_time=current_time,
            timestamp=datetime.utcnow(),
            severity=severity
        ))
        
        logger.warning(f"⚠️ Violation @ {current_time:.1f}s: {rule_id} [{severity}]")
        
        # Callback
        if self._violation_callback:
            self._violation_callback(rule_id, current_time)
        
        # Force immediate command for critical violations
        if severity == "critical" and self._director_pack:
            rule = next(
                (r for r in self._director_pack.dna_invariants if r.rule_id == rule_id),
                None
            )
            if rule:
                # Reset cooldown for critical
                self._last_command_time = 0
                # Remove from delivered to allow re-delivery
                self._delivered_rule_ids.discard(rule_id)
    
    # ==================
    # H0-4: Barge-in Handling
    # ==================
    
    def set_user_speaking(self, is_speaking: bool):
        """유저 말하기 상태 설정 (H0-4)"""
        was_speaking = self._is_user_speaking
        self._is_user_speaking = is_speaking
        
        if was_speaking and not is_speaking:
            # User finished speaking, deliver pending command
            if self._pending_command:
                logger.info(f"📤 Pending command delivered: {self._pending_command[:30]}...")
                self._pending_command = None
    
    async def handle_barge_in(self):
        """유저가 끼어들었을 때 처리 (H0-4)"""
        if not self._director_pack or not self._director_pack.policy:
            return
        
        policy = self._director_pack.policy.barge_in_handling
        
        if policy == "stop_and_ack":
            logger.info("🛑 Barge-in: stop_and_ack")
            if self._session:
                # Send acknowledgment
                await self._session.send_realtime_input(text="네, 말씀하세요.")
        elif policy == "queue_response":
            logger.info("📥 Barge-in: queue_response")
            # Keep pending command for later
            pass
        else:
            # Default: continue
            pass
    
    # ==================
    # H0-5: Log Access
    # ==================
    
    def get_coaching_log(self) -> List[CoachingEvent]:
        """코칭 로그 반환"""
        return self._coaching_log.copy()
    
    def get_violation_log(self) -> List[ViolationEvent]:
        """위반 로그 반환"""
        return self._violation_log.copy()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        세션 통계 + R_ES Score 계산 (Phase 2: Blueprint GI Formula)
        
        Blueprint: GI = D_NA × 50% + P_E × 35% + R_ES × 15%
        R_ES = (rules_followed / rules_total) × response_factor
        """
        commands = len(self._coaching_log)
        violations = len(self._violation_log)
        rules_covered = len(self._delivered_rule_ids)
        total_rules = len(self._director_pack.dna_invariants) if self._director_pack else 0
        duration = time.time() - self._session_start_time if self._session_start_time else 0
        
        # R_ES Score Calculation (Phase 2)
        res_score = self._calculate_res_score()
        
        return {
            "commands_delivered": commands,
            "violations_detected": violations,
            "rules_covered": rules_covered,
            "total_rules": total_rules,
            "session_duration_sec": duration,
            # Phase 2: R_ES Score
            "res_score": res_score,
            "res_grade": self._get_res_grade(res_score),
        }
    
    def _calculate_res_score(self) -> float:
        """
        R_ES (Real-time Execution Score) 계산
        
        공식: R_ES = (followed_ratio) × (1 - violation_penalty) × response_speed_factor
        
        - followed_ratio: 전달된 규칙 비율 (rules_covered / total_rules)
        - violation_penalty: 위반 비율 (violations / commands)
        - response_speed_factor: 평균 반응 시간 기반 (생략: Phase 3)
        """
        if not self._director_pack:
            return 0.0
        
        total_rules = len(self._director_pack.dna_invariants)
        if total_rules == 0:
            return 1.0  # No rules = perfect score
        
        # 1. Rule Coverage (50% weight)
        rules_covered = len(self._delivered_rule_ids)
        coverage_ratio = min(rules_covered / total_rules, 1.0)
        
        # 2. Violation Penalty (30% weight)
        commands = len(self._coaching_log)
        violations = len(self._violation_log)
        if commands > 0:
            violation_ratio = violations / commands
            violation_score = max(0.0, 1.0 - violation_ratio * 2)  # 50% violation = 0 score
        else:
            violation_score = 1.0  # No commands = no violations
        
        # 3. Session Completion (20% weight)
        # Did user complete the expected duration?
        expected_duration = self._director_pack.policy.cooldown_sec * total_rules if self._director_pack.policy else 30
        actual_duration = time.time() - (self._session_start_time or time.time())
        completion_ratio = min(actual_duration / max(expected_duration, 1), 1.0)
        
        # Final R_ES Score
        res_score = (
            coverage_ratio * 0.5 +
            violation_score * 0.3 +
            completion_ratio * 0.2
        )
        
        return round(res_score, 3)
    
    def _get_res_grade(self, score: float) -> str:
        """R_ES 점수 → 등급"""
        if score >= 0.9:
            return "S"
        elif score >= 0.7:
            return "A"
        elif score >= 0.5:
            return "B"
        elif score >= 0.3:
            return "C"
        else:
            return "D"
    
    def reset_session(self):
        """세션 상태 리셋 (H0-6 dedup 포함)"""
        self._delivered_rule_ids.clear()
        self._coaching_log.clear()
        self._violation_log.clear()
        self._last_command_time = 0
        self._pending_command = None
        self._is_user_speaking = False
        logger.info("🔄 Session reset")
    
    def get_mutation_guidance(self, slot_id: str, option: str) -> Optional[str]:
        """Mutation Slot에 대한 가이드 반환"""
        if not self._director_pack:
            return None
        
        slot = next(
            (s for s in self._director_pack.mutation_slots if s.slot_id == slot_id),
            None
        )
        
        if not slot or not slot.coach_line_templates:
            return None
        
        return slot.coach_line_templates.get(option) or slot.coach_line_templates.get("default")
    
    # ==================
    # Live API Session (Expert Fix: @asynccontextmanager)
    # ==================
    
    @asynccontextmanager
    async def start_session(self):
        """
        세션 생명주기 관리 (Expert Fix: @asynccontextmanager 적용)
        
        Usage:
            async with coach.start_session() as session:
                await coach.send_command("rule_id", "멋지게 시작!")
        """
        config = {
            "response_modalities": ["AUDIO"],
        }
        
        if self._system_prompt:
            config["system_instruction"] = self._system_prompt
        else:
            config["system_instruction"] = "너는 숏폼 촬영 코치야. 한국어로 짧게 답해줘."
        
        # H0-2 + H0-1: 재시도 로직을 통한 세션 생성
        try:
            connect_cm = await self._connect_with_retry()
            self._session = connect_cm
            self._session_start_time = time.time()
            self._delivered_rule_ids.clear()
            logger.info(f"🎙️ Live Session 연결! ({LIVE_MODEL})")
            yield connect_cm
        finally:
            if self._session:
                try:
                    await self._session.close()
                except Exception as e:
                    logger.warning(f"세션 종료 중 오류: {e}")
                finally:
                    self._session = None
                    logger.info("🔌 Live Session 종료됨")
    
    # ==================
    # Expert Advice: send_command (Mouth 역할)
    # ==================
    
    async def send_command(self, rule_id: str, command_text: str):
        """
        외부에서 '이 말 해!'라고 시킬 때 호출
        
        Expert Advice: 쿨타임이 안 지났으면 무시 (앵무새 방지)
        
        Args:
            rule_id: 규칙 ID (H0-6 dedup용)
            command_text: 실제 말할 텍스트
        """
        if not self._session:
            logger.error("세션이 연결되지 않았습니다.")
            return False
        
        now = time.time()
        
        # H0-6: 쿨타임 체크 (same rule cooldown)
        if rule_id in self._delivered_rule_ids:
            # 이미 전달된 규칙은 세션 내에서 반복 안 함
            logger.debug(f"Skip '{rule_id}': 이미 전달됨")
            return False
        
        # Global cooldown check
        if now - self._last_command_time < self._cooldown_sec:
            logger.debug(f"Skip: 쿨다운 중 ({self._cooldown_sec}s)")
            return False
        
        logger.info(f"📢 Coach Speaking: {command_text}")
        
        # 텍스트 입력 → 모델이 음성으로 읽어줌 (TTS + 페르소나)
        try:
            await self._session.send(input=command_text, end_of_turn=True)
            
            # H0-5: 로그 기록
            self._coaching_log.append(CoachingEvent(
                rule_id=rule_id,
                command=command_text,
                current_time=now - (self._session_start_time or now),
                timestamp=datetime.utcnow(),
                tone=self._tone,
                priority="command",
                checkpoint_id=None
            ))
            
            # H0-6: 전달 완료 마킹
            self._delivered_rule_ids.add(rule_id)
            self._last_command_time = now
            
            return True
        except Exception as e:
            logger.error(f"명령 전송 실패: {e}")
            return False
            
    async def send_audio(self, pcm_data: bytes):
        """오디오 입력 전송 (16-bit PCM, 16kHz, mono)"""
        if not self._session:
            raise RuntimeError("연결 안됨")
        await self._session.send_realtime_input(
            audio={"data": pcm_data, "mime_type": "audio/pcm"}
        )
    
    async def receive_audio(self, on_audio: Callable[[bytes], None]):
        """오디오 응답 수신 (24kHz PCM)"""
        if not self._session:
            raise RuntimeError("연결 안됨")
        
        while True:
            turn = self._session.receive()
            async for r in turn:
                if r.server_content and r.server_content.model_turn:
                    for part in r.server_content.model_turn.parts:
                        if part.inline_data and isinstance(part.inline_data.data, bytes):
                            on_audio(part.inline_data.data)


# ==================
# 테스트
# ==================

async def test_hardened_coach():
    """하드닝 테스트"""
    print("=== L3 AudioCoach Hardening Test ===")
    
    from app.schemas.vdg_v4 import VDGv4, SemanticPassResult, HookGenome, Microbeat, Scene
    from app.services.vdg_2pass.director_compiler import compile_director_pack
    
    # 1. Create sample VDG
    vdg = VDGv4(
        content_id="test_video",
        duration_sec=15.0,
        semantic=SemanticPassResult(
            hook_genome=HookGenome(
                strength=0.85,
                microbeats=[
                    Microbeat(t=0.5, role="start"),
                    Microbeat(t=1.8, role="punch")
                ]
            ),
            scenes=[
                Scene(scene_id="S01", time_start=0.0, time_end=5.0, duration_sec=5.0, narrative_role="Hook"),
            ]
        )
    )
    
    pack = compile_director_pack(vdg)
    print(f"✅ DirectorPack: {len(pack.dna_invariants)} rules")
    
    # 2. Test hardened features (no API key needed)
    coach = AudioCoach.__new__(AudioCoach)
    coach._director_pack = pack
    coach._system_prompt = "test"
    coach._cooldown_sec = 2.0
    coach._tone = "friendly"
    coach._last_command_time = 0
    coach._coaching_log = []
    coach._violation_log = []
    coach._delivered_rule_ids = set()
    coach._session_start_time = time.time()
    coach._is_user_speaking = False
    coach._pending_command = None
    coach._violation_callback = None
    
    # 3. H0-6: Dedup test
    print("\n[H0-6 Dedup Test]")
    for t in [0.5, 1.0, 1.5]:
        coach._last_command_time = 0  # Reset cooldown
        cmd = coach.get_next_command(current_time=t)
        delivered = len(coach._delivered_rule_ids)
        print(f"   t={t:.1f}s → {cmd[:30] if cmd else '(no new command)'} (delivered: {delivered})")
    
    # 4. H0-5: Log test
    print(f"\n[H0-5 Logging Test]")
    print(f"   Coaching log: {len(coach._coaching_log)} events")
    for event in coach._coaching_log:
        print(f"     - {event.rule_id} @ {event.current_time}s")
    
    # 5. H0-3: Violation test
    print(f"\n[H0-3 Violation Test]")
    coach.report_violation("hook_timing_2s", current_time=2.5, severity="critical")
    print(f"   Violations: {len(coach._violation_log)}")
    
    # 6. Stats
    print(f"\n[Stats]")
    stats = coach.get_session_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print("\n🎉 Hardening Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_hardened_coach())
