"""
Phase 3: LLM-Based Adaptive Coaching Service

사용자 피드백을 LLM으로 파싱하고 DNAInvariant를 검증하여
바이럴 요소를 손상시키지 않는 범위에서 대안 제시

핵심 원칙:
- LLM 시스템 프롬프트에 DNAInvariant 목록 주입
- critical/high priority invariant → 거절 + 대안 제시
- medium/low priority 또는 미지정 → 허용
"""
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from app.schemas.director_pack import DirectorPack, DNAInvariant, MutationSlot
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class UserFeedback:
    """파싱된 사용자 피드백"""
    raw_text: str
    feedback_type: Literal["cannot_do", "alternative_idea", "question", "ok", "creative"]
    affected_domain: Optional[str] = None  # composition, timing, audio, etc.
    affected_rule_id: Optional[str] = None  # 직접 연관된 규칙 ID
    proposed_change: Optional[str] = None
    user_reason: Optional[str] = None  # 사용자 의도/이유
    confidence: float = 0.0


@dataclass
class AdaptiveResponse:
    """적응형 코칭 응답"""
    accepted: bool
    message: str
    alternative: Optional[str] = None
    reason: Optional[str] = None
    affected_rule_id: Optional[str] = None
    coaching_adjustment: Optional[str] = None  # 허용 시 코칭 조정 내용


# ==================
# SYSTEM PROMPT TEMPLATES
# ==================

FEEDBACK_PARSER_SYSTEM_PROMPT = """당신은 실시간 촬영 코칭 시스템의 피드백 분석기입니다.

## 역할
사용자의 피드백을 분석하여 구조화된 정보를 추출합니다.

## 현재 코칭 규칙 (DNAInvariant)
{invariants_json}

## 허용 가능한 변형 (MutationSlot)
{slots_json}

## 피드백 타입
- **cannot_do**: 사용자가 현재 코칭을 따를 수 없는 상황 (장비, 환경, 물리적 제약)
- **alternative_idea**: 사용자가 다른 창의적 아이디어를 제안
- **question**: 코칭에 대한 질문
- **ok**: 코칭 수락
- **creative**: 창의적 표현/연출 제안 (바이럴 요소와 무관한 순수 창작)

## 출력 형식 (JSON)
```json
{
  "feedback_type": "cannot_do|alternative_idea|question|ok|creative",
  "affected_domain": "composition|timing|lighting|audio|performance|null",
  "affected_rule_id": "규칙ID|null",
  "proposed_change": "사용자가 제안하는 대안|null",
  "user_reason": "사용자의 이유/의도|null",
  "confidence": 0.0-1.0
}
```

## 주의사항
1. affected_rule_id는 위 규칙 목록에서 정확히 매칭되는 것만 사용
2. creative 타입은 바이럴 핵심(critical/high) 규칙과 충돌하지 않는 순수 창작
3. 모호한 경우 question으로 분류

사용자 피드백을 분석하세요."""


COACHING_DECISION_SYSTEM_PROMPT = """당신은 실시간 촬영 코칭 시스템의 적응형 코치입니다.

## 역할
사용자의 피드백에 대해 바이럴 요소를 보호하면서 유연하게 대응합니다.

## 핵심 원칙
1. **바이럴 DNA 보호**: critical/high priority 규칙은 절대 양보하지 않음
2. **유연한 대응**: medium/low priority 규칙은 사용자 제안 수용 가능
3. **창의성 존중**: 바이럴 요소와 무관한 창작은 적극 지지

## 현재 코칭 규칙
{invariants_json}

## 허용 가능한 변형
{slots_json}

## 사용자 피드백 분석 결과
{feedback_json}

## 응답 형식 (JSON)
```json
{
  "accepted": true|false,
  "message": "사용자에게 전달할 메시지 (친근하고 짧게)",
  "alternative": "거절 시 대안 제안|null",
  "reason": "결정 이유 (내부용)",
  "coaching_adjustment": "허용 시 코칭 조정 내용|null"
}
```

## 응답 톤
- 친근하고 지지적인 톤
- 거절해도 대안 제시로 긍정적 마무리
- 허용 시 적극적 격려

결정을 내려주세요."""


