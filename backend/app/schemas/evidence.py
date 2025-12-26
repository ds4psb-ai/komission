"""
Pydantic schemas for Evidence Loop system
Phase 4: VDG + EvidenceSnapshot + Outlier Ingestion
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


# ==================
# OUTLIER SCHEMAS
# ==================

class OutlierItemStatus(str, Enum):
    PENDING = "pending"
    SELECTED = "selected"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class OutlierSourceCreate(BaseModel):
    name: str
    base_url: str
    auth_type: str = "none"
    auth_config: Optional[Dict[str, Any]] = None
    crawl_interval_hours: int = 24


class OutlierSourceResponse(BaseModel):
    id: str
    name: str
    base_url: str
    auth_type: str
    last_crawled: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OutlierItemCreate(BaseModel):
    source_id: str
    external_id: str
    video_url: str
    platform: str
    category: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    like_count: Optional[int] = None
    share_count: Optional[int] = None
    growth_rate: Optional[str] = None


class OutlierCrawlItem(BaseModel):
    source_name: str
    external_id: str
    video_url: str
    platform: str
    category: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    like_count: Optional[int] = None
    share_count: Optional[int] = None
    growth_rate: Optional[str] = None
    # Extended metrics
    outlier_score: Optional[float] = None
    outlier_tier: Optional[str] = None
    creator_avg_views: Optional[int] = None
    engagement_rate: Optional[float] = None


class OutlierItemManualCreate(BaseModel):
    video_url: str
    platform: str
    category: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    like_count: Optional[int] = None
    share_count: Optional[int] = None
    growth_rate: Optional[str] = None
    source_name: Optional[str] = "manual"


class OutlierItemResponse(BaseModel):
    id: str
    source_id: str
    external_id: str
    video_url: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    platform: str
    category: str
    view_count: int
    like_count: Optional[int] = None
    growth_rate: Optional[str] = None
    status: OutlierItemStatus
    promoted_to_node_id: Optional[str] = None
    crawled_at: datetime

    class Config:
        from_attributes = True


class OutlierCandidatesResponse(BaseModel):
    total: int
    candidates: List[OutlierItemResponse]


# ==================
# METRIC DAILY SCHEMAS
# ==================

class MetricDailyCreate(BaseModel):
    node_id: str
    date: datetime
    view_count: int
    like_count: Optional[int] = None
    share_count: Optional[int] = None
    comment_count: Optional[int] = None
    delta_views: Optional[int] = None
    delta_rate: Optional[str] = None
    data_source: str = "manual"


class MetricDailyResponse(BaseModel):
    id: str
    node_id: str
    date: datetime
    view_count: int
    like_count: Optional[int] = None
    share_count: Optional[int] = None
    comment_count: Optional[int] = None
    delta_views: Optional[int] = None
    delta_rate: Optional[str] = None
    data_source: str

    class Config:
        from_attributes = True


# ==================
# EVIDENCE SNAPSHOT SCHEMAS
# ==================

class MutationSummary(BaseModel):
    """변주별 성과 요약"""
    pattern_code: str
    success_rate: float = Field(ge=0.0, le=1.0)
    sample_count: int
    avg_delta: str  # "+127%"
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class DepthSummary(BaseModel):
    """Depth별 변주 요약 (mutation_type -> pattern -> stats)"""
    audio: Optional[Dict[str, MutationSummary]] = None
    visual: Optional[Dict[str, MutationSummary]] = None
    hook: Optional[Dict[str, MutationSummary]] = None
    setting: Optional[Dict[str, MutationSummary]] = None


class EvidenceSnapshotCreate(BaseModel):
    parent_node_id: str
    period: str = "4w"  # "4w", "12w", "1y"
    depth1_summary: Dict[str, Any]
    depth2_summary: Optional[Dict[str, Any]] = None
    sample_count: int = 0
    confidence: float = 0.5


class EvidenceSnapshotResponse(BaseModel):
    id: str
    parent_node_id: str
    snapshot_date: datetime
    period: str
    depth1_summary: Dict[str, Any]
    depth2_summary: Optional[Dict[str, Any]] = None
    top_mutation_type: Optional[str] = None
    top_mutation_pattern: Optional[str] = None
    top_mutation_rate: Optional[str] = None
    sample_count: int
    confidence: float
    sheet_synced: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================
# EVIDENCE TABLE ROW (for Sheets export)
# ==================

class EvidenceRow(BaseModel):
    """Evidence Sheet 한 줄 (스프레드시트 컬럼 매핑)"""
    parent_node_id: str
    mutation_type: str  # audio, visual, hook, setting
    before_pattern: str
    after_pattern: str
    success_rate: float
    sample_count: int
    avg_delta: str
    period: str  # "4w", "12w"
    depth: int  # 1, 2, 3
    confidence: float
    risk: str  # low, medium, high
    updated_at: datetime


class EvidenceTableResponse(BaseModel):
    parent_node_id: str
    generated_at: datetime
    period: str
    rows: List[EvidenceRow]
    total_samples: int
    top_recommendation: Optional[str] = None
