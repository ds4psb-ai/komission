"""
O2O Campaign Router - Location-based Verification
"""
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.time import utcnow

from app.database import get_db
from app.models import O2OLocation, O2OCampaign, O2OApplication, O2OApplicationStatus, User
from app.routers.auth import get_current_user

router = APIRouter()


# --- Utils ---

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in meters between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000 # Radius of earth in meters
    return c * r


# --- Schemas ---

class O2OLocationResponse(BaseModel):
    id: str
    location_id: str
    place_name: str
    address: str
    lat: float
    lng: float
    campaign_type: str
    campaign_title: str
    brand: Optional[str]
    reward_points: int
    reward_product: Optional[str]
    active_end: datetime

    class Config:
        from_attributes = True


class O2OCampaignResponse(BaseModel):
    id: str
    campaign_type: str
    campaign_title: str
    brand: Optional[str]
    category: Optional[str]
    reward_points: int
    reward_product: Optional[str]
    description: Optional[str]
    fulfillment_steps: Optional[List[str]]
    place_name: Optional[str]
    address: Optional[str]
    active_start: datetime
    active_end: datetime
    max_participants: Optional[int]


class O2OApplicationResponse(BaseModel):
    id: str
    campaign_id: str
    campaign_title: str
    campaign_type: str
    status: str
    created_at: datetime

class VerifyRequest(BaseModel):
    lat: float
    lng: float
    location_id: str


# --- Endpoints ---

@router.get("/locations", response_model=List[O2OLocationResponse])
async def list_active_locations(db: AsyncSession = Depends(get_db)):
    """List all currently active O2O campaign locations"""
    now = utcnow()
    query = select(O2OLocation).where(
        (O2OLocation.active_start <= now) & 
        (O2OLocation.active_end >= now)
    )
    result = await db.execute(query)
    locations = result.scalars().all()
    
    return [
        O2OLocationResponse(
            id=str(loc.id),
            location_id=loc.location_id,
            place_name=loc.place_name,
            address=loc.address,
            lat=loc.lat,
            lng=loc.lng,
            campaign_type=loc.campaign_type,
            campaign_title=loc.campaign_title,
            brand=loc.brand,
            reward_points=loc.reward_points,
            reward_product=loc.reward_product,
            active_end=loc.active_end
        ) for loc in locations
    ]


@router.get("/campaigns", response_model=List[O2OCampaignResponse])
async def list_active_campaigns(db: AsyncSession = Depends(get_db)):
    """List all active O2O campaigns (visit/instant/shipment)"""
    now = utcnow()

    location_query = select(O2OLocation).where(
        (O2OLocation.active_start <= now) &
        (O2OLocation.active_end >= now)
    )
    location_result = await db.execute(location_query)
    locations = location_result.scalars().all()

    campaign_query = select(O2OCampaign).where(
        (O2OCampaign.active_start <= now) &
        (O2OCampaign.active_end >= now)
    )
    campaign_result = await db.execute(campaign_query)
    campaigns = campaign_result.scalars().all()

    cards: List[O2OCampaignResponse] = []

    for loc in locations:
        cards.append(
            O2OCampaignResponse(
                id=str(loc.id),
                campaign_type="visit",
                campaign_title=loc.campaign_title,
                brand=loc.brand,
                category=loc.category,
                reward_points=loc.reward_points,
                reward_product=loc.reward_product,
                description=None,
                fulfillment_steps=["위치 인증", "촬영"],
                place_name=loc.place_name,
                address=loc.address,
                active_start=loc.active_start,
                active_end=loc.active_end,
                max_participants=loc.max_participants,
            )
        )

    for camp in campaigns:
        steps = None
        if isinstance(camp.fulfillment_steps, dict):
            steps = camp.fulfillment_steps.get("steps")
        elif isinstance(camp.fulfillment_steps, list):
            steps = camp.fulfillment_steps

        cards.append(
            O2OCampaignResponse(
                id=str(camp.id),
                campaign_type=camp.campaign_type,
                campaign_title=camp.campaign_title,
                brand=camp.brand,
                category=camp.category,
                reward_points=camp.reward_points,
                reward_product=camp.reward_product,
                description=camp.description,
                fulfillment_steps=steps,
                place_name=None,
                address=None,
                active_start=camp.active_start,
                active_end=camp.active_end,
                max_participants=camp.max_participants,
            )
        )

    cards.sort(key=lambda item: item.reward_points, reverse=True)
    return cards


