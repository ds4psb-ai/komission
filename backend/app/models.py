"""
SQLAlchemy Models for Komission FACTORY v5.2
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum, Float
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


class O2OApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    SELECTED = "selected"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    REJECTED = "rejected"


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
    
    # Curator System - Special permissions for dev curators
    is_curator: Mapped[bool] = mapped_column(Boolean, default=False)
    curator_since: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
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
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # fashion, beauty, food, lifestyle
    
    # Rewards
    reward_points: Mapped[int] = mapped_column(Integer, default=0)
    reward_product: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Validity
    verification_method: Mapped[str] = mapped_column(String(50))  # gps_match, receipt_scan, timestamp
    active_start: Mapped[datetime] = mapped_column(DateTime)
    active_end: Mapped[datetime] = mapped_column(DateTime)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class O2OCampaign(Base):
    """Non-location O2O campaigns (instant/shipment)"""
    __tablename__ = "o2o_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    campaign_type: Mapped[str] = mapped_column(String(50))  # instant, shipment
    campaign_title: Mapped[str] = mapped_column(String(255))
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reward_points: Mapped[int] = mapped_column(Integer, default=0)
    reward_product: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fulfillment_steps: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    active_start: Mapped[datetime] = mapped_column(DateTime)
    active_end: Mapped[datetime] = mapped_column(DateTime)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class O2OApplication(Base):
    """User application for shipment/instant O2O campaigns"""
    __tablename__ = "o2o_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("o2o_campaigns.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(SQLEnum(O2OApplicationStatus), default=O2OApplicationStatus.APPLIED)
    shipment_tracking: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


# ==================
# GAMIFICATION SYSTEM (Expert Recommendation)
# ==================

class BadgeType(str, enum.Enum):
    """Badge types for gamification"""
    FIRST_FORK = "first_fork"           # 🍽️ 첫 포크
    VIRAL_MAKER = "viral_maker"         # 🚀 바이럴 메이커 (+50% 성장률)
    SPEED_RUNNER = "speed_runner"       # ⚡ 스피드러너 (24h 내 3개 리믹스)
    ORIGINAL_CREATOR = "original_creator"  # 👨‍👧‍👦 내 포크가 또 Fork됨
    COLLABORATOR = "collaborator"       # 🤝 퀘스트에서 수익 얻기
    STREAK_3 = "streak_3"               # 🔥 3일 연속
    STREAK_7 = "streak_7"               # 🔥🔥 7일 연속
    STREAK_30 = "streak_30"             # 🔥🔥🔥 30일 연속


class UserBadge(Base):
    """User's earned badges"""
    __tablename__ = "user_badges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    badge_type: Mapped[str] = mapped_column(SQLEnum(BadgeType))
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Optional context (e.g., which node earned this badge)
    context_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", backref="badges")


class UserStreak(Base):
    """User's daily activity streak tracking"""
    __tablename__ = "user_streaks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True)
    
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # K-Points earned from streaks
    streak_points_earned: Mapped[int] = mapped_column(Integer, default=0)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MissionType(str, enum.Enum):
    """Daily mission types"""
    APP_OPEN = "app_open"           # 앱 접속
    FIRST_FILMING = "first_filming" # 첫 촬영
    QUEST_ACCEPT = "quest_accept"   # 퀘스트 수락
    FORK_CREATE = "fork_create"     # 포크 생성


class DailyMission(Base):
    """User's daily mission completion tracking"""
    __tablename__ = "daily_missions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    mission_type: Mapped[str] = mapped_column(SQLEnum(MissionType))
    mission_date: Mapped[datetime] = mapped_column(DateTime)  # Date of the mission
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# --- Feedback Loop System (Pattern Learning) ---

