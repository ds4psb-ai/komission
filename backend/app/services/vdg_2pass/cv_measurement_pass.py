# backend/app/services/vdg_2pass/cv_measurement_pass.py
"""
VDG CV Measurement Pass (Pass 2: 결정론적 측정)

설계 원칙:
- Pass 1 (LLM): 의미/인과/측정설계(Plan Seed) 생성
- Pass 2 (CV): 수치/좌표/결정론적 측정 수행

핵심 특징:
- 동일 입력 = 동일 출력 (100% 재현 가능)
- ffmpeg + OpenCV 기반
- 3개 MVP 메트릭: center_offset, brightness, blur
"""
from __future__ import annotations

import os
import logging
import tempfile
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import cv2
import numpy as np

from app.schemas.vdg_unified_pass import (
    AnalysisPlanSeedLLM,
    AnalysisPointSeedLLM,
    MeasurementSpecLLM,
)

logger = logging.getLogger(__name__)


# ============================================
# Configuration
# ============================================

CV_PASS_VERSION = "cv_measurement_v2.0"

# 지원 메트릭 (MVP: 3개 + 확장: 3개)
SUPPORTED_CV_METRICS = {
    # MVP (v1.0)
    "cmp.center_offset_xy.v1",
    "lit.brightness_ratio.v1",
    "cmp.blur_score.v1",
    # 확장 (v2.0)
    "edit.scene_change.v1",       # 씬 전환 감지
    "cmp.face_bbox.v1",           # 얼굴 바운딩 박스 (구도)
    "txt.text_density.v1",        # 텍스트 밀도 (자막 타이밍)
}


# ============================================
# Result Types
# ============================================

@dataclass
class MetricResult:
    """단일 메트릭 측정 결과"""
    metric_id: str
    value: Any  # float, List[float], Dict, etc.
    confidence: float = 1.0  # 측정 신뢰도 (0-1)
    roi: str = "full_frame"
    aggregation: str = "mean"
    frame_count: int = 0
    note: Optional[str] = None


@dataclass
class PointMeasurement:
    """단일 analysis point에 대한 모든 측정 결과"""
    t_center_ms: int
    t_window_ms: int
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    evidence_frame_path: Optional[str] = None  # 대표 프레임 저장 경로


@dataclass
class CVMeasurementResult:
    """CV Pass 전체 결과"""
    measurements: List[PointMeasurement] = field(default_factory=list)
    version: str = CV_PASS_VERSION
    run_at: str = ""
    total_frames_processed: int = 0
    processing_time_ms: int = 0


@dataclass
class CVPassProvenance:
    """CV Pass 실행 메타데이터"""
    version: str
    run_at: str
    video_path: str
    metrics_requested: List[str]
    metrics_measured: List[str]
    total_frames: int
    processing_time_ms: int


# ============================================
# Frame Extraction
# ============================================

class FrameExtractor:
    """ffmpeg 기반 프레임 추출"""
    
    @staticmethod
    def extract_frames_for_window(
        video_path: str,
        t_center_ms: int,
        t_window_ms: int,
        fps: float = 10.0,
        output_dir: Optional[str] = None,
    ) -> List[Tuple[int, np.ndarray]]:
        """
        특정 윈도우의 프레임 추출
        
        Args:
            video_path: 비디오 파일 경로
            t_center_ms: 중심 타임스탬프 (ms)
            t_window_ms: 윈도우 폭 (ms)
            fps: 추출 FPS
            output_dir: 프레임 저장 디렉토리 (None이면 임시)
        
        Returns:
            List of (timestamp_ms, frame_array)
        """
        start_ms = max(0, t_center_ms - t_window_ms // 2)
        end_ms = t_center_ms + t_window_ms // 2
        
        start_sec = start_ms / 1000.0
        duration_sec = (end_ms - start_ms) / 1000.0
        
        output_dir = output_dir or tempfile.mkdtemp(prefix="cv_frames_")
        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
        
        # ffmpeg로 프레임 추출
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_sec:.3f}",
            "-i", video_path,
            "-t", f"{duration_sec:.3f}",
            "-vf", f"fps={fps}",
            "-q:v", "2",
            output_pattern,
        ]
        
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                timeout=180,  # 3분 (긴 영상 지원)
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed: {e.stderr.decode()}")
            return []
        except FileNotFoundError:
            logger.error("ffmpeg not found")
            return []
        
        # 프레임 로드
        frames = []
        frame_files = sorted(Path(output_dir).glob("frame_*.jpg"))
        
        for i, frame_path in enumerate(frame_files):
            timestamp_ms = start_ms + int(i * (1000 / fps))
            frame = cv2.imread(str(frame_path))
            if frame is not None:
                frames.append((timestamp_ms, frame))
        
        return frames
    
    @staticmethod
    def extract_single_frame(
        video_path: str,
        t_ms: int,
    ) -> Optional[np.ndarray]:
        """단일 프레임 추출"""
        frames = FrameExtractor.extract_frames_for_window(
            video_path, t_ms, 100, fps=10
        )
        return frames[0][1] if frames else None


