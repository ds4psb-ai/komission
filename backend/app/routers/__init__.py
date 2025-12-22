"""
API Routers package
"""
from fastapi import APIRouter

# Main API router
api_router = APIRouter(prefix="/api/v1")

# Import and include sub-routers
from app.routers.remix import router as remix_router
from app.routers.auth import router as auth_router
from app.routers.o2o import router as o2o_router
from app.routers.royalty import router as royalty_router

api_router.include_router(remix_router, prefix="/remix", tags=["Remix"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(o2o_router, prefix="/o2o", tags=["O2O"])
api_router.include_router(royalty_router, tags=["Royalty"])

