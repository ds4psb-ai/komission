"""
Keyframe Verifier (P0-3)

LLM이 찍은 keyframe t_ms를 CV로 검증하고 evidence_id 생성

기능:
1. keyframe t_ms에서 실제 프레임 추출
2. CV 측정 (blur, brightness, motion)
3. evidence_id 생성 (결정론적)
4. start < peak < end 순서 검증
5. CV 변화량으로 peak 신뢰도 판정

사용:
    from app.services.vdg_2pass.keyframe_verifier import keyframe_verifier
    results = keyframe_verifier.verify_and_generate_evidence(keyframes, video_path, kick_index)
"""
import hashlib
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

logger = logging.getLogger(__name__)


@dataclass
class KeyframeEvidence:
    """키프레임 증거 데이터"""
    keyframe_role: str  # start/peak/end
    t_ms: int
    evidence_id: Optional[str]
    verified: bool
    reason: Optional[str] = None  # 실패 사유
    blur_score: Optional[float] = None
    brightness: Optional[float] = None
    motion_proxy: Optional[float] = None  # 이전 프레임과 차이
    frame_hash: Optional[str] = None


class KeyframeVerifier:
    """
    Keyframe t_ms → 실제 프레임 검증 + evidence 생성
    
    LLM이 "이게 peak입니다"라고 말한 t_ms에서:
    1. 실제 프레임을 추출할 수 있는지
    2. 그 프레임이 CV 관점에서 "변화"가 있는지
    를 검증합니다.
    """
    
    MIN_BLUR_CHANGE_RATIO = 0.05  # 5% 이상 변화 필요
    MIN_BRIGHTNESS_CHANGE = 10  # 최소 밝기 변화
    
    def verify_and_generate_evidence(
        self,
        keyframes: List[Dict[str, Any]],
        video_path: str,
        kick_index: int
    ) -> List[KeyframeEvidence]:
        """
        각 keyframe에 대해 검증 및 evidence 생성
        
        Args:
            keyframes: [{"t_ms": int, "role": str, "what_to_see": str}, ...]
            video_path: 비디오 파일 경로
            kick_index: 킥 인덱스 (evidence_id 생성용)
            
        Returns:
            List[KeyframeEvidence]
        """
        if not CV2_AVAILABLE:
            logger.warning("cv2 not available, skipping keyframe verification")
            return [
                KeyframeEvidence(
                    keyframe_role=kf.get('role', 'unknown'),
                    t_ms=kf.get('t_ms', 0),
                    evidence_id=None,
                    verified=False,
                    reason="cv2_not_available"
                )
                for kf in keyframes
            ]
        
        results = []
        prev_frame_data = None
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Failed to open video: {video_path}")
                return [
                    KeyframeEvidence(
                        keyframe_role=kf.get('role', 'unknown'),
                        t_ms=kf.get('t_ms', 0),
                        evidence_id=None,
                        verified=False,
                        reason="video_open_failed"
                    )
                    for kf in keyframes
                ]
            
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sort keyframes by t_ms for sequential processing
            sorted_kfs = sorted(keyframes, key=lambda x: x.get('t_ms', 0))
            
            for kf in sorted_kfs:
                t_ms = kf.get('t_ms', 0)
                role = kf.get('role', 'unknown')
                
                # Calculate frame number
                frame_num = int((t_ms / 1000) * fps)
                
                if frame_num < 0 or frame_num >= total_frames:
                    results.append(KeyframeEvidence(
                        keyframe_role=role,
                        t_ms=t_ms,
                        evidence_id=None,
                        verified=False,
                        reason=f"frame_out_of_range_{frame_num}/{total_frames}"
                    ))
                    continue
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    results.append(KeyframeEvidence(
                        keyframe_role=role,
                        t_ms=t_ms,
                        evidence_id=None,
                        verified=False,
                        reason="frame_extraction_failed"
                    ))
                    continue
                
                # CV measurements
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                brightness = float(gray.mean())
                
                # Motion proxy (difference from previous frame)
                motion_proxy = None
                if prev_frame_data is not None:
                    prev_gray = prev_frame_data.get('gray')
                    if prev_gray is not None and prev_gray.shape == gray.shape:
                        diff = cv2.absdiff(prev_gray, gray)
                        motion_proxy = float(diff.mean())
                
                # Generate deterministic evidence_id
                frame_bytes = frame.tobytes()[:2048]  # First 2KB for hash
                frame_hash = hashlib.md5(frame_bytes).hexdigest()[:8]
                evidence_id = f"ev.frame.k{kick_index}.{role}.{frame_hash}"
                
                results.append(KeyframeEvidence(
                    keyframe_role=role,
                    t_ms=t_ms,
                    evidence_id=evidence_id,
                    verified=True,
                    blur_score=round(blur_score, 2),
                    brightness=round(brightness, 2),
                    motion_proxy=round(motion_proxy, 2) if motion_proxy else None,
                    frame_hash=frame_hash
                ))
                
                # Store for next iteration
                prev_frame_data = {
                    'gray': gray.copy(),
                    't_ms': t_ms
                }
            
            cap.release()
            
        except Exception as e:
            logger.error(f"Keyframe verification error: {e}")
            return [
                KeyframeEvidence(
                    keyframe_role=kf.get('role', 'unknown'),
                    t_ms=kf.get('t_ms', 0),
                    evidence_id=None,
                    verified=False,
                    reason=f"exception: {str(e)[:50]}"
                )
                for kf in keyframes
            ]
        
        return results
    
    def validate_sequence(self, results: List[KeyframeEvidence]) -> Dict[str, Any]:
        """
        start < peak < end 순서 검증 + CV 변화량 체크
        
        Returns:
            {"valid": bool, "issues": List[str], "peak_confidence": float}
        """
        issues = []
        
        # Build role map
        by_role = {r.keyframe_role: r for r in results if r.verified}
        
        # Check all roles present
        missing_roles = set(['start', 'peak', 'end']) - set(by_role.keys())
        if missing_roles:
            issues.append(f"missing_roles: {missing_roles}")
            return {"valid": False, "issues": issues, "peak_confidence": 0.0}
        
        # Check temporal order
        start_t = by_role['start'].t_ms
        peak_t = by_role['peak'].t_ms
        end_t = by_role['end'].t_ms
        
        if not (start_t < peak_t < end_t):
            issues.append(f"order_invalid: start={start_t}, peak={peak_t}, end={end_t}")
            return {"valid": False, "issues": issues, "peak_confidence": 0.0}
        
        # Check CV change at peak
        peak_confidence = 1.0
        
        start_blur = by_role['start'].blur_score or 0
        peak_blur = by_role['peak'].blur_score or 0
        
        if start_blur > 0:
            blur_change = abs(peak_blur - start_blur) / start_blur
            if blur_change < self.MIN_BLUR_CHANGE_RATIO:
                issues.append(f"low_blur_change: {blur_change:.2%}")
                peak_confidence *= 0.7
        
        # Check brightness change
        start_bright = by_role['start'].brightness or 0
        peak_bright = by_role['peak'].brightness or 0
        
        if abs(peak_bright - start_bright) < self.MIN_BRIGHTNESS_CHANGE:
            issues.append("low_brightness_change")
            peak_confidence *= 0.8
        
        # Check motion at peak
        if by_role['peak'].motion_proxy is not None:
            if by_role['peak'].motion_proxy < 5:  # Low motion threshold
                issues.append("low_peak_motion")
                peak_confidence *= 0.9
        
        return {
            "valid": len([i for i in issues if "order" in i or "missing" in i]) == 0,
            "issues": issues,
            "peak_confidence": round(peak_confidence, 2)
        }
    
    def get_evidence_ids(self, results: List[KeyframeEvidence]) -> List[str]:
        """검증된 keyframe의 evidence_id 리스트 반환"""
        return [r.evidence_id for r in results if r.verified and r.evidence_id]


# Singleton instance
keyframe_verifier = KeyframeVerifier()
