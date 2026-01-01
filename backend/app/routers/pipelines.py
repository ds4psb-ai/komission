"""
Pipeline Router - Save/Load Canvas State
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Pipeline, User
from app.routers.auth import get_current_user

router = APIRouter()

# --- Constants ---
MAX_GRAPH_DATA_SIZE = 1024 * 1024  # 1MB max
MAX_NODES = 100
MAX_EDGES = 200

# --- Schemas ---

class PipelineCreate(BaseModel):
    title: str
    graph_data: dict  # React Flow JSON
    is_public: bool = False

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError('Title cannot be empty')
        if len(v) > 100:
            raise ValueError('Title must be 100 characters or less')
        return v.strip()

    @field_validator('graph_data')
    @classmethod
    def validate_graph_data(cls, v: dict) -> dict:
        if not isinstance(v, dict):
            raise ValueError('graph_data must be a dictionary')
        if 'nodes' not in v or 'edges' not in v:
            raise ValueError('graph_data must contain nodes and edges')
        if not isinstance(v.get('nodes'), list):
            raise ValueError('nodes must be a list')
        if not isinstance(v.get('edges'), list):
            raise ValueError('edges must be a list')
        if len(v.get('nodes', [])) > MAX_NODES:
            raise ValueError(f'Maximum {MAX_NODES} nodes allowed')
        if len(v.get('edges', [])) > MAX_EDGES:
            raise ValueError(f'Maximum {MAX_EDGES} edges allowed')
        return v

class PipelineUpdate(BaseModel):
    title: Optional[str] = None
    graph_data: Optional[dict] = None
    is_public: Optional[bool] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v.strip()) < 1:
            raise ValueError('Title cannot be empty')
        if len(v) > 100:
            raise ValueError('Title must be 100 characters or less')
        return v.strip()

    @field_validator('graph_data')
    @classmethod
    def validate_graph_data(cls, v: Optional[dict]) -> Optional[dict]:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError('graph_data must be a dictionary')
        if 'nodes' not in v or 'edges' not in v:
            raise ValueError('graph_data must contain nodes and edges')
        if len(v.get('nodes', [])) > MAX_NODES:
            raise ValueError(f'Maximum {MAX_NODES} nodes allowed')
        if len(v.get('edges', [])) > MAX_EDGES:
            raise ValueError(f'Maximum {MAX_EDGES} edges allowed')
        return v

class PipelineResponse(BaseModel):
    id: str
    title: str
    graph_data: dict
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# --- Helpers ---

def _validate_uuid(pipeline_id: str) -> UUID:
    """Validate and convert string to UUID"""
    try:
        return UUID(pipeline_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline ID format")

def _to_response(pipeline: Pipeline) -> PipelineResponse:
    """Convert Pipeline model to response schema"""
    return PipelineResponse(
        id=str(pipeline.id),
        title=pipeline.title,
        graph_data=pipeline.graph_data,
        is_public=pipeline.is_public,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at
    )

# --- Endpoints ---

@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    data: PipelineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save a new pipeline"""
    pipeline = Pipeline(
        title=data.title,
        graph_data=data.graph_data,
        is_public=data.is_public,
        user_id=current_user.id
    )
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    return _to_response(pipeline)

@router.get("/public", response_model=List[PipelineResponse])
async def list_public_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """List all public pipelines (Marketplace)"""
    result = await db.execute(
        select(Pipeline)
        .where(Pipeline.is_public == True)
        .order_by(Pipeline.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    pipelines = result.scalars().all()
    return [_to_response(p) for p in pipelines]

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List my saved pipelines"""
    result = await db.execute(
        select(Pipeline)
        .where(Pipeline.user_id == current_user.id)
        .order_by(Pipeline.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    pipelines = result.scalars().all()
    return [_to_response(p) for p in pipelines]

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Load a specific pipeline"""
    _validate_uuid(pipeline_id)
    
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Permission check: owner or public
    if pipeline.user_id != current_user.id and not pipeline.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return _to_response(pipeline)

@router.patch("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: str,
    data: PipelineUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing pipeline"""
    _validate_uuid(pipeline_id)
    
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if data.title is not None:
        pipeline.title = data.title
    if data.graph_data is not None:
        pipeline.graph_data = data.graph_data
    if data.is_public is not None:
        pipeline.is_public = data.is_public
        
    await db.commit()
    await db.refresh(pipeline)
    return _to_response(pipeline)

@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a pipeline"""
    _validate_uuid(pipeline_id)
    
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.delete(pipeline)
    await db.commit()

