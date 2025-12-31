"""
Creator Router - P2 Feedback Loop
Handles creator submissions for pattern-based videos.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models import (
    User, CreatorSubmission, CreatorSubmissionStatus, 
    PatternLibrary, OutlierItem, OutlierItemStatus, OutlierSource
)
from app.routers.auth import get_current_user
from app.utils.time import utcnow

router = APIRouter(prefix="/api/v1/creator", tags=["creator"])


# ============ Schemas ============

class SubmissionCreate(BaseModel):
    """Request to submit a video based on a pattern"""
    pattern_id: str = Field(..., description="PatternLibrary pattern_id")
    video_url: str = Field(..., description="URL of the submitted video")
    platform: str = Field(..., description="Platform: tiktok, instagram, youtube")
    creator_notes: Optional[str] = Field(None, description="Notes on what was varied")
    invariant_checklist: Optional[dict] = Field(None, description="Checklist completion status")


class SubmissionResponse(BaseModel):
    """Response after submission"""
    id: str
    pattern_id: str
    video_url: str
    platform: str
    status: str
    submitted_at: datetime
    message: str

    class Config:
        from_attributes = True


class SubmissionListItem(BaseModel):
    """Item in submissions list"""
    id: str
    pattern_id: str
    video_url: str
    platform: str
    status: str
    submitted_at: datetime
    final_view_count: Optional[int] = None
    performance_vs_baseline: Optional[str] = None


class SubmissionListResponse(BaseModel):
    """List of submissions"""
    total: int
    submissions: List[SubmissionListItem]


# ============ Endpoints ============

@router.post("/submissions", response_model=SubmissionResponse)
async def submit_video(
    request: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a video created based on a PatternLibrary pattern.
    
    Simple Flow (aligned with docs Phase 4.4-5):
    1. Creator views pattern guide (invariant_rules, mutation_strategy)
    2. Creator films video following the guide
    3. Creator submits video URL here → recorded as CreatorSubmission
    4. Admin can later promote to OutlierItem via O2O flow for tracking
    
    Note: This does NOT auto-create OutlierItem. Use existing /outliers API
    or O2O campaign flow for metric tracking integration.
    """
    # Validate pattern exists
    pattern_result = await db.execute(
        select(PatternLibrary).where(PatternLibrary.pattern_id == request.pattern_id)
    )
    pattern = pattern_result.scalar_one_or_none()
    
    # Check if already submitted
    existing_result = await db.execute(
        select(CreatorSubmission).where(
            CreatorSubmission.video_url == request.video_url,
            CreatorSubmission.user_id == current_user.id,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="이미 제출된 영상입니다."
        )
    
    # Create submission record (simple, no OutlierItem auto-creation)
    submission = CreatorSubmission(
        pattern_id=request.pattern_id,
        pattern_library_id=pattern.id if pattern else None,
        user_id=current_user.id,
        video_url=request.video_url,
        platform=request.platform,
        creator_notes=request.creator_notes,
        invariant_checklist=request.invariant_checklist,
        status=CreatorSubmissionStatus.PENDING,  # Awaits admin promotion
        submitted_at=utcnow(),
    )
    
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    return SubmissionResponse(
        id=str(submission.id),
        pattern_id=submission.pattern_id,
        video_url=submission.video_url,
        platform=submission.platform,
        status=submission.status.value if hasattr(submission.status, 'value') else str(submission.status),
        submitted_at=submission.submitted_at,
        message="✅ 영상이 제출되었습니다! 관리자 검토 후 추적이 시작됩니다."
    )


@router.get("/submissions", response_model=SubmissionListResponse)
async def list_my_submissions(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's submissions"""
    result = await db.execute(
        select(CreatorSubmission)
        .where(CreatorSubmission.user_id == current_user.id)
        .order_by(CreatorSubmission.submitted_at.desc())
        .limit(limit)
    )
    submissions = result.scalars().all()
    
    count_result = await db.execute(
        select(func.count(CreatorSubmission.id))
        .where(CreatorSubmission.user_id == current_user.id)
    )
    total = count_result.scalar_one()
    
    return SubmissionListResponse(
        total=total,
        submissions=[
            SubmissionListItem(
                id=str(s.id),
                pattern_id=s.pattern_id,
                video_url=s.video_url,
                platform=s.platform,
                status=s.status.value if hasattr(s.status, 'value') else str(s.status),
                submitted_at=s.submitted_at,
                final_view_count=s.final_view_count,
                performance_vs_baseline=s.performance_vs_baseline,
            )
            for s in submissions
        ]
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionListItem)
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific submission"""
    result = await db.execute(
        select(CreatorSubmission).where(
            CreatorSubmission.id == submission_id,
            CreatorSubmission.user_id == current_user.id,
        )
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return SubmissionListItem(
        id=str(submission.id),
        pattern_id=submission.pattern_id,
        video_url=submission.video_url,
        platform=submission.platform,
        status=submission.status.value if hasattr(submission.status, 'value') else str(submission.status),
        submitted_at=submission.submitted_at,
        final_view_count=submission.final_view_count,
        performance_vs_baseline=submission.performance_vs_baseline,
    )


# ============ Admin Endpoints ============

class PromoteResponse(BaseModel):
    """Response after promoting submission to OutlierItem"""
    submission_id: str
    outlier_item_id: str
    status: str
    message: str


@router.post("/submissions/{submission_id}/promote", response_model=PromoteResponse)
async def promote_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Promote a CreatorSubmission to OutlierItem for tracking.
    
    Admin action that:
    1. Creates OutlierItem from submission
    2. Links submission to OutlierItem
    3. Sets status to TRACKING
    4. Enables track_depth_experiment.py monitoring
    """
    import uuid as uuid_module
    
    # Check admin permission (TODO: proper role check)
    # For now, any authenticated user can promote
    
    # Get submission
    result = await db.execute(
        select(CreatorSubmission).where(CreatorSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if submission.status != CreatorSubmissionStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot promote: status is {submission.status.value}"
        )
    
    # Get pattern for category
    pattern = None
    if submission.pattern_library_id:
        pattern_result = await db.execute(
            select(PatternLibrary).where(PatternLibrary.id == submission.pattern_library_id)
        )
        pattern = pattern_result.scalar_one_or_none()
    
    # Get user info
    user_result = await db.execute(
        select(User).where(User.id == submission.user_id)
    )
    user = user_result.scalar_one_or_none()

    from app.utils.url_normalizer import normalize_video_url
    canonical_url = normalize_video_url(submission.video_url, submission.platform)

    conditions = [OutlierItem.video_url == submission.video_url]
    if canonical_url:
        conditions.append(OutlierItem.canonical_url == canonical_url)

    existing_item_result = await db.execute(
        select(OutlierItem).where(or_(*conditions))
    )
    existing_item = existing_item_result.scalar_one_or_none()
    if existing_item:
        submission.outlier_item_id = existing_item.id
        submission.status = CreatorSubmissionStatus.TRACKING
        submission.tracking_started_at = utcnow()
        await db.commit()

        return PromoteResponse(
            submission_id=str(submission.id),
            outlier_item_id=str(existing_item.id),
            status="TRACKING",
            message="✅ 제출이 승격되었습니다. 14일간 지표를 추적합니다."
        )

    source_result = await db.execute(
        select(OutlierSource).where(OutlierSource.name == "creator_submission")
    )
    source = source_result.scalar_one_or_none()
    if not source:
        source = OutlierSource(
            name="creator_submission",
            base_url="internal",
            auth_type="none",
            auth_config=None,
        )
        db.add(source)
        await db.flush()

    # Create OutlierItem
    outlier_item = OutlierItem(
        id=uuid_module.uuid4(),
        source_id=source.id,
        external_id=f"creator_{submission.id}",
        video_url=submission.video_url,
        platform=submission.platform,
        category=pattern.category if pattern else "creator_submission",
        title=f"[Creator] {user.display_name or user.email if user else 'Unknown'} - {submission.pattern_id}",
        view_count=0,
        like_count=0,
        outlier_score=0.0,
        outlier_tier=None,
        status=OutlierItemStatus.SELECTED,
        analysis_status="pending",
        crawled_at=utcnow(),
        canonical_url=canonical_url,
        raw_payload={
            "pattern_id": submission.pattern_id,
            "creator_notes": submission.creator_notes,
            "invariant_checklist": submission.invariant_checklist,
            "submission_id": str(submission.id),
            "submission_type": "pattern_based",
        }
    )
    db.add(outlier_item)
    await db.flush()
    
    # Update submission
    submission.outlier_item_id = outlier_item.id
    submission.status = CreatorSubmissionStatus.TRACKING
    submission.tracking_started_at = utcnow()
    
    await db.commit()
    
    return PromoteResponse(
        submission_id=str(submission.id),
        outlier_item_id=str(outlier_item.id),
        status="TRACKING",
        message="✅ 제출이 승격되었습니다. 14일간 지표를 추적합니다."
    )


@router.get("/admin/pending", response_model=SubmissionListResponse)
async def list_pending_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
):
    """List all pending submissions for admin review"""
    result = await db.execute(
        select(CreatorSubmission)
        .where(CreatorSubmission.status == CreatorSubmissionStatus.PENDING)
        .order_by(CreatorSubmission.submitted_at.desc())
        .limit(limit)
    )
    submissions = result.scalars().all()
    
    return SubmissionListResponse(
        total=len(submissions),
        submissions=[
            SubmissionListItem(
                id=str(s.id),
                pattern_id=s.pattern_id,
                video_url=s.video_url,
                platform=s.platform,
                status=s.status.value if hasattr(s.status, 'value') else str(s.status),
                submitted_at=s.submitted_at,
                final_view_count=s.final_view_count,
                performance_vs_baseline=s.performance_vs_baseline,
            )
            for s in submissions
        ]
    )
