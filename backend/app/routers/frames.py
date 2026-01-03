"""
Frame Serving Router

키프레임 이미지 서빙 엔드포인트

작동 방식:
1. VDG CV 분석 시 저장된 evidence frames 서빙
2. 프레임이 없으면 동적으로 영상에서 추출
3. CDN/스토리지 통합 가능
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pathlib import Path
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/frames", tags=["frames"])

# 프레임 저장 기본 경로
FRAME_STORAGE_PATH = Path(os.getenv("FRAME_STORAGE_PATH", "/tmp/komission/frames"))


@router.get("/{content_id}/{t_ms}")
async def get_frame(
    content_id: str,
    t_ms: int,
    width: Optional[int] = Query(None, ge=100, le=1920, description="리사이즈 너비"),
    quality: int = Query(85, ge=50, le=100, description="JPEG 품질"),
):
    """
    키프레임 이미지 서빙
    
    Args:
        content_id: VDG 콘텐츠 ID
        t_ms: 타임스탬프 (밀리초)
        width: 옵션 - 리사이즈 너비
        quality: JPEG 품질 (기본 85)
    
    Returns:
        JPEG 이미지
    """
    # 1. 정확한 타임스탬프 파일 찾기
    frame_path = FRAME_STORAGE_PATH / content_id / f"{t_ms}.jpg"
    
    if frame_path.exists():
        logger.info(f"📸 Serving frame: {frame_path}")
        return FileResponse(
            path=str(frame_path),
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=31536000"}  # 1년 캐시
        )
    
    # 2. 근사치 프레임 찾기 (±500ms)
    content_dir = FRAME_STORAGE_PATH / content_id
    if content_dir.exists():
        for frame_file in content_dir.glob("*.jpg"):
            try:
                file_t_ms = int(frame_file.stem)
                if abs(file_t_ms - t_ms) <= 500:  # 500ms 허용
                    logger.info(f"📸 Serving approximate frame: {frame_file} (requested: {t_ms})")
                    return FileResponse(
                        path=str(frame_file),
                        media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=31536000"}
                    )
            except ValueError:
                continue
    
    # 3. 동적 추출은 비용이 높으므로 placeholder 반환
    logger.warning(f"🔴 Frame not found: {content_id}/{t_ms}, returning placeholder")
    
    # 투명 1x1 픽셀 이미지 (placeholder)
    transparent_pixel = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # RGBA
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND
        0x42, 0x60, 0x82
    ])
    
    return Response(
        content=transparent_pixel,
        media_type="image/png",
        headers={"Cache-Control": "no-cache"}
    )


@router.get("/{content_id}")
async def list_frames(content_id: str):
    """
    콘텐츠의 저장된 프레임 목록 조회
    
    Args:
        content_id: VDG 콘텐츠 ID
    
    Returns:
        프레임 타임스탬프 목록
    """
    content_dir = FRAME_STORAGE_PATH / content_id
    
    if not content_dir.exists():
        return {"content_id": content_id, "frames": [], "count": 0}
    
    frames = []
    for frame_file in sorted(content_dir.glob("*.jpg")):
        try:
            t_ms = int(frame_file.stem)
            frames.append({
                "t_ms": t_ms,
                "url": f"/api/frames/{content_id}/{t_ms}",
                "size_bytes": frame_file.stat().st_size,
            })
        except ValueError:
            continue
    
    return {
        "content_id": content_id,
        "frames": frames,
        "count": len(frames),
    }
