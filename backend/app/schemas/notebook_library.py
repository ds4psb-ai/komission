from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class NotebookLibraryCreate(BaseModel):
    """NotebookLM Pattern Engine 결과 저장 요청"""
    source_url: str
    platform: str
    category: str
    summary: Dict[str, Any]  # Pattern Engine 결과 (필수)
    cluster_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    source_pack_id: Optional[str] = None  # PEGL v1.0
    temporal_phase: Optional[str] = None
    variant_age_days: Optional[int] = None
    novelty_decay_score: Optional[float] = None
    burstiness_index: Optional[float] = None


class NotebookLibraryResponse(BaseModel):
    """NotebookLM Pattern Engine 결과 응답"""
    id: str
    source_url: str
    platform: str
    category: str
    summary: Dict[str, Any]
    cluster_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    source_pack_id: Optional[str] = None  # PEGL v1.0
    temporal_phase: Optional[str] = None
    variant_age_days: Optional[int] = None
    novelty_decay_score: Optional[float] = None
    burstiness_index: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

