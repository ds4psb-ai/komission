"""
VDG Quality Validator

remix_suggestions 및 기타 VDG 출력의 품질을 자동 검증

품질 기준:
- remix_suggestions: 최소 2개, variable_elements 최소 2개, invariant 명시
- capsule_brief: hook_script 필수, shotlist 최소 1개
- product_placement_guide: 체험단 콘텐츠면 필수
"""
import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityResult:
    """품질 검증 결과"""
    is_valid: bool
    score: float  # 0.0 ~ 1.0
    issues: List[str]
    suggestions: List[str]


class VDGQualityValidator:
    """
    VDG 출력 품질 검증기
    
    검증 항목:
    1. remix_suggestions 품질
    2. capsule_brief 완성도
    3. product_placement_guide 유무 (체험단용)
    4. hook_genome 완성도
    """
    
    # 최소 품질 기준
    MIN_REMIX_SUGGESTIONS = 2
    MIN_VARIABLE_ELEMENTS = 2
    MIN_SHOTLIST_ITEMS = 1
    
    def validate_vdg(self, vdg_data: Dict[str, Any]) -> QualityResult:
        """
        전체 VDG 품질 검증
        
        Returns:
            QualityResult with overall score and issues
        """
        issues = []
        suggestions = []
        scores = []
        
        # 1. remix_suggestions 검증
        remix_result = self._validate_remix_suggestions(
            vdg_data.get("remix_suggestions", [])
        )
        issues.extend(remix_result["issues"])
        suggestions.extend(remix_result["suggestions"])
        scores.append(remix_result["score"])
        
        # 2. capsule_brief 검증
        capsule_result = self._validate_capsule_brief(
            vdg_data.get("capsule_brief", {})
        )
        issues.extend(capsule_result["issues"])
        suggestions.extend(capsule_result["suggestions"])
        scores.append(capsule_result["score"])
        
        # 3. hook_genome 검증
        hook_result = self._validate_hook_genome(
            vdg_data.get("hook_genome", {})
        )
        issues.extend(hook_result["issues"])
        scores.append(hook_result["score"])
        
        # 전체 점수 계산 (가중 평균)
        weights = [0.4, 0.3, 0.3]  # remix, capsule, hook
        overall_score = sum(s * w for s, w in zip(scores, weights))
        
        is_valid = overall_score >= 0.6 and len([i for i in issues if "CRITICAL" in i]) == 0
        
        return QualityResult(
            is_valid=is_valid,
            score=round(overall_score, 2),
            issues=issues,
            suggestions=suggestions
        )
    
    def _validate_remix_suggestions(self, suggestions: List[Dict]) -> Dict:
        """
        remix_suggestions 품질 검증
        
        필수 조건:
        - 최소 2개 제안
        - 각 제안에 variable_elements 최소 2개
        - viral_element_to_keep 명시 (불변 요소)
        - target_niche가 구체적 (5자 이상)
        - concept이 실용적 (20자 이상)
        """
        issues = []
        score = 1.0
        
        # 개수 체크
        if len(suggestions) < self.MIN_REMIX_SUGGESTIONS:
            issues.append(f"CRITICAL: remix_suggestions {len(suggestions)}개 < 최소 {self.MIN_REMIX_SUGGESTIONS}개")
            score -= 0.4
        
        valid_suggestions = 0
        for i, sugg in enumerate(suggestions):
            sugg_issues = []
            
            # variable_elements 체크
            var_elements = sugg.get("variable_elements", [])
            if len(var_elements) < self.MIN_VARIABLE_ELEMENTS:
                sugg_issues.append(f"variable_elements {len(var_elements)}개 < {self.MIN_VARIABLE_ELEMENTS}개")
            
            # viral_element_to_keep (불변 요소) 체크
            viral_keep = sugg.get("viral_element_to_keep", "")
            if not viral_keep or len(viral_keep) < 5:
                sugg_issues.append("viral_element_to_keep 누락/불충분")
            
            # target_niche 구체성 체크
            niche = sugg.get("target_niche", "")
            if not niche or len(niche) < 5:
                sugg_issues.append("target_niche 불충분")
            
            # concept 실용성 체크
            concept = sugg.get("concept", "")
            if not concept or len(concept) < 20:
                sugg_issues.append("concept 불충분 (20자 미만)")
            
            if sugg_issues:
                issues.append(f"remix_suggestions[{i}]: {', '.join(sugg_issues)}")
                score -= 0.1
            else:
                valid_suggestions += 1
        
        # 품질 좋은 제안 비율 반영
        if len(suggestions) > 0:
            quality_ratio = valid_suggestions / len(suggestions)
            score = max(0, min(1, score * quality_ratio + 0.3))
        
        suggestions_tips = []
        if score < 0.7:
            suggestions_tips.append("remix_suggestions에 구체적인 타겟/컨셉/변수 요소 추가 필요")
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions_tips
        }
    
    def _validate_capsule_brief(self, capsule: Dict) -> Dict:
        """
        capsule_brief 품질 검증
        
        필수 조건:
        - hook_script 존재 및 10자 이상
        - shotlist 최소 1개
        - product_placement_guide 존재 (체험단용)
        """
        issues = []
        suggestions = []
        score = 1.0
        
        # hook_script 체크
        hook_script = capsule.get("hook_script", "")
        if not hook_script or len(hook_script) < 10:
            issues.append("capsule_brief.hook_script 누락/불충분")
            score -= 0.3
        
        # shotlist 체크
        shotlist = capsule.get("shotlist", [])
        if len(shotlist) < self.MIN_SHOTLIST_ITEMS:
            issues.append(f"capsule_brief.shotlist {len(shotlist)}개 < 최소 {self.MIN_SHOTLIST_ITEMS}개")
            score -= 0.2
        
        # product_placement_guide 체크
        ppg = capsule.get("product_placement_guide", {})
        if not ppg or not ppg.get("recommended_timing"):
            issues.append("product_placement_guide 누락 (체험단 변주 가이드 없음)")
            suggestions.append("체험단 제품 배치 가이드 추가 권장")
            score -= 0.2
        else:
            # guide 품질 체크
            if len(ppg.get("invariant_elements", [])) < 1:
                issues.append("product_placement_guide.invariant_elements 누락")
                score -= 0.1
            if len(ppg.get("variable_elements", [])) < 1:
                issues.append("product_placement_guide.variable_elements 누락")
                score -= 0.1
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions
        }
    
    def _validate_hook_genome(self, hook: Dict) -> Dict:
        """
        hook_genome 품질 검증
        """
        issues = []
        score = 1.0
        
        # 필수 필드
        if not hook.get("pattern"):
            issues.append("hook_genome.pattern 누락")
            score -= 0.2
        
        if not hook.get("hook_summary") or len(hook.get("hook_summary", "")) < 5:
            issues.append("hook_genome.hook_summary 불충분")
            score -= 0.2
        
        # microbeats 체크
        microbeats = hook.get("microbeats", [])
        if len(microbeats) < 2:
            issues.append(f"hook_genome.microbeats {len(microbeats)}개 < 2개")
            score -= 0.2
        
        # virality_analysis 체크
        virality = hook.get("virality_analysis", {})
        if not virality.get("curiosity_gap"):
            issues.append("virality_analysis.curiosity_gap 누락")
            score -= 0.1
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": []
        }


# 싱글톤 인스턴스
vdg_validator = VDGQualityValidator()


def validate_vdg_quality(vdg_data: Dict[str, Any]) -> QualityResult:
    """편의 함수: VDG 품질 검증"""
    return vdg_validator.validate_vdg(vdg_data)


def is_vdg_quality_sufficient(vdg_data: Dict[str, Any], min_score: float = 0.6) -> bool:
    """편의 함수: VDG 품질이 최소 기준 이상인지"""
    result = vdg_validator.validate_vdg(vdg_data)
    return result.score >= min_score