@router.post("/campaigns/{campaign_id}/apply", response_model=O2OApplicationResponse)
async def apply_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply to an instant/shipment campaign"""
    query = select(O2OCampaign).where(O2OCampaign.campaign_id == campaign_id)
    campaign = (await db.execute(query)).scalar_one_or_none()

    if not campaign:
        try:
            campaign_uuid = uuid.UUID(campaign_id)
        except ValueError:
            campaign_uuid = None
        if campaign_uuid:
            campaign = await db.get(O2OCampaign, campaign_uuid)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    now = utcnow()
    if not (campaign.active_start <= now <= campaign.active_end):
        raise HTTPException(status_code=400, detail="Campaign is not active")

    existing_query = select(O2OApplication).where(
        (O2OApplication.campaign_id == campaign.id) &
        (O2OApplication.user_id == current_user.id)
    )
    existing = (await db.execute(existing_query)).scalar_one_or_none()

    if existing:
        return O2OApplicationResponse(
            id=str(existing.id),
            campaign_id=str(campaign.id),
            campaign_title=campaign.campaign_title,
            campaign_type=campaign.campaign_type,
            status=existing.status,
            created_at=existing.created_at,
        )

    application = O2OApplication(
        campaign_id=campaign.id,
        user_id=current_user.id,
        status=O2OApplicationStatus.APPLIED,
    )
    db.add(application)
    await db.flush()

    return O2OApplicationResponse(
        id=str(application.id),
        campaign_id=str(campaign.id),
        campaign_title=campaign.campaign_title,
        campaign_type=campaign.campaign_type,
        status=application.status,
        created_at=application.created_at,
    )


@router.get("/applications/me", response_model=List[O2OApplicationResponse])
async def list_my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's O2O campaign applications"""
    query = select(O2OApplication, O2OCampaign).join(
        O2OCampaign, O2OApplication.campaign_id == O2OCampaign.id
    ).where(O2OApplication.user_id == current_user.id)
    result = await db.execute(query)

    applications: List[O2OApplicationResponse] = []
    for application, campaign in result.all():
        applications.append(
            O2OApplicationResponse(
                id=str(application.id),
                campaign_id=str(campaign.id),
                campaign_title=campaign.campaign_title,
                campaign_type=campaign.campaign_type,
                status=application.status,
                created_at=application.created_at,
            )
        )

    return applications


