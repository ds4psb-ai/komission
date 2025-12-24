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


class NotebookLibraryResponse(BaseModel):
    id: str
    source_url: str
    platform: str
    category: str
    summary: Dict[str, Any]
    cluster_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
