"""
O2O Campaign Router - Location-based Verification
"""
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import O2OLocation, User
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
