"""
VDG v4.0 2-Pass Pipeline Module.

P0 Components:
- quality_gate: VDG 품질 검증
- keyframe_verifier: CV 기반 keyframe 검증
- evidence_clip_generator: 댓글 기반 클립 생성

P1 Components:
- vdg_db_saver: VDG → DB 정규화 저장
- cluster_test: 클러스터링 테스트
"""

from app.services.vdg_2pass.quality_gate import proof_grade_gate, ProofGradeGate
from app.services.vdg_2pass.keyframe_verifier import keyframe_verifier, KeyframeVerifier, CV2_AVAILABLE
from app.services.vdg_2pass.evidence_clip_generator import evidence_clip_generator, EvidenceGuidedClipGenerator
from app.services.vdg_2pass.vdg_db_saver import vdg_db_saver, VDGDatabaseSaver
from app.services.vdg_2pass.cluster_test import cluster_test_service, ClusterTestService

__all__ = [
    # P0
    "proof_grade_gate",
    "ProofGradeGate",
    "keyframe_verifier",
    "KeyframeVerifier",
    "CV2_AVAILABLE",
    "evidence_clip_generator",
    "EvidenceGuidedClipGenerator",
    # P1
    "vdg_db_saver",
    "VDGDatabaseSaver",
    "cluster_test_service",
    "ClusterTestService",
]
