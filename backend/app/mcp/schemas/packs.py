"""
MCP Source Pack 관련 스키마
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class VDGInfo(BaseModel):
    """VDG 분석 정보"""
    quality_score: Optional[float] = None
    quality_valid: Optional[bool] = None
    analysis_status: Optional[str] = None


class PackSource(BaseModel):
    """소스팩 항목"""
    id: str
    title: str
    platform: str = "unknown"
    category: str = "unknown"
    tier: Optional[str] = None
    score: float = 0
    views: int = 0
    growth_rate: Optional[float] = None
    video_url: str = ""
    comments: Optional[List[Dict[str, Any]]] = None
    vdg: Optional[VDGInfo] = None


class SourcePackResponse(BaseModel):
    """소스팩 생성 응답"""
    name: str
    created_at: str
    outlier_count: int
    sources: List[PackSource]
