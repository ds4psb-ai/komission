"""
Template Seeds Schema and API Models
Based on 15_FINAL_ARCHITECTURE.md - Opal 템플릿 시드 생성기
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TemplateType(str, Enum):
    """템플릿 시드 유형"""
    CAPSULE = "capsule"  # 캡슐 노드용
    GUIDE = "guide"      # 촬영 가이드용
    EDIT = "edit"        # 편집 가이드용


class SeedParams(BaseModel):
    """템플릿 시드 파라미터"""
    hook: Optional[str] = Field(None, description="0-2초 훅 문장/장면")
    shotlist: List[str] = Field(default_factory=list, description="3-6개 샷 시퀀스")
    audio: Optional[str] = Field(None, description="추천 사운드/리듬")
    scene: Optional[str] = Field(None, description="장소/소품/분위기")
    timing: List[str] = Field(default_factory=list, description="컷 길이/템포")
    do_not: List[str] = Field(default_factory=list, description="금지 요소")


class TemplateSeedCreate(BaseModel):
    """템플릿 시드 생성 요청"""
    parent_id: Optional[str] = Field(None, description="Parent 노드 ID")
    cluster_id: Optional[str] = Field(None, description="참고 클러스터 ID")
    template_type: TemplateType = Field(default=TemplateType.CAPSULE)


class TemplateSeedResponse(BaseModel):
    """템플릿 시드 응답"""
    seed_id: str
    parent_id: Optional[str] = None
    cluster_id: Optional[str] = None
    template_type: TemplateType
    prompt_version: Optional[str] = None
    seed_params: SeedParams
    created_at: datetime


class GenerateSeedRequest(BaseModel):
    """Opal 시드 생성 요청"""
    parent_id: str = Field(description="Parent 노드 ID")
    cluster_id: Optional[str] = Field(None, description="참고 클러스터 ID")
    template_type: TemplateType = Field(default=TemplateType.CAPSULE)
    context: Optional[dict] = Field(None, description="추가 컨텍스트")


class GenerateSeedResponse(BaseModel):
    """Opal 시드 생성 응답"""
    success: bool
    seed: Optional[TemplateSeedResponse] = None
    error: Optional[str] = None
