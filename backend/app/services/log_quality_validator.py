"""
Log Quality Validator

P1 로그 품질 검증 로직:
1. intervention-outcome 조인율 (목표: 100%)
2. compliance_unknown_reason 누락률 (목표: < 15%)
3. control group 비율 (목표: ~10%)

로드맵 P1 검증 체크리스트 자동화
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from app.services.session_logger import get_session_logger
from app.schemas.session_events import SessionEventSummary

logger = logging.getLogger(__name__)


class QualityStatus(str, Enum):
    """Quality check status."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class QualityCheck:
    """Single quality check result."""
    name: str
    status: QualityStatus
    actual_value: float
    threshold: float
    description: str
    recommendation: Optional[str] = None


@dataclass
class LogQualityReport:
    """Complete log quality report."""
    total_sessions: int
    checks: List[QualityCheck]
    overall_status: QualityStatus
    is_ready_for_flywheel: bool
    summary: str


# ====================
# QUALITY THRESHOLDS (P1 Roadmap)
# ====================

class QualityThresholds:
    """P1 quality thresholds from roadmap."""
    
    # intervention_id로 intervention ↔ outcome 조인 100%
    INTERVENTION_OUTCOME_JOIN_RATE_MIN = 0.95  # 95% minimum, 100% ideal
    
    # compliance_unknown_reason 누락률 < 5%
    COMPLIANCE_UNKNOWN_RATE_MAX = 0.15  # 15% maximum
    
    # Control group 비율 ~10%
    CONTROL_RATIO_MIN = 0.08  # 8% minimum
    CONTROL_RATIO_MAX = 0.12  # 12% maximum
    
    # upload_outcome_proxy 입력률 > 30%
    UPLOAD_OUTCOME_RATE_MIN = 0.30  # 30% minimum
    
    # Negative evidence 비율 < 20%
    NEGATIVE_EVIDENCE_RATE_MAX = 0.20  # 20% maximum
    
    # 최소 세션 수 (통계적 유의성)
    MIN_SESSIONS_FOR_VALIDATION = 10


