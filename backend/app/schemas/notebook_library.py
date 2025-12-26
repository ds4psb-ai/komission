from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class NotebookLibraryCreate(BaseModel):
    source_url: str
    platform: str
    category: str
    summary: Dict[str, Any]
    cluster_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    temporal_phase: Optional[str] = None
    variant_age_days: Optional[int] = None
    novelty_decay_score: Optional[float] = None
    burstiness_index: Optional[float] = None


class NotebookLibraryResponse(BaseModel):
    id: str
    source_url: str
    platform: str
    category: str
    summary: Dict[str, Any]
    cluster_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    temporal_phase: Optional[str] = None
    variant_age_days: Optional[int] = None
    novelty_decay_score: Optional[float] = None
    burstiness_index: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
