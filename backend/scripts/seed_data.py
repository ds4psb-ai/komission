import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from app.config import settings
from app.models import RemixNode, O2OLocation, O2OCampaign, User, NodeLayer, NodePermission, NodeGovernance, Base

# Database URL
DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_data():
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding Data...")
        
        # 0. Create Initial User
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@k-meme.com",
            name="Admin User",
            role="admin",
            k_points=1000,
            firebase_uid="firebase_uid_admin_123"
        )
        
        # Check if user exists
        existing_user = await db.execute(select(User).where(User.email == admin_user.email))
        existing_user = existing_user.scalar_one_or_none()
        
        if not existing_user:
            db.add(admin_user)
            await db.flush()
            admin_id = admin_user.id
        else:
            admin_id = existing_user.id

        # 1. Create O2O Locations
        locations = [
            O2OLocation(
                id=uuid.uuid4(),
                location_id="loc_seongsu_001",
                campaign_type="visit_challenge",
                place_name="Komission Pop-up Store Seongsu",
                address="Seoul, Seongdong-gu, Seongsu-dong 2-ga, 322-1",
                # coordinates removed as it is not in the model
                lat=37.544579,
                lng=127.056045,
                brand="Samsung Galaxy",
                campaign_title="Capture the Night Challenge",
                category="lifestyle",
                verification_method="gps_match",
                reward_points=500,
                reward_product="Galaxy Case 20% Off",
                active_start=datetime.now() - timedelta(days=1),
                active_end=datetime.now() + timedelta(days=30),
                max_participants=1000,
                gmaps_place_id="ChIJ..."
            ),
            O2OLocation(
                id=uuid.uuid4(),
                location_id="loc_gangnam_002",
                campaign_type="product_trial",
                place_name="Nike Gangnam Flagship",
                address="Seoul, Gangnam-gu, Yeoksam-dong, 813-1",
                lat=37.502621,
                lng=127.025538,
                brand="Nike",
                campaign_title="Run Your Way",
                category="fashion",
                verification_method="gps_match",
                reward_points=300,
                reward_product="Nike Headband",
                active_start=datetime.now() - timedelta(days=5),
                active_end=datetime.now() + timedelta(days=15),
                max_participants=500,
                gmaps_place_id="ChIJ..."
            )
        ]
        
        for loc in locations:
            # Check if exists
            exists = await db.get(O2OLocation, loc.id)
            if not exists:
                db.add(loc)

        # 1-2. Create O2O Campaigns (Instant/Shipment)
        campaigns = [
            O2OCampaign(
                id=uuid.uuid4(),
                campaign_id="camp_instant_001",
                campaign_type="instant",
                campaign_title="브랜드 릴스 즉시 챌린지",
                brand="Komission",
                category="lifestyle",
                description="브랜드 가이드에 맞춰 즉시 촬영 가능한 온라인 챌린지",
                reward_points=250,
                reward_product=None,
                fulfillment_steps={"steps": ["촬영", "제출", "승인"]},
                active_start=datetime.now() - timedelta(days=2),
                active_end=datetime.now() + timedelta(days=20),
                max_participants=2000,
            ),
            O2OCampaign(
                id=uuid.uuid4(),
                campaign_id="camp_ship_001",
                campaign_type="shipment",
                campaign_title="신제품 언박싱 배송형 캠페인",
                brand="Coupang",
                category="lifestyle",
                description="선정 후 제품 배송 → 언박싱 촬영",
                reward_points=800,
                reward_product="신제품 체험 키트",
                fulfillment_steps={"steps": ["신청", "선정", "배송", "촬영"]},
                active_start=datetime.now() - timedelta(days=1),
                active_end=datetime.now() + timedelta(days=25),
                max_participants=500,
            ),
        ]

        for camp in campaigns:
            exists = await db.execute(select(O2OCampaign).where(O2OCampaign.campaign_id == camp.campaign_id))
            if not exists.scalar_one_or_none():
                db.add(camp)

        # 2. Create Remix Nodes (Outliers)
        nodes = [
            RemixNode(
                id=uuid.uuid4(),
                node_id="remix_master_001",
                title="Slickback Challenge (Official)",
                layer=NodeLayer.MASTER,
                permission=NodePermission.READ_ONLY,
                governed_by=NodeGovernance.OPEN_COMMUNITY,
                owner_type="admin",
                created_by=admin_id,
                source_video_url="https://example.com/slickback.mp4",
                platform="tiktok",
                is_published=True,
                view_count=1542000,
                genealogy_depth=0,
                created_at=datetime.now() - timedelta(days=10),
                gemini_analysis={
                    "metadata": {"title": "A Lakota", "bpm": 130, "mood": "Energetic"},
                    "visual_dna": {"setting_description": "Street, floating steps"},
                    "commerce_context": {"primary_category": "Dance", "keywords": ["shoes", "streetwear"]}
                },
                claude_brief={
                    "title_kr": "초전도체 슬릭백",
                    "caption": "중력을 거스르는 자",
                    "hashtags": ["#Slickback", "#Dance", "#Floating"]
                }
            ),
             RemixNode(
                id=uuid.uuid4(),
                node_id="remix_fork_002",
                title="Slickback on Ice",
                layer=NodeLayer.FORK,
                permission=NodePermission.FULL_EDIT,
                governed_by=NodeGovernance.OPEN_COMMUNITY,
                owner_type="user",
                created_by=admin_id, # Simplified for seed
                source_video_url="https://example.com/slickback_ice.mp4",
                platform="instagram",
                is_published=True,
                view_count=45000,
                genealogy_depth=1,
                created_at=datetime.now() - timedelta(days=5)
            ),
             RemixNode(
                id=uuid.uuid4(),
                node_id="remix_master_cat",
                title="Happy Cat Meme",
                layer=NodeLayer.MASTER,
                permission=NodePermission.READ_ONLY,
                governed_by=NodeGovernance.OPEN_COMMUNITY,
                owner_type="admin",
                created_by=admin_id,
                source_video_url="https://example.com/happy_cat.mp4",
                platform="tiktok",
                is_published=True,
                view_count=8900000,
                genealogy_depth=0,
                created_at=datetime.now() - timedelta(days=20),
                gemini_analysis={
                    "metadata": {"title": "Happy Happy Happy", "bpm": 150, "mood": "Cute"},
                    "visual_dna": {"setting_description": "Green screen, waving paws"},
                    "commerce_context": {"primary_category": "Pet", "keywords": ["cat food", "toys"]}
                },
                 claude_brief={
                    "title_kr": "행복한 고양이",
                    "caption": "직장인 퇴근 10분 전",
                    "hashtags": ["#Cat", "#Meme", "#Happy"]
                }
            )
        ]

        for node in nodes:
             db.add(node)

        await db.commit()
        print("✅ Data Seeded Successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
