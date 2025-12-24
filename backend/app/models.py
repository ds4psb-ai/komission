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
    
    # 선별 상태
    status: Mapped[str] = mapped_column(SQLEnum(OutlierItemStatus), default=OutlierItemStatus.PENDING)
    promoted_to_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )  # Parent로 승격된 경우
    
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source: Mapped["OutlierSource"] = relationship("OutlierSource", back_populates="items")
    promoted_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode", foreign_keys=[promoted_to_node_id])


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parent_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")
