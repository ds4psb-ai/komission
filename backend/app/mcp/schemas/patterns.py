"""
MCP 패턴 관련 스키마
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatternResult(BaseModel):
    """패턴 검색 결과 항목"""
    id: str
    title: str
    tier: Optional[str] = None
    platform: Optional[str] = None
    category: Optional[str] = None
    score: Optional[float] = None
    views: int = 0


class SearchFilters(BaseModel):
    """검색 필터"""
    category: Optional[str] = None
    platform: Optional[str] = None
    min_tier: str = "C"
    limit: int = 10


class SearchResponse(BaseModel):
    """패턴 검색 응답"""
    query: str
    filters: SearchFilters
    count: int
    results: List[PatternResult]