@router.post("/verify")
async def verify_location(
    data: VerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user's location against a campaign location.
    If within 100m, award points.
    """
    # 1. Get Location
    result = await db.execute(select(O2OLocation).where(O2OLocation.location_id == data.location_id))
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    # 2. Check Validity (Date)
    now = utcnow()
    if not (location.active_start <= now <= location.active_end):
        raise HTTPException(status_code=400, detail="Campaign is not active")
        
    # 3. Check Distance (GPS)
    distance = haversine(data.lng, data.lat, location.lng, location.lat)
    if distance > 100: # 100 meters radius
        raise HTTPException(status_code=400, detail=f"Too far from location ({int(distance)}m)")
        
    # 4. Award Points (Idempotency check could be added here via a separate History table)
    # For MVP, we just add points directly.
    current_user.k_points += location.reward_points
    await db.commit()
    
    return {
        "status": "verified",
        "points_awarded": location.reward_points,
        "total_points": current_user.k_points,
        "distance": int(distance),
        "message": f"Successfully verified at {location.place_name}!"
    }


# ==================
# Admin Endpoints
# ==================

class CreateCampaignRequest(BaseModel):
    campaign_type: str  # instant, shipment, visit
    campaign_title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    reward_points: int = 0
    reward_product: Optional[str] = None
    fulfillment_steps: Optional[List[str]] = None
    active_days: int = 30  # Days from now
    max_participants: Optional[int] = None


class UpdateApplicationStatusRequest(BaseModel):
    status: str  # selected, shipped, delivered, completed, rejected
    tracking_number: Optional[str] = None


class ApplicationDetailResponse(BaseModel):
    id: str
    campaign_id: str
    campaign_title: str
    campaign_type: str
    user_id: str
    user_email: str
    user_name: Optional[str]
    status: str
    shipment_tracking: Optional[str]
    created_at: datetime
    updated_at: datetime


def require_admin(user: User) -> None:
    """Helper to check admin role"""
    if user.role not in ("admin", "brand"):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/admin/applications", response_model=List[ApplicationDetailResponse])
async def list_all_applications(
    status_filter: Optional[str] = None,
    campaign_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] List all campaign applications with optional filters"""
    require_admin(current_user)
    
    query = select(O2OApplication, O2OCampaign, User).join(
        O2OCampaign, O2OApplication.campaign_id == O2OCampaign.id
    ).join(
        User, O2OApplication.user_id == User.id
    )
    
    if status_filter:
        query = query.where(O2OApplication.status == status_filter)
    if campaign_id:
        query = query.where(O2OCampaign.campaign_id == campaign_id)
    
    query = query.order_by(O2OApplication.created_at.desc())
    result = await db.execute(query)
    
    applications: List[ApplicationDetailResponse] = []
    for app, campaign, user in result.all():
        applications.append(
            ApplicationDetailResponse(
                id=str(app.id),
                campaign_id=str(campaign.id),
                campaign_title=campaign.campaign_title,
                campaign_type=campaign.campaign_type,
                user_id=str(user.id),
                user_email=user.email,
                user_name=user.name,
                status=app.status.value if hasattr(app.status, 'value') else app.status,
                shipment_tracking=app.shipment_tracking,
                created_at=app.created_at,
                updated_at=app.updated_at,
            )
        )
    
    return applications


@router.patch("/admin/applications/{application_id}")
async def update_application_status(
    application_id: str,
    data: UpdateApplicationStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Update application status (approve/ship/complete/reject)"""
    require_admin(current_user)
    
    try:
        app_uuid = uuid.UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    application = await db.get(O2OApplication, app_uuid)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Validate status transition
    valid_statuses = {"selected", "shipped", "delivered", "completed", "rejected"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Update status
    application.status = O2OApplicationStatus(data.status)
    if data.tracking_number:
        application.shipment_tracking = data.tracking_number
    
    await db.commit()
    
    return {
        "id": str(application.id),
        "status": application.status.value if hasattr(application.status, 'value') else application.status,
        "tracking_number": application.shipment_tracking,
        "message": f"Application updated to {data.status}"
    }


@router.post("/admin/campaigns", response_model=O2OCampaignResponse)
async def create_campaign(
    data: CreateCampaignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Create a new O2O campaign"""
    require_admin(current_user)
    
    from datetime import timedelta
    
    now = utcnow()
    campaign = O2OCampaign(
        campaign_id=f"campaign_{now.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
        campaign_type=data.campaign_type,
        campaign_title=data.campaign_title,
        brand=data.brand,
        category=data.category,
        description=data.description,
        reward_points=data.reward_points,
        reward_product=data.reward_product,
        fulfillment_steps={"steps": data.fulfillment_steps} if data.fulfillment_steps else None,
        active_start=now,
        active_end=now + timedelta(days=data.active_days),
        max_participants=data.max_participants,
    )
    
    db.add(campaign)
    await db.flush()
    
    return O2OCampaignResponse(
        id=str(campaign.id),
        campaign_type=campaign.campaign_type,
        campaign_title=campaign.campaign_title,
        brand=campaign.brand,
        category=campaign.category,
        reward_points=campaign.reward_points,
        reward_product=campaign.reward_product,
        description=campaign.description,
        fulfillment_steps=data.fulfillment_steps,
        place_name=None,
        address=None,
        active_start=campaign.active_start,
        active_end=campaign.active_end,
        max_participants=campaign.max_participants,
    )


@router.get("/admin/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Get statistics for a campaign"""
    require_admin(current_user)
    
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID")
    
    campaign = await db.get(O2OCampaign, campaign_uuid)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Count applications by status
    from sqlalchemy import func
    stats_query = select(
        O2OApplication.status,
        func.count(O2OApplication.id).label("count")
    ).where(
        O2OApplication.campaign_id == campaign_uuid
    ).group_by(O2OApplication.status)
    
    result = await db.execute(stats_query)
    status_counts = {row.status.value if hasattr(row.status, 'value') else row.status: row.count for row in result.all()}
    
    total = sum(status_counts.values())
    
    return {
        "campaign_id": str(campaign.id),
        "campaign_title": campaign.campaign_title,
        "total_applications": total,
        "max_participants": campaign.max_participants,
        "status_breakdown": status_counts,
        "fill_rate": round(total / campaign.max_participants * 100, 1) if campaign.max_participants else None,
    }

