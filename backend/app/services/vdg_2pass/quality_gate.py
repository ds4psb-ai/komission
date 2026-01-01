"""
Proof-Grade Quality Gate (P0-1)

VDG 결과 저장 전 자동 검증 + fail-soft

검증 규칙:
1. viral_kicks: high-confidence 2개 이상
2. keyframes: start/peak/end 3개 + 범위/순서 검증
3. comment_evidence_top5: 비어있으면 경고
4. provenance: 필수 필드 존재

사용:
    from app.services.vdg_2pass.quality_gate import proof_grade_gate
    proof_ready, issues = proof_grade_gate.validate(result, video_duration_ms)
"""
from typing import Tuple, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityGateResult:
    """품질 게이트 검증 결과"""
    proof_ready: bool
    issues: List[str]
    high_conf_kicks: int
    total_kicks: int
    evidence_score: float  # 0-1


class ProofGradeGate:
    """VDG 결과 품질 검증 게이트"""
    
    MIN_HIGH_CONF_KICKS = 2  # 최소 high-confidence kick 수
    MIN_KEYFRAMES_PER_KICK = 3  # start/peak/end
    REQUIRED_ROLES = {'start', 'peak', 'end'}
    
    # Provenance 필수 필드
    REQUIRED_PROVENANCE = ['prompt_version', 'model_id', 'schema_version']
    
    def validate(
        self, 
        result, 
        video_duration_ms: int
    ) -> Tuple[bool, List[str]]:
        """
        VDG 결과 검증
        
        Args:
            result: VDGUnifiedResult 또는 dict
            video_duration_ms: 영상 길이 (ms)
            
        Returns:
            (proof_ready: bool, issues: List[str])
        """
        issues = []
        high_conf_kicks = 0
        total_kicks = 0
        
        # Dict 지원 (flexibility)
        if isinstance(result, dict):
            provenance = result.get('provenance', {})
            kicks = provenance.get('viral_kicks', []) if provenance else []
            comment_evidence = provenance.get('comment_evidence_top5', []) if provenance else []
            meta = result.get('meta', {})
        else:
            provenance = result.provenance
            kicks = provenance.viral_kicks if provenance else []
            comment_evidence = provenance.comment_evidence_top5 if provenance else []
            meta = result.meta
        
        total_kicks = len(kicks)
        
        # 1. viral_kicks 품질 검증
        for kick in kicks:
            kick_issues = self._validate_kick(kick, video_duration_ms)
            if kick_issues:
                issues.extend(kick_issues)
            elif self._is_high_confidence(kick):
                high_conf_kicks += 1
        
        if high_conf_kicks < self.MIN_HIGH_CONF_KICKS:
            issues.append(
                f"high_conf_kicks={high_conf_kicks} < {self.MIN_HIGH_CONF_KICKS} required"
            )
        
        # 2. comment_evidence 검증
        if not comment_evidence:
            issues.append("comment_evidence_top5 is empty (proof pending)")
        
        # 3. provenance 완전성
        prov_issues = self._validate_provenance(meta)
        issues.extend(prov_issues)
        
        # 결과 판정
        proof_ready = len(issues) == 0
        
        # 로깅
        if proof_ready:
            logger.info(f"✅ Quality Gate PASSED: {high_conf_kicks}/{total_kicks} high-conf kicks")
        else:
            logger.warning(f"⚠️ Quality Gate FAILED: {len(issues)} issues - {issues[:3]}")
        
        return proof_ready, issues
    
    def validate_full(
        self, 
        result, 
        video_duration_ms: int
    ) -> QualityGateResult:
        """확장된 결과 반환"""
        proof_ready, issues = self.validate(result, video_duration_ms)
        
        # Dict 지원
        if isinstance(result, dict):
            provenance = result.get('provenance', {})
            kicks = provenance.get('viral_kicks', []) if provenance else []
        else:
            kicks = result.provenance.viral_kicks if result.provenance else []
        
        high_conf = sum(1 for k in kicks if self._is_high_confidence(k))
        total = len(kicks)
        
        # Evidence score 계산
        evidence_score = self._calculate_evidence_score(result)
        
        return QualityGateResult(
            proof_ready=proof_ready,
            issues=issues,
            high_conf_kicks=high_conf,
            total_kicks=total,
            evidence_score=evidence_score
        )
    
    def _validate_kick(self, kick, duration_ms: int) -> List[str]:
        """개별 kick 검증"""
        issues = []
        
        # Dict 지원
        if isinstance(kick, dict):
            kick_index = kick.get('kick_index', 0)
            keyframes = kick.get('keyframes', [])
            comment_refs = kick.get('comment_evidence_refs', [])
        else:
            kick_index = kick.kick_index
            keyframes = kick.keyframes or []
            comment_refs = getattr(kick, 'comment_evidence_refs', []) or []
        
        prefix = f"kick_{kick_index}"
        
        # keyframes 존재 검증
        if len(keyframes) < self.MIN_KEYFRAMES_PER_KICK:
            issues.append(f"{prefix}: keyframes={len(keyframes)} < 3 required")
            return issues  # 더 이상 검증 불가
        
        # role 검증 (start/peak/end)
        if isinstance(keyframes[0], dict):
            roles = {kf.get('role') for kf in keyframes}
            sorted_kfs = sorted(keyframes, key=lambda x: x.get('t_ms', 0))
        else:
            roles = {kf.role for kf in keyframes}
            sorted_kfs = sorted(keyframes, key=lambda x: x.t_ms)
        
        missing_roles = self.REQUIRED_ROLES - roles
        if missing_roles:
            issues.append(f"{prefix}: missing roles {missing_roles}")
        
        # t_ms 범위 검증
        for kf in sorted_kfs:
            t_ms = kf.get('t_ms', 0) if isinstance(kf, dict) else kf.t_ms
            if not (0 <= t_ms <= duration_ms):
                issues.append(f"{prefix}: t_ms={t_ms} out of range [0, {duration_ms}]")
        
        # 순서 검증 (start < peak < end)
        role_times = {}
        for kf in sorted_kfs:
            if isinstance(kf, dict):
                role_times[kf.get('role')] = kf.get('t_ms', 0)
            else:
                role_times[kf.role] = kf.t_ms
        
        if all(r in role_times for r in ['start', 'peak', 'end']):
            if not (role_times['start'] < role_times['peak'] < role_times['end']):
                issues.append(f"{prefix}: keyframe order invalid (start < peak < end)")
        
        return issues
    
    def _is_high_confidence(self, kick) -> bool:
        """High-confidence kick 판정"""
        if isinstance(kick, dict):
            keyframes = kick.get('keyframes', [])
            comment_refs = kick.get('comment_evidence_refs', [])
            confidence = kick.get('confidence', 0.5)
        else:
            keyframes = kick.keyframes or []
            comment_refs = getattr(kick, 'comment_evidence_refs', []) or []
            confidence = getattr(kick, 'confidence', 0.5)
        
        has_all_keyframes = len(keyframes) >= 3
        has_evidence = bool(comment_refs)
        has_good_confidence = confidence >= 0.6
        
        return has_all_keyframes and (has_evidence or has_good_confidence)
    
    def _validate_provenance(self, meta) -> List[str]:
        """Provenance 필수 필드 검증"""
        issues = []
        
        if not meta:
            issues.append("meta block missing")
            return issues
        
        for field in self.REQUIRED_PROVENANCE:
            if isinstance(meta, dict):
                value = meta.get(field)
            else:
                value = getattr(meta, field, None)
            
            if not value:
                issues.append(f"meta.{field} missing")
        
        return issues
    
    def _calculate_evidence_score(self, result) -> float:
        """Evidence 완성도 점수 (0-1)"""
        scores = []
        
        # Dict 지원
        if isinstance(result, dict):
            provenance = result.get('provenance', {})
            kicks = provenance.get('viral_kicks', []) if provenance else []
            comments = provenance.get('comment_evidence_top5', []) if provenance else []
        else:
            kicks = result.provenance.viral_kicks if result.provenance else []
            comments = result.provenance.comment_evidence_top5 if result.provenance else []
        
        # Comment evidence score (20%)
        comment_score = min(len(comments) / 5, 1.0) * 0.2
        scores.append(comment_score)
        
        # Kick evidence score (80%)
        if kicks:
            kick_scores = []
            for kick in kicks:
                if isinstance(kick, dict):
                    kfs = kick.get('keyframes', [])
                    refs = kick.get('comment_evidence_refs', [])
                else:
                    kfs = kick.keyframes or []
                    refs = getattr(kick, 'comment_evidence_refs', []) or []
                
                kf_score = min(len(kfs) / 3, 1.0) * 0.6
                ref_score = min(len(refs) / 2, 1.0) * 0.4
                kick_scores.append(kf_score + ref_score)
            
            avg_kick_score = sum(kick_scores) / len(kick_scores) if kick_scores else 0
            scores.append(avg_kick_score * 0.8)
        
        return round(sum(scores), 3)


# Singleton instance
proof_grade_gate = ProofGradeGate()
