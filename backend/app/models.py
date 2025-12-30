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
from app.utils.time import utcnow


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


# ==================
# P0-1: RUN/ARTIFACT/IDEMPOTENCY LAYER (PEGL v1.0)
# ==================

class RunStatus(str, enum.Enum):
    """파이프라인 실행 상태"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunType(str, enum.Enum):
    """파이프라인 실행 유형"""
    CRAWLER = "crawler"
    ANALYSIS = "analysis"
    CLUSTERING = "clustering"
    EVIDENCE = "evidence"
    SOURCE_PACK = "source_pack"
    PATTERN_SYNTHESIS = "pattern_synthesis"
    DECISION = "decision"
    BANDIT = "bandit"


class Run(Base):
    """
    파이프라인 실행 기록 (PEGL Phase 0 핵심)
    - 모든 파이프라인은 Run을 생성해야 함
    - idempotency_key로 중복 실행 방지
    - 실패 시 원인 파악 1분 이내 목표
    """
    __tablename__ = "runs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # 사람 친화적 ID
    
    # 실행 유형 및 상태
    run_type: Mapped[str] = mapped_column(SQLEnum(RunType))
    status: Mapped[str] = mapped_column(SQLEnum(RunStatus), default=RunStatus.QUEUED)
    
    # Idempotency (동일 입력 재실행 방지)
    idempotency_key: Mapped[str] = mapped_column(String(64), index=True)  # SHA256 of inputs
    inputs_hash: Mapped[str] = mapped_column(String(64))  # SHA256 of canonical inputs
    inputs_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 원본 입력
    
    # 실행 시간
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 결과 요약
    result_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 메타데이터
    triggered_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "cron", "manual", "api"
    parent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )  # 중첩 실행용
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="run")
    parent_run: Mapped[Optional["Run"]] = relationship("Run", remote_side=[id])


class ArtifactType(str, enum.Enum):
    """아티팩트 유형"""
    RAW_DATA = "raw_data"
    ANALYSIS_SCHEMA = "analysis_schema"
    CLUSTER_RESULT = "cluster_result"
    SOURCE_PACK = "source_pack"
    PATTERN_LIBRARY = "pattern_library"
    EVIDENCE_SNAPSHOT = "evidence_snapshot"
    DECISION_OBJECT = "decision_object"
    TRANSCRIPT = "transcript"


class Artifact(Base):
    """
    파이프라인 산출물 (PEGL Phase 0 핵심)
    - 모든 산출물은 Artifact로 추적
    - storage_path로 실제 데이터 위치 참조
    - schema_version으로 버전 관리
    """
    __tablename__ = "artifacts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # 사람 친화적 ID
    
    # Run 연결
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("runs.id"), index=True)
    
    # 아티팩트 정보
    artifact_type: Mapped[str] = mapped_column(SQLEnum(ArtifactType))
    name: Mapped[str] = mapped_column(String(255))
    
    # 저장 위치
    storage_type: Mapped[str] = mapped_column(String(50))  # "db", "s3", "drive", "local"
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 버전 관리
    schema_version: Mapped[str] = mapped_column(String(20), default="v1.0")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA256 of content
    
    # 실제 데이터 (작은 데이터는 직접 저장)
    data_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # 메타데이터
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="artifacts")

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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class O2OApplication(Base):
    """User application for shipment/instant O2O campaigns"""
    __tablename__ = "o2o_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("o2o_campaigns.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(SQLEnum(O2OApplicationStatus), default=O2OApplicationStatus.APPLIED)
    shipment_tracking: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
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
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
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
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
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
    video_url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
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
    
    # O2O Campaign Eligibility (체험단 적합 여부)
    campaign_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Best Comments (바이럴 인간 지표)
    best_comments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    # [{"text": "...", "likes": 1000, "lang": "ko", "translation_en": "..."}, ...]
    comments_missing_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # blocked, no_comments, timeout
    
    # P0-2: Raw 데이터 보관 (원본 재현성 보장)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 크롤링 원본
    canonical_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # 정규화된 URL
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )  # 수집 Run 연결
    
    # P0-4: Real upload date from platform (distinct from crawled_at)
    upload_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 영상 실제 업로드일
    
    # P0-5: VDG Quality Score (vdg_quality_validator.py)
    vdg_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 ~ 1.0
    vdg_quality_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    vdg_quality_issues: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # ["issue1", "issue2", ...]
    
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
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
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
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
    
    # Phase E: NotebookLM Citations Integration
    notebooklm_citation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original citation from NLM
    synthesis_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "notebooklm_data_table", "pattern_synthesis"
    synthesis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pattern_syntheses.id"), nullable=True
    )  # Link to PatternSynthesis
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    parent_node: Mapped["RemixNode"] = relationship("RemixNode", backref="evidence_snapshots")


class NotebookLibraryEntry(Base):
    """
    NotebookLM Pattern Engine 결과를 DB에 래핑한 라이브러리 엔트리
    + 코드 기반 분석 스키마 (15_FINAL_ARCHITECTURE.md 기반)
    """
    __tablename__ = "notebook_library"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(50))
    summary: Mapped[dict] = mapped_column(JSONB)  # NotebookLM Pattern Engine 결과 (필수, DB-wrapped)
    cluster_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    parent_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), nullable=True
    )
    
    # Source Pack 연결 (PEGL v1.0)
    source_pack_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notebook_source_packs.id"), nullable=True
    )
    
    # NEW: 코드 기반 분석 스키마 (Gemini 3.0 Pro Structured Output)
    analysis_schema: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    schema_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "v1.0"

    # Temporal variation signals (17_TEMPORAL_VARIATION_THEORY.md)
    temporal_phase: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    variant_age_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    novelty_decay_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    burstiness_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

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
    
    # Temporal Recurrence / Pattern Lineage (v1)
    ancestor_cluster_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # 조상 클러스터 ID
    recurrence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 재등장 점수 (0~1)
    recurrence_count: Mapped[int] = mapped_column(Integer, default=0)  # 재등장 횟수
    origin_cluster_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 최초 기원 클러스터
    last_recurrence_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 마지막 재등장 시점
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    representative_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")


# ==================
# TEMPORAL RECURRENCE / PATTERN LINEAGE (v1)
# ==================

class RecurrenceLinkStatus(str, enum.Enum):
    """재등장 링크 상태"""
    CANDIDATE = "candidate"    # 후보 (임계값 0.80~0.88)
    CONFIRMED = "confirmed"    # 확정 (임계값 ≥0.88 + 하드게이트 2/3)
    REJECTED = "rejected"      # 기각


class PatternRecurrenceLink(Base):
    """
    패턴 재등장 링크 (Temporal Recurrence v1)
    과거 패턴과 현재 패턴의 유사성을 추적
    
    - confirmed만 L2 리랭커에 반영
    - candidate는 Shadow Mode로 DB에만 기록
    - 2회 이상 반복 매칭 시 confirmed로 승격
    """
    __tablename__ = "pattern_recurrence_links"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관계 클러스터
    cluster_id_current: Mapped[str] = mapped_column(String(100), index=True)  # 현재 클러스터
    cluster_id_ancestor: Mapped[str] = mapped_column(String(100), index=True)  # 과거 조상 클러스터
    
    # 상태
    status: Mapped[str] = mapped_column(SQLEnum(RecurrenceLinkStatus), default=RecurrenceLinkStatus.CANDIDATE)
    
    # Recurrence Score 및 피처 (v1 공식)
    # recurrence_score = 0.35*microbeat + 0.20*hook_genome + 0.15*focus_window + 0.10*audio_format + 0.10*comment_sig + 0.10*product_slot
    recurrence_score: Mapped[float] = mapped_column(Float, default=0.0)
    microbeat_sim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hook_genome_sim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    focus_window_sim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    audio_format_sim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    comment_signature_sim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product_slot_sim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 증거
    evidence_count: Mapped[int] = mapped_column(Integer, default=1)  # 매칭 횟수 (2회 이상 → confirmed 승격 조건)
    trigger_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )  # 트리거 Run
    feature_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 피처 스냅샷
    
    # 승격 정보
    promotion_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # "2+ matches", "score >= 0.90 + hard_gate"
    
    # 타임스탬프
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ==================
# P0-3: VDG EDGE (PEGL v1.0)
# ==================

class VDGEdgeStatus(str, enum.Enum):
    """VDG Edge 상태"""
    CANDIDATE = "candidate"    # 후보 (자동 생성)
    CONFIRMED = "confirmed"    # 확정 (증거 기반)
    REJECTED = "rejected"      # 기각


class VDGEdgeType(str, enum.Enum):
    """VDG Edge 관계 유형"""
    FORK = "fork"              # 직접 포크
    VARIATION = "variation"    # 변주 (동일 패턴)
    INSPIRED_BY = "inspired_by"  # 영감 (간접 관계)


class VDGEdge(Base):
    """
    VDG 관계 그래프 엣지 (PEGL Phase 0 핵심)
    - Parent-Child 관계를 증거 기반으로 추적
    - candidate → confirmed 상태 전이는 Evidence Loop에서만
    - confidence는 자동 계산, evidence_json에 근거 저장
    """
    __tablename__ = "vdg_edges"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관계 노드
    parent_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), index=True
    )
    child_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), index=True
    )
    
    # 관계 유형 및 상태
    edge_type: Mapped[str] = mapped_column(SQLEnum(VDGEdgeType), default=VDGEdgeType.FORK)
    edge_status: Mapped[str] = mapped_column(SQLEnum(VDGEdgeStatus), default=VDGEdgeStatus.CANDIDATE)
    
    # 신뢰도 및 증거
    confidence: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 ~ 1.0
    evidence_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # {
    #   "similarity_score": 0.85,
    #   "matching_patterns": ["hook-2s-text", "audio-trending"],
    #   "temporal_distance_days": 7,
    #   "performance_lift": "+35%"
    # }
    
    # 확정 정보
    confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmation_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "auto", "manual"
    
    # Run 연결
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )  # 생성 Run
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    parent_node: Mapped["RemixNode"] = relationship("RemixNode", foreign_keys=[parent_node_id])
    child_node: Mapped["RemixNode"] = relationship("RemixNode", foreign_keys=[child_node_id])
    confirmer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[confirmed_by])


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
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
    # Week 2: 크리에이터 활용 추적
    GUIDE_VIEW = "guide_view"           # 가이드 페이지 방문
    REMIX_GUIDE_CLICK = "remix_guide_click"  # remix_suggestions 클릭
    CAPSULE_BRIEF_VIEW = "capsule_brief_view"  # capsule_brief 뷰
    VIDEO_PRODUCTION_START = "video_production_start"  # 영상 제작 시작
    VIDEO_PRODUCTION_COMPLETE = "video_production_complete"  # 영상 제작 완료


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


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
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
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
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    board: Mapped["EvidenceBoard"] = relationship("EvidenceBoard", back_populates="items")
    outlier_item: Mapped[Optional["OutlierItem"]] = relationship("OutlierItem")
    remix_node: Mapped[Optional["RemixNode"]] = relationship("RemixNode")


# ==================
# NOTEBOOK SOURCE PACK (17_NOTEBOOKLM_LIBRARY_STRATEGY.md)
# ==================

class NotebookSourcePack(Base):
    """
    NotebookLM Source Pack 기록 (PEGL v1.0 업데이트)
    클러스터 + temporal_phase 단위로 Source Pack 관리
    - 패턴 경계는 VDG/DB 고정 원칙에 따라 cluster_id 기준
    - temporal_phase로 시간대별 패턴 품질 변화 추적
    """
    __tablename__ = "notebook_source_packs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 핵심 식별자: cluster_id + temporal_phase
    cluster_id: Mapped[str] = mapped_column(String(100), index=True)
    temporal_phase: Mapped[str] = mapped_column(String(20), index=True)  # "early", "growth", "mature", "decay"
    
    # Pack 타입 및 파일 정보
    pack_type: Mapped[str] = mapped_column(String(50))  # "sheet" | "docx"
    drive_file_id: Mapped[str] = mapped_column(String(100))  # Google Drive file ID
    drive_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Full URL for convenience
    
    # Idempotency (PEGL P0 기준)
    inputs_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA256 of input entries
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )  # 생성 Run 연결
    
    # 버전 관리
    source_version: Mapped[str] = mapped_column(String(50), default="v1.0")  # Pack 생성 시 스키마 버전
    entry_count: Mapped[int] = mapped_column(Integer, default=0)  # 포함된 엔트리 수
    
    # Phase C: Multi-Output Protocol (SoR)
    output_targets: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "creator,business,ops"
    pack_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "standard" | "mega"
    schema_version: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "v3.3"
    
    # Phase D: NotebookLM Integration
    notebook_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Automation linkage
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ==================
# P0-4: PATTERN LIBRARY (PEGL v1.0)
# ==================

class PatternLibrary(Base):
    """
    패턴 라이브러리 (PEGL v1.0 핵심)
    NotebookLM Pattern Engine의 출력을 DB-wrapped로 저장
    
    - invariant_rules: 불변 규칙 (이 패턴의 핵심)
    - mutation_strategy: 변주 포인트 (이 패턴에서 변주 가능한 요소)
    - citations: 출처 (Source Pack의 어느 항목에서 추출했는지)
    """
    __tablename__ = "pattern_library"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # "tiktok_beauty_hook2s_v1"
    
    # Source Pack 연결
    source_pack_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notebook_source_packs.id"), nullable=True
    )
    
    # 패턴 범위 (VDG/DB 패턴 경계 원칙)
    cluster_id: Mapped[str] = mapped_column(String(100), index=True)
    temporal_phase: Mapped[str] = mapped_column(String(20), index=True)  # "early", "growth", "mature", "decay"
    platform: Mapped[str] = mapped_column(String(50))  # "tiktok", "instagram", "youtube"
    category: Mapped[str] = mapped_column(String(50))  # "beauty", "food", "meme"
    
    # Pattern Engine 출력 (NotebookLM 결과)
    invariant_rules: Mapped[dict] = mapped_column(JSONB)
    # {
    #   "hook": {"type": "text_punch", "duration_sec": 2, "required": true},
    #   "music": {"genre": "trending_kpop", "bpm_range": [120, 140]},
    #   "pacing": {"cuts_per_10sec": 5}
    # }
    
    mutation_strategy: Mapped[dict] = mapped_column(JSONB)
    # {
    #   "modifiable": ["background_color", "font_style", "hook_text_content"],
    #   "constrained": ["hook_duration", "music_genre"],
    #   "forbidden": ["remove_hook", "slow_pacing"]
    # }
    
    citations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # [
    #   {"source_entry_id": "...", "context": "Best performing variant with +350% growth"},
    #   {"source_entry_id": "...", "context": "Consistent hook pattern across 12 variants"}
    # ]
    
    # 리비전 관리
    revision: Mapped[int] = mapped_column(Integer, default=1)
    previous_revision_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pattern_library.id"), nullable=True
    )
    
    # 성능 메타데이터 (추후 업데이트)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)  # 기반 샘플 수
    avg_success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 성공률
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)  # 신뢰도
    
    # Run 연결
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    source_pack: Mapped[Optional["NotebookSourcePack"]] = relationship("NotebookSourcePack")
    previous_revision: Mapped[Optional["PatternLibrary"]] = relationship("PatternLibrary", remote_side=[id])


# ==================
# P0-5: EVIDENCE LOOP STATE MACHINE (PEGL v1.0)
# ==================

class EvidenceEventStatus(str, enum.Enum):
    """Evidence Loop 이벤트 상태"""
    QUEUED = "queued"              # 대기중
    RUNNING = "running"            # 분석중
    EVIDENCE_READY = "evidence_ready"  # 증거 수집 완료
    DECIDED = "decided"            # 결정 완료
    EXECUTED = "executed"          # 실행됨
    MEASURED = "measured"          # 측정 완료
    FAILED = "failed"              # 실패


class EvidenceEvent(Base):
    """
    Evidence Loop 이벤트 (PEGL v1.0 핵심)
    "증거 → 결정 → 실행 → 측정" 루프의 단일 이벤트
    
    상태 전이:
    QUEUED → RUNNING → EVIDENCE_READY → DECIDED → EXECUTED → MEASURED
    """
    __tablename__ = "evidence_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # 사람 친화적 ID
    
    # Run 연결
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )
    
    # 대상 Parent
    parent_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id"), index=True
    )
    
    # 상태
    status: Mapped[str] = mapped_column(SQLEnum(EvidenceEventStatus), default=EvidenceEventStatus.QUEUED)
    
    # 산출물 연결
    evidence_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_snapshots.id"), nullable=True
    )
    decision_object_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True  # DecisionObject.id (circular reference 방지)
    )
    
    # 에러 정보
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 타이밍
    queued_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    evidence_ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    measured_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    parent_node: Mapped["RemixNode"] = relationship("RemixNode")
    evidence_snapshot: Mapped[Optional["EvidenceSnapshot"]] = relationship("EvidenceSnapshot")


class DecisionType(str, enum.Enum):
    """결정 유형"""
    GO = "go"          # 진행
    STOP = "stop"      # 중단
    PIVOT = "pivot"    # 방향 전환


class DecisionObject(Base):
    """
    결정 객체 (PEGL v1.0 핵심)
    Evidence Loop에서 내린 결정을 구조화된 형태로 저장
    
    - decision_json: 구조화된 결정 내용
    - transcript_artifact_id: Debate 기록 (옵션)
    """
    __tablename__ = "decision_objects"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # 사람 친화적 ID
    
    # Evidence Event 연결
    evidence_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_events.id"), index=True
    )
    
    # 결정 내용
    decision_type: Mapped[str] = mapped_column(SQLEnum(DecisionType))
    decision_json: Mapped[dict] = mapped_column(JSONB)
    # {
    #   "action": "create_variant",
    #   "variant_type": "audio_swap",
    #   "rationale": "Top mutation type is audio with +127% avg delta",
    #   "target_kpi": "view_retention > 50%",
    #   "timeline_days": 7
    # }
    
    # 근거
    evidence_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # {
    #   "top_mutation": "audio",
    #   "avg_delta": "+127%",
    #   "sample_count": 12,
    #   "confidence": 0.85
    # }
    
    # Debate 기록 (옵션)
    transcript_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=True
    )  # Debate 텍스트 기록
    
    # 결정자
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # null이면 자동 결정
    decision_method: Mapped[str] = mapped_column(String(50), default="auto")  # "auto", "manual", "hybrid"
    
    # 메타데이터
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    evidence_event: Mapped["EvidenceEvent"] = relationship("EvidenceEvent")
    transcript_artifact: Mapped[Optional["Artifact"]] = relationship("Artifact")
    decider: Mapped[Optional["User"]] = relationship("User")


# ==================
# PATTERN SYNTHESIS (NotebookLM Data Tables → DB) - Phase B
# ==================

class SynthesisType(str, enum.Enum):
    """Pattern Synthesis 유형 (NotebookLM Data Tables 출력)"""
    INVARIANT_RULES = "invariant_rules"    # 불변 규칙 추출
    MUTATION_STRATEGY = "mutation_strategy"  # 변주 전략
    FAILURE_MODES = "failure_modes"        # 실패 패턴
    AUDIENCE_SIGNAL = "audience_signal"    # 오디언스 반응 시그널
    HOOK_PATTERN = "hook_pattern"          # 훅 패턴
    DIRECTOR_INTENT = "director_intent"    # 연출 의도


class PatternSynthesis(Base):
    """
    NotebookLM Data Tables → DB 래핑 (Phase B: Data Tables Pipeline)
    
    NotebookLM의 구조화 테이블 출력을 DB에 저장하여 SoR 원칙 준수
    - Data Tables → Sheets Export → 이 모델로 ingest
    - Citations으로 Evidence Loop 연결
    
    참조: docs/17_NOTEBOOKLM_LIBRARY_STRATEGY.md (2.5 Data Tables)
    """
    __tablename__ = "pattern_syntheses"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # NotebookLM 연결
    notebook_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)  # NotebookLM notebook ID
    source_sheet_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Data Tables export URL
    
    # 패턴 경계 (VDG/DB 패턴 경계 원칙)
    cluster_id: Mapped[str] = mapped_column(String(100), index=True)
    temporal_phase: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    
    # 합성 내용
    synthesis_type: Mapped[str] = mapped_column(SQLEnum(SynthesisType), index=True)
    synthesis_data: Mapped[dict] = mapped_column(JSONB)
    # invariant_rules 예:
    # {
    #   "rules": ["Hook ≤ 2s", "CU shot opening"],
    #   "must_keep": {"hook": "text_punch", "pacing": "5_cuts_per_10s"},
    #   "confidence": 0.92
    # }
    
    # 출처 (NotebookLM 인용 기능)
    citations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # [
    #   {"source_entry": "entry_123", "excerpt": "...", "relevance": 0.95},
    #   {"source_entry": "entry_456", "excerpt": "..."}
    # ]
    
    # 출력 대상 (Studio Multi-Output)
    output_format: Mapped[str] = mapped_column(String(20), default="creator")  # creator, business, ops
    language: Mapped[str] = mapped_column(String(10), default="ko")  # ko, en
    
    # Run/Pack 연결
    source_pack_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notebook_source_packs.id"), nullable=True
    )
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )
    
    # 메타데이터
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    source_pack: Mapped[Optional["NotebookSourcePack"]] = relationship("NotebookSourcePack")


# ==================
# P2: CREATOR FEEDBACK LOOP
# ==================

class CreatorSubmissionStatus(str, enum.Enum):
    """Status of a creator submission"""
    PENDING = "pending"           # Submitted, awaiting metric tracking
    TRACKING = "tracking"         # Metrics being collected (14 days)
    COMPLETE = "complete"         # Tracking complete, evidence generated
    FAILED = "failed"             # Video unavailable or rejected


class CreatorSubmission(Base):
    """
    P2 Creator Feedback Loop - Links PatternLibrary to creator-submitted videos.
    
    Flow:
    1. Creator views PatternLibrary guide
    2. Creator films video following invariant_rules
    3. Creator submits video URL with pattern_id
    4. System tracks metrics for 14 days
    5. Results feed back into Evidence Loop
    """
    __tablename__ = "creator_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Pattern reference
    pattern_id: Mapped[str] = mapped_column(String(200), index=True)  # PatternLibrary.pattern_id
    pattern_library_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pattern_library.id"), nullable=True
    )
    
    # Creator info
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Video submission
    video_url: Mapped[str] = mapped_column(String(500))
    platform: Mapped[str] = mapped_column(String(50))  # tiktok, instagram, youtube
    
    # Creator notes on what they varied
    creator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invariant_checklist: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # {"첫 2초 시선 고정": true, "음악 싱크": true, ...}
    
    # Metric tracking
    status: Mapped[str] = mapped_column(SQLEnum(CreatorSubmissionStatus), default=CreatorSubmissionStatus.PENDING)
    outlier_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outlier_items.id"), nullable=True
    )  # Linked OutlierItem for metric tracking
    
    # Performance results (after 14-day tracking)
    final_view_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    performance_vs_baseline: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "+45%", "-10%"
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    tracking_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tracking_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    pattern_library: Mapped[Optional["PatternLibrary"]] = relationship("PatternLibrary")
    outlier_item: Mapped[Optional["OutlierItem"]] = relationship("OutlierItem")


# ==================
# COACHING SESSION LOGS (Proof Playbook v1.0)
# ==================

class CoachingAssignment(str, enum.Enum):
    """코칭 그룹 할당"""
    COACHED = "coached"
    CONTROL = "control"


class CoachingMode(str, enum.Enum):
    """코칭 세션 모드"""
    HOMAGE = "homage"
    MUTATION = "mutation"
    CAMPAIGN = "campaign"


class EvidenceType(str, enum.Enum):
    """증거 유형"""
    FRAME = "frame"
    AUDIO = "audio"
    TEXT = "text"


class ComplianceResult(str, enum.Enum):
    """준수 결과"""
    COMPLIED = "complied"
    VIOLATED = "violated"
    UNKNOWN = "unknown"


class CoachingSession(Base):
    """
    오디오 코칭 세션 (Proof Playbook v1.0)
    
    핵심 조인키: session_id + pattern_id + pack_id
    """
    __tablename__ = "coaching_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id_hash: Mapped[str] = mapped_column(String(64), index=True)  # 개인정보 X - 해시만
    
    # Session config
    mode: Mapped[str] = mapped_column(SQLEnum(CoachingMode), default=CoachingMode.HOMAGE)
    pattern_id: Mapped[str] = mapped_column(String(100), index=True)
    pack_id: Mapped[str] = mapped_column(String(100), index=True)
    pack_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Coaching assignment (Goodhart prevention: 10% control, 5% holdout)
    assignment: Mapped[str] = mapped_column(SQLEnum(CoachingAssignment), default=CoachingAssignment.COACHED)
    holdout_group: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Device/Environment (P2)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Aggregated metrics (denormalized for query efficiency)
    intervention_count: Mapped[int] = mapped_column(Integer, default=0)
    compliance_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unknown_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    interventions: Mapped[List["CoachingIntervention"]] = relationship(
        "CoachingIntervention", back_populates="session", cascade="all, delete-orphan"
    )
    outcomes: Mapped[List["CoachingOutcome"]] = relationship(
        "CoachingOutcome", back_populates="session", cascade="all, delete-orphan"
    )
    upload_outcome: Mapped[Optional["CoachingUploadOutcome"]] = relationship(
        "CoachingUploadOutcome", back_populates="session", uselist=False
    )


class CoachingIntervention(Base):
    """
    코칭 개입 이벤트
    
    증명용 핵심 필드:
    - t_sec: 언제 개입했는지
    - rule_id: 어떤 규칙 위반인지
    - coach_line_id: 어떤 코칭 문장이었는지
    """
    __tablename__ = "coaching_interventions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("coaching_sessions.session_id"), index=True
    )
    
    t_sec: Mapped[float] = mapped_column(Float)  # 세션 시작 기준 초
    rule_id: Mapped[str] = mapped_column(String(100), index=True)
    ap_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # ActionPoint ID
    
    # Evidence
    evidence_id: Mapped[str] = mapped_column(String(100))
    evidence_type: Mapped[str] = mapped_column(SQLEnum(EvidenceType), default=EvidenceType.FRAME)
    
    # Coach line delivered
    coach_line_id: Mapped[str] = mapped_column(String(50))  # strict/friendly/neutral
    coach_line_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metric snapshot
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metric_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    session: Mapped["CoachingSession"] = relationship("CoachingSession", back_populates="interventions")


class CoachingOutcome(Base):
    """
    행동 변화 관찰 기록
    
    compliance = COMPLIED: 코칭 후 규칙 준수
    compliance = VIOLATED: 코칭 후에도 위반 지속
    compliance = UNKNOWN: 측정 불가
    """
    __tablename__ = "coaching_outcomes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("coaching_sessions.session_id"), index=True
    )
    
    t_sec: Mapped[float] = mapped_column(Float)  # 관찰 시점
    rule_id: Mapped[str] = mapped_column(String(100), index=True)
    
    # Compliance result
    compliance: Mapped[str] = mapped_column(SQLEnum(ComplianceResult), default=ComplianceResult.UNKNOWN)
    compliance_unknown_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Metric after intervention
    metric_value_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metric_delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Time since intervention
    latency_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    session: Mapped["CoachingSession"] = relationship("CoachingSession", back_populates="outcomes")


class CoachingUploadOutcome(Base):
    """
    업로드 결과 프록시 (성과 Lift 계산용)
    """
    __tablename__ = "coaching_upload_outcomes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("coaching_sessions.session_id"), unique=True, index=True
    )
    
    # Upload status
    uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    upload_platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Early performance buckets
    early_views_bucket: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    early_likes_bucket: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Self-rating (1-5)
    self_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    self_rating_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    session: Mapped["CoachingSession"] = relationship("CoachingSession", back_populates="upload_outcome")
