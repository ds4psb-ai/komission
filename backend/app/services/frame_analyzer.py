"""
Frame Analyzer for Real-time Video Coaching

Gemini Vision API를 사용하여 실시간 프레임 분석 수행.
1fps 프레임에서 구도, 밝기, 안정성 등을 평가하여 DNAInvariant 규칙 준수 여부 판단.

Usage:
    analyzer = FrameAnalyzer(api_key)
    compliance = await analyzer.analyze_frame(frame_base64, rules)
"""
import asyncio
import base64
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Gemini 2.5 Flash Vision 모델 (비용 효율적)
VISION_MODEL = "gemini-2.5-flash"


@dataclass
class FrameAnalysisResult:
    """프레임 분석 결과"""
    rule_id: str
    is_compliant: bool
    confidence: float  # 0.0 ~ 1.0
    message: Optional[str] = None  # 위반 시 피드백 메시지
    measured_value: Optional[float] = None  # 측정된 값


class FrameAnalyzer:
    """
    실시간 프레임 분석기 (Gemini Vision)
    
    1fps 프레임을 분석하여 DNAInvariant 규칙 준수 여부를 판단합니다.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (없으면 환경변수에서 로드)
        """
        import os
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            logger.warning("google-genai not installed, using mock client")
            self.client = None
        
        self.model = VISION_MODEL
        self._last_analysis_time = 0
        self._min_interval_sec = 1.0  # 최소 분석 간격 (1fps)
    
    async def analyze_frame(
        self,
        frame_base64: str,
        rules: List[Any],  # List[DNAInvariant]
        current_time: float = 0.0
    ) -> Dict[str, FrameAnalysisResult]:
        """
        프레임 분석 → 규칙 준수 여부 판단
        
        Args:
            frame_base64: Base64 인코딩된 프레임 이미지 (JPEG/PNG)
            rules: 평가할 DNAInvariant 규칙 목록
            current_time: 현재 영상 시간 (초)
        
        Returns:
            {rule_id: FrameAnalysisResult} 형태의 딕셔너리
        """
        import time
        
        # Rate limiting (1fps)
        now = time.time()
        if now - self._last_analysis_time < self._min_interval_sec:
            logger.debug("Skipping frame analysis (rate limited)")
            return {}
        self._last_analysis_time = now
        
        if not self.client:
            logger.warning("Vision client not available, returning mock results")
            return self._mock_analysis(rules)
        
        try:
            # 구도/밝기/안정성 관련 규칙만 필터링
            visual_rules = [r for r in rules if self._is_visual_rule(r)]
            
            if not visual_rules:
                return {}
            
            prompt = self._build_analysis_prompt(visual_rules)
            
            # Gemini Vision API 호출
            response = await asyncio.to_thread(
                self._call_vision_api,
                frame_base64,
                prompt
            )
            
            results = self._parse_response(response, visual_rules)
            logger.info(f"Frame analysis complete: {len(results)} rules evaluated at t={current_time:.1f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return {}
    
    def _is_visual_rule(self, rule: Any) -> bool:
        """규칙이 시각적 분석이 필요한지 확인"""
        if not hasattr(rule, 'domain'):
            return False
        
        # composition, lighting 관련 규칙만 시각 분석
        if rule.domain in ["composition", "safety"]:
            return True
        
        # metric_id로 판단
        if hasattr(rule, 'spec') and rule.spec:
            metric_id = rule.spec.metric_id if hasattr(rule.spec, 'metric_id') else ""
            visual_metrics = ["cmp.", "lit.", "stb.", "center", "brightness", "stability"]
            return any(m in metric_id for m in visual_metrics)
        
        return False
    
    def _build_analysis_prompt(self, rules: List[Any]) -> str:
        """규칙 기반 분석 프롬프트 생성"""
        prompt = """You are a video coaching assistant analyzing a single frame.
        
Evaluate the following visual rules and respond in JSON format:

Rules to evaluate:
"""
        for rule in rules:
            metric_id = rule.spec.metric_id if hasattr(rule.spec, 'metric_id') else "unknown"
            target = rule.spec.target if hasattr(rule.spec, 'target') else None
            prompt += f"\n- {rule.rule_id}: {rule.check_hint or metric_id}"
            if target:
                prompt += f" (target: {target})"
        
        prompt += """

For each rule, respond with:
{
    "rule_id": {
        "compliant": true/false,
        "confidence": 0.0-1.0,
        "measured_value": number or null,
        "feedback": "brief Korean feedback if not compliant"
    }
}

Important:
- center_offset: 0.0 = perfect center, 1.0 = edge
- brightness: 0.0 = dark, 1.0 = bright
- stability: inferred from blur/motion (1.0 = stable)

Respond ONLY with valid JSON, no markdown or explanation."""
        
        return prompt
    
    def _call_vision_api(self, frame_base64: str, prompt: str) -> str:
        """동기 Vision API 호출 (별도 스레드에서 실행)"""
        try:
            # 이미지 데이터 준비
            image_data = base64.b64decode(frame_base64)
            
            # Gemini Vision API 호출
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part(text=prompt),
                            types.Part(inline_data=types.Blob(
                                mime_type="image/jpeg",
                                data=image_data
                            ))
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # 낮은 온도로 일관된 분석
                    max_output_tokens=500
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Vision API call failed: {e}")
            raise
    
    def _parse_response(
        self,
        response_text: str,
        rules: List[Any]
    ) -> Dict[str, FrameAnalysisResult]:
        """API 응답 파싱 → FrameAnalysisResult"""
        import json
        
        results = {}
        
        try:
            # JSON 파싱 (코드블록 제거)
            text = response_text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            data = json.loads(text)
            
            for rule in rules:
                rule_id = rule.rule_id
                if rule_id in data:
                    item = data[rule_id]
                    results[rule_id] = FrameAnalysisResult(
                        rule_id=rule_id,
                        is_compliant=item.get("compliant", True),
                        confidence=item.get("confidence", 0.5),
                        message=item.get("feedback"),
                        measured_value=item.get("measured_value")
                    )
                else:
                    # 응답에 없으면 준수로 간주
                    results[rule_id] = FrameAnalysisResult(
                        rule_id=rule_id,
                        is_compliant=True,
                        confidence=0.3
                    )
                    
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Vision response: {e}")
            # 파싱 실패 시 모든 규칙 준수로 간주
            for rule in rules:
                results[rule.rule_id] = FrameAnalysisResult(
                    rule_id=rule.rule_id,
                    is_compliant=True,
                    confidence=0.1
                )
        
        return results
    
    def _mock_analysis(self, rules: List[Any]) -> Dict[str, FrameAnalysisResult]:
        """테스트용 Mock 분석 결과"""
        import random
        
        results = {}
        for rule in rules:
            if self._is_visual_rule(rule):
                # 80% 확률로 준수
                is_compliant = random.random() > 0.2
                results[rule.rule_id] = FrameAnalysisResult(
                    rule_id=rule.rule_id,
                    is_compliant=is_compliant,
                    confidence=0.7,
                    message=None if is_compliant else "구도를 조정해주세요",
                    measured_value=random.uniform(0.2, 0.8)
                )
        
        return results


# Singleton instance for reuse
_frame_analyzer: Optional[FrameAnalyzer] = None


def get_frame_analyzer(api_key: Optional[str] = None) -> FrameAnalyzer:
    """싱글톤 FrameAnalyzer 인스턴스 반환"""
    global _frame_analyzer
    if _frame_analyzer is None:
        _frame_analyzer = FrameAnalyzer(api_key)
    return _frame_analyzer