class LogQualityValidator:
    """
    Validates log quality against P1 roadmap criteria.
    
    Usage:
        validator = LogQualityValidator()
        report = validator.validate_all_sessions()
        
        if report.is_ready_for_flywheel:
            print("✅ Ready for DistillRun!")
        else:
            print("❌ Fix issues before proceeding")
            for check in report.checks:
                if check.status != QualityStatus.PASS:
                    print(f"  - {check.name}: {check.recommendation}")
    """
    
    def __init__(self, session_logger=None):
        """Initialize with optional session logger."""
        self._logger = session_logger or get_session_logger()
    
    def validate_all_sessions(self) -> LogQualityReport:
        """
        Run all quality checks on logged sessions.
        
        Returns:
            LogQualityReport with all check results
        """
        stats = self._logger.get_all_sessions_summary()
        total_sessions = stats.get("total_sessions", 0)
        
        checks = []
        
        # Check 1: Intervention-Outcome Join Rate
        checks.append(self._check_join_rate(stats))
        
        # Check 2: Compliance Unknown Rate
        checks.append(self._check_unknown_rate(stats))
        
        # Check 3: Control Group Ratio
        checks.append(self._check_control_ratio(stats))
        
        # Check 4: Minimum Sessions
        checks.append(self._check_min_sessions(total_sessions))
        
        # Determine overall status
        overall_status = self._calculate_overall_status(checks)
        is_ready = overall_status != QualityStatus.FAIL and total_sessions >= QualityThresholds.MIN_SESSIONS_FOR_VALIDATION
        
        summary = self._generate_summary(checks, total_sessions, is_ready)
        
        return LogQualityReport(
            total_sessions=total_sessions,
            checks=checks,
            overall_status=overall_status,
            is_ready_for_flywheel=is_ready,
            summary=summary
        )
    
    def validate_session(self, session_id: str) -> List[QualityCheck]:
        """
        Validate a single session's log quality.
        
        Returns:
            List of quality checks for this session
        """
        summary = self._logger.get_session_summary(session_id)
        if not summary:
            return [QualityCheck(
                name="session_exists",
                status=QualityStatus.FAIL,
                actual_value=0,
                threshold=1,
                description="Session not found",
                recommendation="Verify session ID is correct"
            )]
        
        checks = []
        
        # Check join rate for this session
        join_rate = summary.intervention_outcome_join_rate
        checks.append(QualityCheck(
            name="intervention_outcome_join",
            status=self._get_status(join_rate, QualityThresholds.INTERVENTION_OUTCOME_JOIN_RATE_MIN, higher_is_better=True),
            actual_value=join_rate,
            threshold=QualityThresholds.INTERVENTION_OUTCOME_JOIN_RATE_MIN,
            description=f"Intervention-outcome join rate: {join_rate:.1%}",
            recommendation="Ensure every intervention has a corresponding outcome logged" if join_rate < 0.95 else None
        ))
        
        # Check unknown rate
        unknown_rate = summary.compliance_unknown_rate
        checks.append(QualityCheck(
            name="compliance_unknown",
            status=self._get_status(unknown_rate, QualityThresholds.COMPLIANCE_UNKNOWN_RATE_MAX, higher_is_better=False),
            actual_value=unknown_rate,
            threshold=QualityThresholds.COMPLIANCE_UNKNOWN_RATE_MAX,
            description=f"Compliance unknown rate: {unknown_rate:.1%}",
            recommendation="Add compliance_unknown_reason for unmeasured outcomes" if unknown_rate > 0.15 else None
        ))
        
        # Check negative evidence rate
        neg_rate = summary.negative_evidence_rate
        checks.append(QualityCheck(
            name="negative_evidence",
            status=self._get_status(neg_rate, QualityThresholds.NEGATIVE_EVIDENCE_RATE_MAX, higher_is_better=False),
            actual_value=neg_rate,
            threshold=QualityThresholds.NEGATIVE_EVIDENCE_RATE_MAX,
            description=f"Negative evidence rate: {neg_rate:.1%}",
            recommendation="Review rules causing negative outcomes" if neg_rate > 0.20 else None
        ))
        
        return checks
    
    # ====================
    # INDIVIDUAL CHECKS
    # ====================
    
    def _check_join_rate(self, stats: dict) -> QualityCheck:
        """Check intervention-outcome join rate."""
        rate = stats.get("avg_intervention_outcome_join_rate", 0)
        
        if rate >= QualityThresholds.INTERVENTION_OUTCOME_JOIN_RATE_MIN:
            status = QualityStatus.PASS
            recommendation = None
        elif rate >= 0.80:
            status = QualityStatus.WARN
            recommendation = "Some interventions missing outcomes. Check frontend logging."
        else:
            status = QualityStatus.FAIL
            recommendation = "Critical: Most interventions have no outcome. Verify outcome logging flow."
        
        return QualityCheck(
            name="intervention_outcome_join_rate",
            status=status,
            actual_value=rate,
            threshold=QualityThresholds.INTERVENTION_OUTCOME_JOIN_RATE_MIN,
            description=f"Average join rate: {rate:.1%} (target: ≥95%)",
            recommendation=recommendation
        )
    
    def _check_unknown_rate(self, stats: dict) -> QualityCheck:
        """Check compliance unknown rate."""
        rate = stats.get("avg_compliance_unknown_rate", 0)
        
        if rate <= QualityThresholds.COMPLIANCE_UNKNOWN_RATE_MAX:
            status = QualityStatus.PASS
            recommendation = None
        elif rate <= 0.25:
            status = QualityStatus.WARN
            recommendation = "Unknown rate slightly high. Add compliance_unknown_reason for edge cases."
        else:
            status = QualityStatus.FAIL
            recommendation = "Too many unknowns. Improve compliance detection or add reasons."
        
        return QualityCheck(
            name="compliance_unknown_rate",
            status=status,
            actual_value=rate,
            threshold=QualityThresholds.COMPLIANCE_UNKNOWN_RATE_MAX,
            description=f"Unknown rate: {rate:.1%} (target: ≤15%)",
            recommendation=recommendation
        )
    
    def _check_control_ratio(self, stats: dict) -> QualityCheck:
        """Check control group ratio."""
        ratio = stats.get("control_ratio", 0)
        
        if QualityThresholds.CONTROL_RATIO_MIN <= ratio <= QualityThresholds.CONTROL_RATIO_MAX:
            status = QualityStatus.PASS
            recommendation = None
        elif ratio < QualityThresholds.CONTROL_RATIO_MIN:
            status = QualityStatus.WARN
            recommendation = f"Control ratio low ({ratio:.1%}). Check CoachingRouter assignment."
        else:
            status = QualityStatus.WARN
            recommendation = f"Control ratio high ({ratio:.1%}). May be too many sessions without coaching."
        
        return QualityCheck(
            name="control_group_ratio",
            status=status,
            actual_value=ratio,
            threshold=0.10,  # Target 10%
            description=f"Control ratio: {ratio:.1%} (target: 8-12%)",
            recommendation=recommendation
        )
    
    def _check_min_sessions(self, total: int) -> QualityCheck:
        """Check minimum session count for statistical validity."""
        threshold = QualityThresholds.MIN_SESSIONS_FOR_VALIDATION
        
        if total >= threshold:
            status = QualityStatus.PASS
            recommendation = None
        elif total >= threshold // 2:
            status = QualityStatus.WARN
            recommendation = f"Need more sessions ({total}/{threshold}) for reliable validation."
        else:
            status = QualityStatus.FAIL
            recommendation = f"Insufficient sessions ({total}/{threshold}). Run more coaching sessions."
        
        return QualityCheck(
            name="minimum_sessions",
            status=status,
            actual_value=float(total),
            threshold=float(threshold),
            description=f"Sessions: {total} (minimum: {threshold})",
            recommendation=recommendation
        )
    
    # ====================
    # HELPERS
    # ====================
    
    def _get_status(self, value: float, threshold: float, higher_is_better: bool) -> QualityStatus:
        """Determine status based on value vs threshold."""
        if higher_is_better:
            if value >= threshold:
                return QualityStatus.PASS
            elif value >= threshold * 0.8:
                return QualityStatus.WARN
            else:
                return QualityStatus.FAIL
        else:
            if value <= threshold:
                return QualityStatus.PASS
            elif value <= threshold * 1.5:
                return QualityStatus.WARN
            else:
                return QualityStatus.FAIL
    
    def _calculate_overall_status(self, checks: List[QualityCheck]) -> QualityStatus:
        """Calculate overall status from check results."""
        if any(c.status == QualityStatus.FAIL for c in checks):
            return QualityStatus.FAIL
        if any(c.status == QualityStatus.WARN for c in checks):
            return QualityStatus.WARN
        return QualityStatus.PASS
    
    def _generate_summary(self, checks: List[QualityCheck], total: int, is_ready: bool) -> str:
        """Generate human-readable summary."""
        passed = sum(1 for c in checks if c.status == QualityStatus.PASS)
        warned = sum(1 for c in checks if c.status == QualityStatus.WARN)
        failed = sum(1 for c in checks if c.status == QualityStatus.FAIL)
        
        status_emoji = "✅" if is_ready else "❌"
        
        lines = [
            f"{status_emoji} Log Quality Report ({total} sessions)",
            f"  Pass: {passed}, Warn: {warned}, Fail: {failed}",
        ]
        
        if is_ready:
            lines.append("  → Ready for DistillRun!")
        else:
            lines.append("  → Fix issues before proceeding")
            for c in checks:
                if c.status == QualityStatus.FAIL:
                    lines.append(f"    ❌ {c.name}: {c.recommendation}")
                elif c.status == QualityStatus.WARN:
                    lines.append(f"    ⚠️ {c.name}: {c.recommendation}")
        
        return "\n".join(lines)


# Singleton
_validator_instance = None


def get_log_quality_validator() -> LogQualityValidator:
    """Get singleton LogQualityValidator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = LogQualityValidator()
    return _validator_instance