# ============================================
# Metric Calculators
# ============================================

class MetricCalculators:
    """개별 메트릭 계산기 (결정론적)"""
    
    @staticmethod
    def center_offset_xy(
        frames: List[np.ndarray],
        roi: str = "full_frame",
    ) -> Tuple[List[float], float]:
        """
        피사체 중심 오프셋 계산
        
        Returns:
            ([offset_x, offset_y], confidence)
            offset: -1.0 ~ 1.0 (화면 중앙 기준)
        """
        if not frames:
            return [0.0, 0.0], 0.0
        
        offsets_x = []
        offsets_y = []
        
        for frame in frames:
            h, w = frame.shape[:2]
            center_x, center_y = w / 2, h / 2
            
            # 얼굴 감지 시도
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Haar Cascade 사용 (결정론적)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # 가장 큰 얼굴 선택
                largest = max(faces, key=lambda f: f[2] * f[3])
                fx, fy, fw, fh = largest
                face_center_x = fx + fw / 2
                face_center_y = fy + fh / 2
                
                # 정규화 (-1 ~ 1)
                offset_x = (face_center_x - center_x) / center_x
                offset_y = (face_center_y - center_y) / center_y
            else:
                # 얼굴 없으면 중앙 가정
                offset_x = 0.0
                offset_y = 0.0
            
            offsets_x.append(offset_x)
            offsets_y.append(offset_y)
        
        # 평균
        mean_x = float(np.mean(offsets_x))
        mean_y = float(np.mean(offsets_y))
        
        # 신뢰도: 얼굴 감지율
        detection_rate = sum(1 for ox in offsets_x if ox != 0.0) / len(offsets_x)
        confidence = max(0.3, detection_rate)
        
        return [round(mean_x, 4), round(mean_y, 4)], confidence
    
    @staticmethod
    def brightness_ratio(
        frames: List[np.ndarray],
        roi: str = "full_frame",
    ) -> Tuple[float, float]:
        """
        밝기 비율 계산 (0-1)
        
        Returns:
            (brightness_ratio, confidence)
        """
        if not frames:
            return 0.5, 0.0
        
        brightness_values = []
        
        for frame in frames:
            # HSV로 변환하여 V(밝기) 채널 추출
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            v_channel = hsv[:, :, 2]
            
            # 0-255 → 0-1 정규화
            brightness = float(np.mean(v_channel)) / 255.0
            brightness_values.append(brightness)
        
        mean_brightness = float(np.mean(brightness_values))
        std_brightness = float(np.std(brightness_values))
        
        # 신뢰도: 표준편차가 낮을수록 높음
        confidence = max(0.5, 1.0 - std_brightness * 2)
        
        return round(mean_brightness, 4), round(confidence, 4)
    
    @staticmethod
    def blur_score(
        frames: List[np.ndarray],
        roi: str = "full_frame",
    ) -> Tuple[float, float]:
        """
        블러 스코어 계산 (Laplacian variance)
        높을수록 선명, 낮을수록 흐림
        
        Returns:
            (blur_score_normalized, confidence)
        """
        if not frames:
            return 0.5, 0.0
        
        blur_scores = []
        
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Laplacian variance (높을수록 선명)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            
            blur_scores.append(variance)
        
        mean_blur = float(np.mean(blur_scores))
        
        # 정규화 (0-1, 경험적 threshold)
        # 일반적으로 100 이하면 흐림, 500 이상이면 선명
        normalized = min(1.0, mean_blur / 500.0)
        
        # 신뢰도: 프레임 수 기반
        confidence = min(1.0, len(frames) / 5.0)
        
        return round(normalized, 4), round(confidence, 4)

    @staticmethod
    def scene_change(
        frames: List[np.ndarray],
        roi: str = "full_frame",
        threshold: float = 30.0,
    ) -> Tuple[Dict[str, Any], float]:
        """
        씬 전환 감지 (프레임 간 차이)
        
        Returns:
            ({"has_change": bool, "change_scores": [float], "max_score": float}, confidence)
        """
        if len(frames) < 2:
            return {"has_change": False, "change_scores": [], "max_score": 0.0}, 0.0
        
        change_scores = []
        
        for i in range(1, len(frames)):
            prev_gray = cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            
            # 프레임 간 절대 차이
            diff = cv2.absdiff(prev_gray, curr_gray)
            score = float(np.mean(diff))
            change_scores.append(round(score, 2))
        
        max_score = max(change_scores) if change_scores else 0.0
        has_change = max_score > threshold
        
        confidence = min(1.0, len(frames) / 5.0)
        
        return {
            "has_change": has_change,
            "change_scores": change_scores[:10],  # 최대 10개
            "max_score": round(max_score, 2),
        }, round(confidence, 4)

    @staticmethod
    def face_bbox(
        frames: List[np.ndarray],
        roi: str = "full_frame",
    ) -> Tuple[Dict[str, Any], float]:
        """
        얼굴 바운딩 박스 (구도 분석용)
        
        Returns:
            ({"detected": bool, "bbox_normalized": [x, y, w, h], "area_ratio": float}, confidence)
            bbox_normalized: 0-1 범위로 정규화된 좌표
        """
        if not frames:
            return {"detected": False, "bbox_normalized": None, "area_ratio": 0.0}, 0.0
        
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        
        all_bboxes = []
        
        for frame in frames:
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            if len(faces) > 0:
                largest = max(faces, key=lambda f: f[2] * f[3])
                fx, fy, fw, fh = largest
                
                # 정규화 (0-1)
                bbox_norm = [
                    round(fx / w, 4),
                    round(fy / h, 4),
                    round(fw / w, 4),
                    round(fh / h, 4),
                ]
                area_ratio = (fw * fh) / (w * h)
                all_bboxes.append((bbox_norm, area_ratio))
        
        if not all_bboxes:
            return {"detected": False, "bbox_normalized": None, "area_ratio": 0.0}, 0.3
        
        # 평균 bbox 계산
        avg_bbox = [
            round(np.mean([b[0][i] for b in all_bboxes]), 4)
            for i in range(4)
        ]
        avg_area = round(np.mean([b[1] for b in all_bboxes]), 4)
        
        detection_rate = len(all_bboxes) / len(frames)
        
        return {
            "detected": True,
            "bbox_normalized": avg_bbox,
            "area_ratio": avg_area,
        }, round(max(0.5, detection_rate), 4)

    @staticmethod
    def text_density(
        frames: List[np.ndarray],
        roi: str = "full_frame",
    ) -> Tuple[Dict[str, Any], float]:
        """
        텍스트 밀도 측정 (자막/텍스트 오버레이 감지)
        
        MSER (Maximally Stable Extremal Regions) 기반
        OCR 없이 텍스트 영역만 감지
        
        Returns:
            ({"has_text": bool, "text_area_ratio": float, "region_count": int}, confidence)
        """
        if not frames:
            return {"has_text": False, "text_area_ratio": 0.0, "region_count": 0}, 0.0
        
        all_ratios = []
        all_counts = []
        
        for frame in frames:
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # MSER로 텍스트 영역 감지
            mser = cv2.MSER_create()
            mser.setMinArea(50)
            mser.setMaxArea(int(h * w * 0.1))
            
            regions, _ = mser.detectRegions(gray)
            
            # 텍스트 영역 필터링 (aspect ratio 기반)
            text_regions = []
            for region in regions:
                x, y, rw, rh = cv2.boundingRect(region)
                aspect = rw / max(rh, 1)
                
                # 텍스트는 보통 가로로 긴 형태
                if 0.1 < aspect < 10 and rw > 10 and rh > 5:
                    text_regions.append((x, y, rw, rh))
            
            # 텍스트 영역 비율 계산
            if text_regions:
                # 겹치는 영역 제거 (간단히 합계)
                total_text_area = sum(rw * rh for _, _, rw, rh in text_regions)
                # 최대 50%까지 (겹침 고려)
                ratio = min(0.5, total_text_area / (w * h))
            else:
                ratio = 0.0
            
            all_ratios.append(ratio)
            all_counts.append(len(text_regions))
        
        avg_ratio = float(np.mean(all_ratios))
        avg_count = int(np.mean(all_counts))
        has_text = avg_ratio > 0.01  # 1% 이상이면 텍스트 있음
        
        confidence = min(1.0, len(frames) / 5.0)
        
        return {
            "has_text": has_text,
            "text_area_ratio": round(avg_ratio, 4),
            "region_count": avg_count,
        }, round(confidence, 4)