class PatternPrediction(Base):
    """
    개별 예측 기록
    영상 분석 시 생성된 패턴별 예측값 저장
    """
    __tablename__ = "pattern_predictions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[str] = mapped_column(String(100), index=True)  # RemixNode.node_id
    
    # 패턴 정보
    pattern_code: Mapped[str] = mapped_column(String(100), index=True)  # e.g., "VIS_RAPID_CUT"
    pattern_type: Mapped[str] = mapped_column(String(20))  # "visual" | "audio" | "semantic"
    segment_index: Mapped[int] = mapped_column(Integer, default=0)  # Viral Mosaic 인덱스
    
    # 예측값
    predicted_retention: Mapped[float] = mapped_column(default=0.5)
    
    # 실제값 (나중에 채워짐)
    actual_retention: Mapped[Optional[float]] = mapped_column(nullable=True)
    prediction_error: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # 검증 정보
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verification_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "tiktok_api" | "youtube_api" | "manual"
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PatternConfidence(Base):
    """
    패턴별 신뢰도 (집계 테이블)
    실제 성과 데이터가 쌓일수록 정확도 향상
    """
    __tablename__ = "pattern_confidences"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 패턴 식별
    pattern_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # e.g., "VIS_RAPID_CUT"
    pattern_type: Mapped[str] = mapped_column(String(20))  # "visual" | "audio" | "semantic"
    
    # 신뢰도 통계
    sample_count: Mapped[int] = mapped_column(Integer, default=0)  # 검증된 샘플 수
    avg_absolute_error: Mapped[float] = mapped_column(default=0.0)  # 평균 절대 오차
    confidence_score: Mapped[float] = mapped_column(default=0.5)  # 0.0 ~ 1.0 (높을수록 신뢰)
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================
# EVIDENCE LOOP SYSTEM (Phase 4)
# ==================

class OutlierSource(Base):
    """
    외부 아웃라이어 소스 사이트
    크롤링 대상 사이트 관리
    """
    __tablename__ = "outlier_sources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))  # "TrendAnalyzer", "ViralHunter"
    base_url: Mapped[str] = mapped_column(String(500))
    auth_type: Mapped[str] = mapped_column(String(50))  # "api_key", "session", "none"
    auth_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 인증 설정
    
    # 크롤링 상태
    last_crawled: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    crawl_interval_hours: Mapped[int] = mapped_column(Integer, default=24)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    items: Mapped[List["OutlierItem"]] = relationship("OutlierItem", back_populates="source")


class OutlierItemStatus(str, enum.Enum):
    PENDING = "pending"        # 수집됨, 미검토
    SELECTED = "selected"      # Parent 후보로 선정
    REJECTED = "rejected"      # 제외됨
    PROMOTED = "promoted"      # RemixNode(Parent)로 승격됨


class OutlierItem(Base):
    """
    크롤링된 아웃라이어 후보
    외부 소스에서 발견된 바이럴 콘텐츠
    """
    __tablename__ = "outlier_items"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlier_sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)  # 소스별 고유ID
    
    # 콘텐츠 정보
    video_url: Mapped[str] = mapped_column(String(500))
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    platform: Mapped[str] = mapped_column(String(50))  # tiktok, instagram, youtube
    category: Mapped[str] = mapped_column(String(50), index=True)  # beauty, meme, food...
    
    # 크롤링 시 수집된 메트릭
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    share_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    growth_rate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "+350%"
    
    # Extended Metrics (for Outlier Detection)
    outlier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outlier_tier: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)  # S/A/B/C
    creator_avg_views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 선별 상태
    status: Mapped[str] = mapped_column(SQLEnum(OutlierItemStatus), default=OutlierItemStatus.PENDING)
    promoted_to_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )  # Parent로 승격된 경우
    
    # VDG Analysis Gate (Admin 승인 후에만 분석)
    analysis_status: Mapped[str] = mapped_column(
        String(20), default="pending"  # pending | approved | analyzing | completed | skipped
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Best Comments (바이럴 인간 지표)
    best_comments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    # [{"text": "...", "likes": 1000, "lang": "ko", "translation_en": "..."}, ...]
    
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source: Mapped["OutlierSource"] = relationship("OutlierSource", back_populates="items")
    promoted_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode", foreign_keys=[promoted_to_node_id])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])


class MetricDaily(Base):
    """
    일별 성과 추적 (14일+)
    노드별 일일 메트릭 히스토리
    """
    __tablename__ = "metric_daily"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("remix_nodes.id"), index=True)
    
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # 절대값
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    share_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 전일 대비 증분
    delta_views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    delta_rate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "+15%"
    
    # 데이터 소스
    data_source: Mapped[str] = mapped_column(String(50), default="manual")  # manual, api, crawler
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node: Mapped["RemixNode"] = relationship("RemixNode", backref="daily_metrics")


class EvidenceSnapshot(Base):
    """
    증거 스냅샷 (VDG 요약)
    Parent 노드의 변주 성과 요약
    """
    __tablename__ = "evidence_snapshots"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("remix_nodes.id"), index=True)
    
    # 스냅샷 기간
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    period: Mapped[str] = mapped_column(String(10))  # "4w", "12w", "1y"
    
    # 집계 데이터 (JSONB)
    # 예: {"audio": {"VIS_KPOP": {"success_rate": 0.85, "sample_count": 12, "avg_delta": "+127%"}}}
    depth1_summary: Mapped[dict] = mapped_column(JSONB)  # 변주별 성공률
    depth2_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # 최고/최저 변주
    top_mutation_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # audio, visual
    top_mutation_pattern: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    top_mutation_rate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # 통계
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(default=0.5)
    
    # 시트 연동
    sheet_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    sheet_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_node: Mapped["RemixNode"] = relationship("RemixNode", backref="evidence_snapshots")


