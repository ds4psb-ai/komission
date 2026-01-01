# backend/app/services/vdg_2pass/vdg_unified_pipeline.py
"""
VDG Unified Pipeline Orchestrator

아키텍처:
┌─────────────────────────────────────────────────────────────┐
│  Pass 1: UnifiedPass (Gemini 3.0 Pro)                      │
│  - Hook clip: 10fps (정밀 microbeat)                        │
│  - Full video: 1fps (전체 인과)                             │
│  - 출력: 의미/인과/Plan Seed                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Pass 2: CVMeasurementPass (ffmpeg + OpenCV)               │
│  - 결정론적 측정                                            │
│  - 3개 MVP 메트릭: center_offset, brightness, blur          │
│  - 출력: 수치/좌표                                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Merger: VDG Result                                         │
│  - Semantic + CV 측정값 통합                                │
│  - Deterministic IDs 생성                                   │
│  - Evidence 링크                                            │
└─────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import os
import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from app.schemas.vdg_unified_pass import (
    UnifiedPassLLMOutput,
    AnalysisPointSeedLLM,
    MeasurementSpecLLM,
)
from app.services.vdg_2pass.unified_pass import (
    UnifiedPass,
    UnifiedPassProvenance,
    get_video_duration_ms,
)
from app.services.vdg_2pass.cv_measurement_pass import (
    CVMeasurementPass,
    CVMeasurementResult,
    CVPassProvenance,
    PointMeasurement,
    MetricResult,
)

logger = logging.getLogger(__name__)


# ============================================
# Pipeline Configuration
# ============================================

PIPELINE_VERSION = "vdg_unified_v1.0"


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    # Pass 1 설정
    model_id: Optional[str] = None
    media_resolution: str = "low"
    hook_clip_seconds: float = 4.0
    hook_clip_fps: float = 10.0
    full_video_fps: float = 1.0
    
    # Pass 2 설정
    cv_extraction_fps: float = 10.0
    save_evidence_frames: bool = False
    evidence_output_dir: Optional[str] = None
    
    # 일반 설정
    skip_cv_pass: bool = False  # CV Pass 스킵 (디버깅용)


# ============================================
# Result Types
# ============================================

@dataclass
class AnalysisPointResult:
    """단일 Analysis Point의 통합 결과"""
    ap_id: str  # 결정론적 ID
    t_center_ms: int
    t_window_ms: int
    priority: str
    reason: str
    
    # Pass 1에서
    target_entity_keys: List[str] = field(default_factory=list)
    evidence_note: Optional[str] = None
    
    # Pass 2에서
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    evidence_frame_path: Optional[str] = None


@dataclass
class VDGUnifiedResult:
    """VDG 통합 파이프라인 결과"""
    # 메타데이터
    pipeline_version: str = PIPELINE_VERSION
    run_at: str = ""
    video_path: str = ""
    duration_ms: int = 0
    
    # Pass 1 결과
    llm_output: Optional[UnifiedPassLLMOutput] = None
    llm_provenance: Optional[UnifiedPassProvenance] = None
    
    # Pass 2 결과
    cv_result: Optional[CVMeasurementResult] = None
    cv_provenance: Optional[CVPassProvenance] = None
    
    # 통합 결과
    analysis_points: List[AnalysisPointResult] = field(default_factory=list)
    
    # 타이밍
    total_latency_ms: int = 0
    pass1_latency_ms: int = 0
    pass2_latency_ms: int = 0


# ============================================
# ID Generation
# ============================================

def generate_ap_id(
    t_center_ms: int,
    t_window_ms: int,
    video_hash: str,
) -> str:
    """
    결정론적 Analysis Point ID 생성
    
    형식: ap_{video_hash[:8]}_{t_center_ms}_{t_window_ms}
    """
    return f"ap_{video_hash[:8]}_{t_center_ms}_{t_window_ms}"


def compute_video_hash(video_path: str) -> str:
    """비디오 파일 해시 (첫 1MB만)"""
    hasher = hashlib.sha256()
    with open(video_path, "rb") as f:
        chunk = f.read(1024 * 1024)  # 1MB
        hasher.update(chunk)
    return hasher.hexdigest()


# ============================================
# Main Pipeline Class
# ============================================

class VDGUnifiedPipeline:
    """
    VDG 통합 파이프라인 오케스트레이터
    
    Pass 1 (UnifiedPass) → Pass 2 (CVMeasurementPass) → Merge
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Pass 1 초기화
        self.pass1 = UnifiedPass(
            model_id=self.config.model_id,
            media_resolution=self.config.media_resolution,
            hook_clip_seconds=self.config.hook_clip_seconds,
            hook_clip_fps=self.config.hook_clip_fps,
            full_video_fps=self.config.full_video_fps,
        )
        
        # Pass 2 초기화
        self.pass2 = CVMeasurementPass(
            extraction_fps=self.config.cv_extraction_fps,
            save_evidence_frames=self.config.save_evidence_frames,
            evidence_output_dir=self.config.evidence_output_dir,
        )
    
    def run(
        self,
        *,
        video_path: str,
        platform: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        top_comments: Optional[List[str]] = None,
        duration_ms: Optional[int] = None,
    ) -> VDGUnifiedResult:
        """
        통합 파이프라인 실행
        
        Args:
            video_path: 비디오 파일 경로
            platform: 플랫폼 (tiktok/youtube/instagram)
            caption: 영상 캡션
            hashtags: 해시태그 목록
            top_comments: 상위 댓글 목록
            duration_ms: 비디오 길이 (None이면 자동 추출)
        
        Returns:
            VDGUnifiedResult
        """
        import time
        start_time = time.time()
        
        logger.info(f"🚀 VDG Pipeline starting: {video_path}")
        
        # duration 자동 추출
        if duration_ms is None:
            duration_ms = get_video_duration_ms(video_path)
            if duration_ms == 0:
                duration_ms = 60000  # 기본 60초
        
        # 비디오 해시 (ID 생성용)
        video_hash = compute_video_hash(video_path)
        
        result = VDGUnifiedResult(
            run_at=datetime.now(timezone.utc).isoformat(),
            video_path=video_path,
            duration_ms=duration_ms,
        )
        
        # ============================================
        # Pass 1: UnifiedPass (LLM)
        # ============================================
        pass1_start = time.time()
        
        try:
            llm_output, llm_prov = self.pass1.run(
                video_path=video_path,
                duration_ms=duration_ms,
                platform=platform,
                caption=caption,
                hashtags=hashtags,
                top_comments=top_comments,
            )
            result.llm_output = llm_output
            result.llm_provenance = llm_prov
            result.pass1_latency_ms = int((time.time() - pass1_start) * 1000)
            
            logger.info(
                f"✅ Pass 1 complete: "
                f"analysis_points={len(llm_output.analysis_plan.points)}, "
                f"latency={result.pass1_latency_ms}ms"
            )
        except Exception as e:
            logger.error(f"❌ Pass 1 failed: {e}")
            raise
        
        # ============================================
        # Pass 2: CVMeasurementPass (CV)
        # ============================================
        if not self.config.skip_cv_pass:
            pass2_start = time.time()
            
            logger.info(f"🔬 Pass 2 starting (CV measurement)...")
            
            try:
                cv_result, cv_prov = self.pass2.run(
                    video_path=video_path,
                    analysis_plan=llm_output.analysis_plan,
                )
                result.cv_result = cv_result
                result.cv_provenance = cv_prov
                result.pass2_latency_ms = int((time.time() - pass2_start) * 1000)
                
                logger.info(
                    f"✅ Pass 2 complete: "
                    f"frames={cv_result.total_frames_processed}, "
                    f"latency={result.pass2_latency_ms}ms"
                )
            except Exception as e:
                logger.error(f"❌ Pass 2 failed: {e}")
                # CV 실패해도 LLM 결과는 반환
        
        # ============================================
        # Merge: 통합 결과 생성
        # ============================================
        result.analysis_points = self._merge_results(
            llm_output=result.llm_output,
            cv_result=result.cv_result,
            video_hash=video_hash,
        )
        
        result.total_latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"🏁 VDG Pipeline complete: "
            f"points={len(result.analysis_points)}, "
            f"total_latency={result.total_latency_ms}ms"
        )
        
        return result
    
    def _merge_results(
        self,
        llm_output: UnifiedPassLLMOutput,
        cv_result: Optional[CVMeasurementResult],
        video_hash: str,
    ) -> List[AnalysisPointResult]:
        """Pass 1 + Pass 2 결과 병합"""
        
        merged = []
        
        # CV 결과를 t_center_ms로 인덱싱
        cv_by_time: Dict[int, PointMeasurement] = {}
        if cv_result:
            for pm in cv_result.measurements:
                cv_by_time[pm.t_center_ms] = pm
        
        # 각 analysis point 처리
        for point in llm_output.analysis_plan.points:
            # 결정론적 ID 생성
            ap_id = generate_ap_id(
                t_center_ms=point.t_center_ms,
                t_window_ms=point.t_window_ms,
                video_hash=video_hash,
            )
            
            # CV 측정값 매칭
            cv_point = cv_by_time.get(point.t_center_ms)
            
            merged_point = AnalysisPointResult(
                ap_id=ap_id,
                t_center_ms=point.t_center_ms,
                t_window_ms=point.t_window_ms,
                priority=point.priority,
                reason=point.reason,
                target_entity_keys=point.target_entity_keys,
                evidence_note=point.evidence_note,
                metrics=cv_point.metrics if cv_point else {},
                evidence_frame_path=cv_point.evidence_frame_path if cv_point else None,
            )
            
            merged.append(merged_point)
        
        return merged


# ============================================
# Convenience Functions
# ============================================

def analyze_video(
    video_path: str,
    platform: str = "tiktok",
    caption: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    top_comments: Optional[List[str]] = None,
    config: Optional[PipelineConfig] = None,
) -> VDGUnifiedResult:
    """
    편의 함수: 비디오 분석 실행
    
    Example:
        result = analyze_video(
            video_path="video.mp4",
            platform="tiktok",
            top_comments=["대박", "이거 어케함"]
        )
        
        # LLM 결과
        print(result.llm_output.hook_genome.strength)
        
        # CV 측정값
        for ap in result.analysis_points:
            print(f"{ap.ap_id}: {ap.metrics}")
    """
    pipeline = VDGUnifiedPipeline(config=config)
    return pipeline.run(
        video_path=video_path,
        platform=platform,
        caption=caption,
        hashtags=hashtags,
        top_comments=top_comments,
    )
