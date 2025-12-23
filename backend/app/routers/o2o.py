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
    now = datetime.utcnow()
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
    now = datetime.utcnow()

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

    now = datetime.utcnow()
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
    now = datetime.utcnow()
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