class NotebookLibraryEntry(Base):
    """
    NotebookLM 요약 결과를 DB에 래핑한 라이브러리 엔트리
    + 코드 기반 분석 스키마 (15_FINAL_ARCHITECTURE.md 기반)
    """
    __tablename__ = "notebook_library"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(50))
    summary: Mapped[dict] = mapped_column(JSONB)
    cluster_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    parent_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )
    
    # NEW: 코드 기반 분석 스키마 (Gemini 3.0 Pro Structured Output)
    analysis_schema: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    schema_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "v1.0"

    # Temporal variation signals (17_TEMPORAL_VARIATION_THEORY.md)
    temporal_phase: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    variant_age_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    novelty_decay_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    burstiness_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parent_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")


# ==================
# PATTERN CLUSTERING (15_FINAL_ARCHITECTURE.md)
# ==================

class PatternCluster(Base):
    """
    유사도 클러스터
    Parent-Kids 변주 패턴을 데이터화, 뎁스 구조를 축적
    """
    __tablename__ = "pattern_clusters"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # "Hook-2s-TextPunch"
    cluster_name: Mapped[str] = mapped_column(String(255))
    pattern_type: Mapped[str] = mapped_column(String(50))  # "visual" | "audio" | "semantic"
    
    # 통계
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_outlier_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    representative_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    representative_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")


# ==================
# OPAL TEMPLATE SEEDS (15_FINAL_ARCHITECTURE.md)
# ==================

class TemplateSeed(Base):
    """
    Opal 템플릿 시드
    초기 템플릿/노드 설계 시드 저장
    """
    __tablename__ = "template_seeds"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seed_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # 연관 노드/클러스터
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )
    cluster_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # 템플릿 정보
    template_type: Mapped[str] = mapped_column(String(50))  # "capsule" | "guide" | "edit"
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    seed_json: Mapped[dict] = mapped_column(JSONB)  # 템플릿 시드 JSON
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")


# ==================
# PHASE 3: CREATOR PERSONA (암묵 신호 기반)
# Based on 04_TECHNICAL_OVERVIEW.md & 16_PDR.md
# ==================

class BehaviorEventType(str, enum.Enum):
    """행동 이벤트 유형"""
    TEMPLATE_OPEN = "template_open"
    SLOT_CHANGE = "slot_change"
    RUN_START = "run_start"
    RUN_COMPLETE = "run_complete"
    REWATCH = "rewatch"
    ABANDON = "abandon"
    EXPORT = "export"
    QUEST_APPLY = "quest_apply"
    CALIBRATION_CHOICE = "calibration_choice"


class CreatorBehaviorEvent(Base):
    """
    크리에이터 행동 이벤트 로그
    암묵 신호 기반 페르소나 추론용
    """
    __tablename__ = "creator_behavior_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    event_type: Mapped[str] = mapped_column(SQLEnum(BehaviorEventType))
    
    # 관련 엔티티 (optional)
    node_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # 이벤트 상세 데이터
    payload_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class CreatorStyleFingerprint(Base):
    """
    크리에이터 스타일 지문
    행동/콘텐츠 신호 기반 자동 생성
    """
    __tablename__ = "creator_style_fingerprints"
    
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    
    # 스타일 벡터 (톤/페이스/훅/자막밀도/샷구성 등)
    style_vector: Mapped[dict] = mapped_column(JSONB)
    
    # 최근 30일 행동/성과 요약
    signal_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # 메타데이터
    version: Mapped[str] = mapped_column(String(20), default="v1.0")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CalibrationChoice(str, enum.Enum):
    """Taste Calibration 선택"""
    A = "A"
    B = "B"


class CreatorCalibrationChoice(Base):
    """
    Taste Calibration 선택 기록
    1분 페어 선택으로 선호 벡터 보정
    """
    __tablename__ = "creator_calibration_choices"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    
    # 페어 정보
    pair_id: Mapped[str] = mapped_column(String(100))
    option_a_id: Mapped[str] = mapped_column(String(100))
    option_b_id: Mapped[str] = mapped_column(String(100))
    
    # 선택
    selected: Mapped[str] = mapped_column(SQLEnum(CalibrationChoice))
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ==================
# TEMPLATE VERSIONING & RL-LITE (15_FINAL_ARCHITECTURE.md)
# ==================

