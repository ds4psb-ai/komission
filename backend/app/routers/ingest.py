"""
Ingest utilities router.
Core logic for URL normalization and metadata extraction (no UI).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.routers.auth import require_curator, User
from app.services.comment_extractor import extract_best_comments
from app.services.social_metadata import normalize_url, extract_social_metadata


router = APIRouter(prefix="/ingest", tags=["Ingest"])


class NormalizeUrlRequest(BaseModel):
    url: str = Field(..., description="Content URL")
    expand_short: bool = Field(default=True, description="Expand short URLs when possible")


class NormalizeUrlResponse(BaseModel):
    platform: str
    content_id: Optional[str]
    canonical_url: str


class ExtractMetadataRequest(BaseModel):
    url: str = Field(..., description="Content URL")
    platform: Optional[str] = Field(default=None, description="Optional platform override")
    include_comments: bool = Field(default=False, description="Also extract best comments")
    comment_limit: int = Field(default=5, ge=1, le=50)


class ExtractMetadataResponse(BaseModel):
    platform: str
    data: dict
    comments: Optional[list] = None


@router.post("/normalize-url", response_model=NormalizeUrlResponse)
async def normalize_url_endpoint(
    payload: NormalizeUrlRequest,
    current_user: User = Depends(require_curator),
):
    try:
        result = normalize_url(payload.url, expand_short=payload.expand_short)
        return NormalizeUrlResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/extract-metadata", response_model=ExtractMetadataResponse)
async def extract_metadata_endpoint(
    payload: ExtractMetadataRequest,
    current_user: User = Depends(require_curator),
):
    try:
        platform, metadata = extract_social_metadata(
            payload.url,
            platform=payload.platform,
        )
        comments = None
        if payload.include_comments:
            comments = await extract_best_comments(
                payload.url,
                platform,
                limit=payload.comment_limit,
            )
        return ExtractMetadataResponse(platform=platform, data=metadata, comments=comments)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
