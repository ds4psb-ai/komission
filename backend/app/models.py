"""
SQLAlchemy Models for Komission FACTORY v5.2
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.database import Base


class NodeLayer(str, enum.Enum):
    MASTER = "master"
    FORK = "fork"
    FORK_OF_FORK = "fork_of_fork"


class NodePermission(str, enum.Enum):
    READ_ONLY = "read_only"
    FULL_EDIT = "full_edit"
    CAMPAIGN_PROTECTED = "campaign_protected"


class NodeGovernance(str, enum.Enum):
    OPEN_COMMUNITY = "open_community"
    BRAND_OFFICIAL = "brand_official"
    CREATOR_VERIFIED = "creator_verified"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="user")  # user, admin, brand, creator
    profile_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Google profile URL
    k_points: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Creator Royalty System
    total_royalty_received: Mapped[int] = mapped_column(Integer, default=0)  # Lifetime royalty earned
    pending_royalty: Mapped[int] = mapped_column(Integer, default=0)         # Unsettled royalty
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    remix_nodes: Mapped[List["RemixNode"]] = relationship("RemixNode", back_populates="creator")
    pipelines: Mapped[List["Pipeline"]] = relationship("Pipeline", back_populates="creator")


class RemixNode(Base):
    __tablename__ = "remix_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # remix_20251222_001
    title: Mapped[str] = mapped_column(String(255))
    
    # Layer & Governance
    layer: Mapped[str] = mapped_column(SQLEnum(NodeLayer), default=NodeLayer.FORK)
    permission: Mapped[str] = mapped_column(SQLEnum(NodePermission), default=NodePermission.FULL_EDIT)
    governed_by: Mapped[str] = mapped_column(SQLEnum(NodeGovernance), default=NodeGovernance.OPEN_COMMUNITY)
    genealogy_depth: Mapped[int] = mapped_column(Integer, default=0)
    
    # Parent/Child relationship (Genealogy Graph)
    parent_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True)
    mutation_profile: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    performance_delta: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "+350%", "-50%"
    
    # AI Analysis
    gemini_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    claude_brief: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Generated Content Paths
    storyboard_images: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # {"shot_1": "s3://...", ...}
    audio_guide_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Source Video
    source_video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # tiktok, instagram, youtube
    
    # O2O Campaign
    campaign_context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    brand_campaign: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Metadata
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    owner_type: Mapped[str] = mapped_column(String(20), default="user")  # admin, brand, user
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Creator Royalty System
    total_fork_count: Mapped[int] = mapped_column(Integer, default=0)         # Number of times forked
    total_royalty_earned: Mapped[int] = mapped_column(Integer, default=0)     # Total points generated for creator
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="remix_nodes")
    children: Mapped[List["RemixNode"]] = relationship("RemixNode", back_populates="parent", remote_side=[id])
    parent: Mapped[Optional["RemixNode"]] = relationship("RemixNode", back_populates="children", remote_side=[parent_node_id])


class UserVideo(Base):
    """User-submitted videos for K-Success certification"""
    __tablename__ = "user_videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    remix_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("remix_nodes.id"))
    
    video_url: Mapped[str] = mapped_column(String(500))
    platform: Mapped[str] = mapped_column(String(50))  # tiktok, instagram
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # K-Success Certification
    is_k_success: Mapped[bool] = mapped_column(Boolean, default=False)
    certification_proof: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # screenshot, link
    certified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class O2OLocation(Base):
    """O2O Campaign Locations"""
    __tablename__ = "o2o_locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    place_name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(Text)
    lat: Mapped[float] = mapped_column()
    lng: Mapped[float] = mapped_column()
    gmaps_place_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Campaign
    campaign_type: Mapped[str] = mapped_column(String(50))  # visit_challenge, product_trial
    campaign_title: Mapped[str] = mapped_column(String(255))
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Rewards
    reward_points: Mapped[int] = mapped_column(Integer, default=0)
    reward_product: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Validity
    verification_method: Mapped[str] = mapped_column(String(50))  # gps_match, receipt_scan, timestamp
    active_start: Mapped[datetime] = mapped_column(DateTime)
    active_end: Mapped[datetime] = mapped_column(DateTime)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Pipeline(Base):
    """Saved Canvas Pipelines (for Marketplace / User Templates)"""
    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    graph_data: Mapped[dict] = mapped_column(JSONB)  # React Flow JSON
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Owner
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="pipelines")


class RoyaltyReason(str, enum.Enum):
    """Reasons for royalty point generation"""
    FORK = "fork"                          # Someone forked this node
    VIEW_MILESTONE = "view_milestone"      # Fork reached view milestone
    K_SUCCESS = "k_success"                # Fork achieved K-Success certification
    GENEALOGY_BONUS = "genealogy_bonus"    # Bonus from descendant's success


class NodeRoyalty(Base):
    """
    Creator Royalty Transaction Log
    Tracks all royalty point transactions between users based on node usage.
    
    🛡️ Anti-Abuse Security:
    - forker_ip_hash: Prevents same IP from farming points
    - forker_device_fp: Prevents same device from farming points
    - is_impact_verified: Royalty only counts after fork reaches 100+ views
    """
    __tablename__ = "node_royalties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Creator (receives royalty)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # Source of royalty
    source_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("remix_nodes.id"))  # Original node
    forked_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True)  # Forked node (if applicable)
    forker_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # User who forked
    
    # 🛡️ Anti-Abuse Security Fields (CTO Mandated)
    forker_ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)      # SHA256 of IP
    forker_device_fp: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # Browser fingerprint
    is_impact_verified: Mapped[bool] = mapped_column(Boolean, default=False)              # True when fork hits 100 views
    
    # Points
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(SQLEnum(RoyaltyReason), default=RoyaltyReason.FORK)
    
    # Settlement tracking
    is_settled: Mapped[bool] = mapped_column(Boolean, default=False)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id], backref="royalties_received")
    source_node: Mapped["RemixNode"] = relationship("RemixNode", foreign_keys=[source_node_id])
    forked_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode", foreign_keys=[forked_node_id])
    forker: Mapped[Optional["User"]] = relationship("User", foreign_keys=[forker_id])