class TemplateVersion(Base):
    """
    템플릿 버전 관리
    템플릿 변경 이력을 추적하여 RL-lite 학습 기반 마련
    """
    __tablename__ = "template_versions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 연관 노드/시드
    parent_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )
    seed_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("template_seeds.id"), nullable=True
    )
    
    # 버전 정보
    version: Mapped[str] = mapped_column(String(20))  # v1.0, v1.1, etc.
    template_json: Mapped[dict] = mapped_column(JSONB)  # 템플릿 스냅샷
    
    # 변경 사유
    change_type: Mapped[str] = mapped_column(String(50))  # "manual", "feedback_driven", "rl_update"
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 성과 연결
    performance_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # 메타데이터
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")
    seed: Mapped[Optional["TemplateSeed"]] = relationship("TemplateSeed")


class FeedbackType(str, enum.Enum):
    """피드백 유형"""
    TOO_HARD = "too_hard"
    TOO_EASY = "too_easy"
    UNCLEAR = "unclear"
    GREAT = "great"
    NEEDS_EXAMPLE = "needs_example"
    WRONG_TIMING = "wrong_timing"
    OTHER = "other"


class TemplateFeedback(Base):
    """
    템플릿 사용자 피드백
    Creator 피드백을 수집하여 RL-lite 정책 업데이트에 활용
    """
    __tablename__ = "template_feedback"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 연관 엔티티
    template_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("template_versions.id"), nullable=True
    )
    node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    
    # 피드백 내용
    feedback_type: Mapped[str] = mapped_column(SQLEnum(FeedbackType))
    rating: Mapped[int] = mapped_column(Integer)  # 1-5 stars
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 컨텍스트
    completion_status: Mapped[str] = mapped_column(String(50))  # "completed", "abandoned", "partial"
    time_spent_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template_version: Mapped[Optional["TemplateVersion"]] = relationship("TemplateVersion")
    node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")


# ==================
# EVIDENCE BOARDS (Virlo Phase B - Collections Alternative)
# ==================

class EvidenceBoardStatus(str, enum.Enum):
    """Evidence Board status"""
    DRAFT = "draft"
    ACTIVE = "active"
    CONCLUDED = "concluded"


class EvidenceBoard(Base):
    """
    Evidence Board - Experiment grouping with KPI tracking
    Replaces Virlo's Collections concept with Evidence-first approach
    """
    __tablename__ = "evidence_boards"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Board info
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Owner
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # KPI and Conclusion
    kpi_target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # "ROAS > 2.0", "CTR > 5%"
    conclusion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # "Variant A wins by 35%"
    winner_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(SQLEnum(EvidenceBoardStatus), default=EvidenceBoardStatus.DRAFT)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    concluded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", backref="evidence_boards")
    items: Mapped[List["EvidenceBoardItem"]] = relationship("EvidenceBoardItem", back_populates="board", cascade="all, delete-orphan")


class EvidenceBoardItem(Base):
    """
    Items in an Evidence Board
    Can reference OutlierItems or RemixNodes
    """
    __tablename__ = "evidence_board_items"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent board
    board_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evidence_boards.id"), index=True)
    
    # Referenced item (one of these should be set)
    outlier_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outlier_items.id"), nullable=True
    )
    remix_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    board: Mapped["EvidenceBoard"] = relationship("EvidenceBoard", back_populates="items")
    outlier_item: Mapped[Optional["OutlierItem"]] = relationship("OutlierItem")
    remix_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")


# ==================
# NOTEBOOK SOURCE PACK (17_NOTEBOOKLM_LIBRARY_STRATEGY.md)
# ==================

class NotebookSourcePack(Base):
    """
    NotebookLM Source Pack 기록
    클러스터별 생성된 Source Pack을 추적하여 NotebookLM 입력 일관성 보장
    """
    __tablename__ = "notebook_source_packs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[str] = mapped_column(String(100), index=True)
    
    # Pack 타입 및 파일 정보
    pack_type: Mapped[str] = mapped_column(String(50))  # "sheet" | "docx"
    drive_file_id: Mapped[str] = mapped_column(String(100))  # Google Drive file ID
    drive_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Full URL for convenience
    
    # 버전 관리
    source_version: Mapped[str] = mapped_column(String(50), default="v1.0")  # Pack 생성 시 스키마 버전
    entry_count: Mapped[int] = mapped_column(Integer, default=0)  # 포함된 엔트리 수
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