class AdaptiveCoachingService:
    """
    Phase 3: LLM 기반 적응형 코칭 서비스
    
    시스템 프롬프트에 DNAInvariant 목록을 주입하여
    LLM이 바이럴 요소를 이해하고 스마트하게 판단
    """
    
    def __init__(
        self,
        director_pack: Optional[DirectorPack] = None,
        llm_client: Optional[Any] = None,  # Gemini/OpenAI client
        use_llm: bool = True,  # LLM 사용 여부 (폴백용)
    ):
        self._pack = director_pack
        self._llm_client = llm_client
        self._use_llm = use_llm
        self._invariants_map: Dict[str, DNAInvariant] = {}
        self._slots_map: Dict[str, MutationSlot] = {}
        
        if director_pack:
            self._build_maps(director_pack)
    
    def _build_maps(self, pack: DirectorPack) -> None:
        """DNAInvariant와 MutationSlot 맵 구축"""
        for inv in pack.dna_invariants:
            self._invariants_map[inv.rule_id] = inv
        
        for slot in pack.mutation_slots:
            self._slots_map[slot.slot_id] = slot
    
    def update_pack(self, pack: DirectorPack) -> None:
        """DirectorPack 업데이트"""
        self._pack = pack
        self._invariants_map.clear()
        self._slots_map.clear()
        self._build_maps(pack)
    
    def _invariants_to_json(self) -> str:
        """DNAInvariant를 LLM 프롬프트용 JSON으로 변환"""
        items = []
        for inv in self._invariants_map.values():
            items.append({
                "rule_id": inv.rule_id,
                "domain": inv.domain,
                "priority": inv.priority,  # critical, high, medium, low
                "description": inv.check_hint or "",
                "tolerance": inv.tolerance,
            })
        return json.dumps(items, ensure_ascii=False, indent=2)
    
    def _slots_to_json(self) -> str:
        """MutationSlot을 LLM 프롬프트용 JSON으로 변환"""
        items = []
        for slot in self._slots_map.values():
            items.append({
                "slot_id": slot.slot_id,
                "description": slot.description or "",
                "variants": slot.variants[:5] if slot.variants else [],
            })
        return json.dumps(items, ensure_ascii=False, indent=2)
    
    async def parse_user_feedback_llm(self, text: str) -> UserFeedback:
        """
        LLM을 사용하여 사용자 피드백 파싱
        """
        if not self._use_llm or not self._llm_client:
            return self._parse_user_feedback_fallback(text)
        
        system_prompt = FEEDBACK_PARSER_SYSTEM_PROMPT.format(
            invariants_json=self._invariants_to_json(),
            slots_json=self._slots_to_json(),
        )
        
        try:
            # Gemini API 호출
            response = await self._call_llm(
                system_prompt=system_prompt,
                user_message=f"사용자 피드백: {text}",
            )
            
            # JSON 파싱
            result = self._extract_json(response)
            
            return UserFeedback(
                raw_text=text,
                feedback_type=result.get("feedback_type", "question"),
                affected_domain=result.get("affected_domain"),
                affected_rule_id=result.get("affected_rule_id"),
                proposed_change=result.get("proposed_change"),
                user_reason=result.get("user_reason"),
                confidence=result.get("confidence", 0.8),
            )
            
        except Exception as e:
            logger.warning(f"LLM parsing failed, using fallback: {e}")
            return self._parse_user_feedback_fallback(text)
    
    async def generate_response_llm(self, feedback: UserFeedback) -> AdaptiveResponse:
        """
        LLM을 사용하여 적응형 응답 생성
        """
        if not self._use_llm or not self._llm_client:
            return self._generate_response_fallback(feedback)
        
        feedback_json = json.dumps({
            "feedback_type": feedback.feedback_type,
            "affected_domain": feedback.affected_domain,
            "affected_rule_id": feedback.affected_rule_id,
            "proposed_change": feedback.proposed_change,
            "user_reason": feedback.user_reason,
        }, ensure_ascii=False)
        
        system_prompt = COACHING_DECISION_SYSTEM_PROMPT.format(
            invariants_json=self._invariants_to_json(),
            slots_json=self._slots_to_json(),
            feedback_json=feedback_json,
        )
        
        try:
            response = await self._call_llm(
                system_prompt=system_prompt,
                user_message="위 피드백에 대한 결정을 내려주세요.",
            )
            
            result = self._extract_json(response)
            
            return AdaptiveResponse(
                accepted=result.get("accepted", True),
                message=result.get("message", "네, 알겠어요!"),
                alternative=result.get("alternative"),
                reason=result.get("reason"),
                affected_rule_id=feedback.affected_rule_id,
                coaching_adjustment=result.get("coaching_adjustment"),
            )
            
        except Exception as e:
            logger.warning(f"LLM response failed, using fallback: {e}")
            return self._generate_response_fallback(feedback)
    
    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        LLM API 호출 (Gemini 또는 OpenAI)
        """
        if hasattr(self._llm_client, 'generate_content'):
            # Gemini
            response = await self._llm_client.generate_content_async(
                contents=[
                    {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_message}"}]}
                ],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 500,
                }
            )
            return response.text
        
        elif hasattr(self._llm_client, 'chat'):
            # OpenAI
            response = await self._llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content
        
        raise ValueError("Unknown LLM client type")
    
    def _extract_json(self, text: str) -> dict:
        """LLM 응답에서 JSON 추출"""
        import re
        
        # ```json ... ``` 블록 찾기
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # { ... } 찾기
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        return {}
    
    # ==================
    # FALLBACK (키워드 기반)
    # ==================
    
    CANNOT_DO_KEYWORDS = ["못", "안 돼", "불가능", "can't", "cannot", "impossible", "어려워"]
    ALTERNATIVE_KEYWORDS = ["대신", "이거 어때", "다른", "instead", "how about", "what if"]
    QUESTION_KEYWORDS = ["?", "어떻게", "왜", "how", "why", "what"]
    OK_KEYWORDS = ["알겠", "네", "ok", "yes", "좋아", "확인"]
    
    DOMAIN_KEYWORDS = {
        "composition": ["구도", "중앙", "위치", "center", "position", "frame"],
        "timing": ["타이밍", "시간", "빨리", "느리", "timing", "fast", "slow"],
        "lighting": ["조명", "역광", "밝", "어두", "light", "bright", "dark"],
        "audio": ["소리", "음성", "목소리", "audio", "voice", "sound"],
        "performance": ["표정", "연기", "동작", "expression", "action", "gesture"],
    }
    
    def _parse_user_feedback_fallback(self, text: str) -> UserFeedback:
        """키워드 기반 폴백 파싱"""
        text_lower = text.lower()
        
        feedback_type: Literal["cannot_do", "alternative_idea", "question", "ok", "creative"] = "question"
        confidence = 0.5
        
        if any(kw in text for kw in self.CANNOT_DO_KEYWORDS):
            feedback_type = "cannot_do"
            confidence = 0.7
        elif any(kw in text for kw in self.ALTERNATIVE_KEYWORDS):
            feedback_type = "alternative_idea"
            confidence = 0.6
        elif any(kw in text for kw in self.OK_KEYWORDS):
            feedback_type = "ok"
            confidence = 0.9
        elif any(kw in text for kw in self.QUESTION_KEYWORDS):
            feedback_type = "question"
            confidence = 0.5
        
        affected_domain = None
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                affected_domain = domain
                break
        
        # 도메인에서 규칙 ID 찾기
        affected_rule_id = None
        if affected_domain:
            for inv in self._invariants_map.values():
                if inv.domain == affected_domain:
                    affected_rule_id = inv.rule_id
                    break
        
        return UserFeedback(
            raw_text=text,
            feedback_type=feedback_type,
            affected_domain=affected_domain,
            affected_rule_id=affected_rule_id,
            proposed_change=None,
            user_reason=None,
            confidence=confidence,
        )
    
    def _generate_response_fallback(self, feedback: UserFeedback) -> AdaptiveResponse:
        """키워드 기반 폴백 응답"""
        if feedback.feedback_type == "ok":
            return AdaptiveResponse(accepted=True, message="좋아요! 계속 진행해요!")
        
        if feedback.feedback_type == "question":
            return AdaptiveResponse(accepted=True, message="궁금한 점이 있으시군요!")
        
        # cannot_do / alternative_idea → DNAInvariant 검증
        affected_inv = self._invariants_map.get(feedback.affected_rule_id) if feedback.affected_rule_id else None
        
        if not affected_inv and feedback.affected_domain:
            for inv in self._invariants_map.values():
                if inv.domain == feedback.affected_domain:
                    affected_inv = inv
                    break
        
        if not affected_inv:
            return AdaptiveResponse(
                accepted=True,
                message="좋아요! 그렇게 해볼까요?",
            )
        
        if affected_inv.priority in ["critical", "high"]:
            return AdaptiveResponse(
                accepted=False,
                message=f"'{affected_inv.check_hint}'은(는) 바이럴 핵심이에요.",
                alternative=self._get_alternative(feedback.affected_domain),
                reason=f"priority={affected_inv.priority}",
                affected_rule_id=affected_inv.rule_id,
            )
        
        return AdaptiveResponse(
            accepted=True,
            message="좋은 아이디어네요! 진행해볼까요?",
            affected_rule_id=affected_inv.rule_id,
        )
    
    def _get_alternative(self, domain: Optional[str]) -> str:
        """도메인별 대안 제시"""
        ALTERNATIVES = {
            "composition": "삼분할 구도나 오프센터도 괜찮아요!",
            "timing": "조금 여유롭게 해도 돼요!",
            "lighting": "측면광이나 자연광도 좋아요!",
            "audio": "자막으로 보완할 수 있어요!",
            "performance": "자연스러운 반응도 좋아요!",
        }
        return ALTERNATIVES.get(domain or "", "다른 방법도 있어요!")
    
    # ==================
    # PUBLIC API
    # ==================
    
    async def process_feedback(self, text: str) -> AdaptiveResponse:
        """
        메인 API: 피드백 처리 (LLM 우선, 폴백 지원)
        """
        logger.info(f"🎤 Processing feedback: {text[:50]}...")
        
        # 1. 피드백 파싱
        feedback = await self.parse_user_feedback_llm(text)
        logger.info(f"   → type={feedback.feedback_type}, domain={feedback.affected_domain}, rule={feedback.affected_rule_id}")
        
        # 2. 응답 생성
        response = await self.generate_response_llm(feedback)
        logger.info(f"   → accepted={response.accepted}, msg={response.message[:30]}")
        
        return response
    
    def process_feedback_sync(self, text: str) -> AdaptiveResponse:
        """
        동기 API: LLM 없이 폴백만 사용
        """
        feedback = self._parse_user_feedback_fallback(text)
        return self._generate_response_fallback(feedback)