# ============================================
# Main CV Pass Class
# ============================================

class CVMeasurementPass:
    """
    Pass 2: CV 결정론적 측정
    
    특징:
    - 동일 입력 = 동일 출력
    - ffmpeg + OpenCV 기반
    - 3개 MVP 메트릭
    """
    
    def __init__(
        self,
        extraction_fps: float = 10.0,
        save_evidence_frames: bool = False,
        evidence_output_dir: Optional[str] = None,
    ):
        self.extraction_fps = extraction_fps
        self.save_evidence_frames = save_evidence_frames
        self.evidence_output_dir = evidence_output_dir
    
    def run(
        self,
        *,
        video_path: str,
        analysis_plan: AnalysisPlanSeedLLM,
    ) -> Tuple[CVMeasurementResult, CVPassProvenance]:
        """
        CV Pass 실행
        
        Args:
            video_path: 비디오 파일 경로
            analysis_plan: Pass 1에서 생성된 측정 계획
        
        Returns:
            (CVMeasurementResult, CVPassProvenance)
        """
        import time
        start_time = time.time()
        
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        result = CVMeasurementResult(
            run_at=datetime.now(timezone.utc).isoformat(),
        )
        
        total_frames = 0
        metrics_requested = set()
        metrics_measured = set()
        
        # 각 analysis point 처리
        for point in analysis_plan.points:
            point_result = self._process_point(video_path, point)
            result.measurements.append(point_result)
            total_frames += max(
                (m.frame_count for m in point_result.metrics.values()),
                default=0
            )
            
            for m in point.measurements:
                metrics_requested.add(m.metric_id)
            for m_id in point_result.metrics.keys():
                metrics_measured.add(m_id)
        
        result.total_frames_processed = total_frames
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Provenance
        prov = CVPassProvenance(
            version=CV_PASS_VERSION,
            run_at=result.run_at,
            video_path=video_path,
            metrics_requested=list(metrics_requested),
            metrics_measured=list(metrics_measured),
            total_frames=total_frames,
            processing_time_ms=result.processing_time_ms,
        )
        
        logger.info(
            f"✅ CVMeasurementPass completed: points={len(result.measurements)}, "
            f"frames={total_frames}, time={result.processing_time_ms}ms"
        )
        
        return result, prov
    
    def _process_point(
        self,
        video_path: str,
        point: AnalysisPointSeedLLM,
    ) -> PointMeasurement:
        """단일 analysis point 처리"""
        
        # 프레임 추출
        frames_data = FrameExtractor.extract_frames_for_window(
            video_path,
            point.t_center_ms,
            point.t_window_ms,
            fps=self.extraction_fps,
        )
        
        frames = [f[1] for f in frames_data]
        
        point_result = PointMeasurement(
            t_center_ms=point.t_center_ms,
            t_window_ms=point.t_window_ms,
        )
        
        # 각 요청된 메트릭 측정
        for spec in point.measurements:
            metric_result = self._measure_metric(frames, spec)
            if metric_result:
                point_result.metrics[spec.metric_id] = metric_result
        
        # Evidence frame 저장 (옵션)
        if self.save_evidence_frames and frames:
            evidence_path = self._save_evidence_frame(
                frames[len(frames) // 2],  # 중간 프레임
                point.t_center_ms,
            )
            point_result.evidence_frame_path = evidence_path
        
        return point_result
    
    def _measure_metric(
        self,
        frames: List[np.ndarray],
        spec: MeasurementSpecLLM,
    ) -> Optional[MetricResult]:
        """단일 메트릭 측정"""
        
        metric_id = spec.metric_id
        
        # 지원 여부 확인
        if metric_id not in SUPPORTED_CV_METRICS:
            logger.warning(f"Unsupported metric: {metric_id}")
            return MetricResult(
                metric_id=metric_id,
                value=None,
                confidence=0.0,
                note=f"unsupported_metric",
            )
        
        if not frames:
            return MetricResult(
                metric_id=metric_id,
                value=None,
                confidence=0.0,
                note="no_frames",
            )
        
        # 메트릭별 계산
        if metric_id == "cmp.center_offset_xy.v1":
            value, confidence = MetricCalculators.center_offset_xy(frames, spec.roi)
        elif metric_id == "lit.brightness_ratio.v1":
            value, confidence = MetricCalculators.brightness_ratio(frames, spec.roi)
        elif metric_id == "cmp.blur_score.v1":
            value, confidence = MetricCalculators.blur_score(frames, spec.roi)
        # v2.0 확장 메트릭
        elif metric_id == "edit.scene_change.v1":
            value, confidence = MetricCalculators.scene_change(frames, spec.roi)
        elif metric_id == "cmp.face_bbox.v1":
            value, confidence = MetricCalculators.face_bbox(frames, spec.roi)
        elif metric_id == "txt.text_density.v1":
            value, confidence = MetricCalculators.text_density(frames, spec.roi)
        else:
            return None
        
        return MetricResult(
            metric_id=metric_id,
            value=value,
            confidence=confidence,
            roi=spec.roi,
            aggregation=spec.aggregation,
            frame_count=len(frames),
        )
    
    def _save_evidence_frame(
        self,
        frame: np.ndarray,
        t_ms: int,
    ) -> Optional[str]:
        """증거 프레임 저장"""
        if self.evidence_output_dir is None:
            self.evidence_output_dir = tempfile.mkdtemp(prefix="cv_evidence_")
        
        output_path = os.path.join(
            self.evidence_output_dir,
            f"evidence_{t_ms}ms.jpg"
        )
        
        cv2.imwrite(output_path, frame)
        return output_path
