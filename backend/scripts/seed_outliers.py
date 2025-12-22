"""
Seed Script: Populate Viral Outliers for Homepage
Extended with more diverse TikTok, Reels, and Shorts content
"""
import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models import Base, RemixNode, User, NodeLayer, NodePermission, NodeGovernance


OUTLIER_SEEDS = [
    # === TikTok Viral Hits ===
    {
        "node_id": "viral_outlier_001",
        "title": "K-밈 탄두리 치킨 댄스 🍗",
        "source_video_url": "https://www.tiktok.com/@kfoodmeme/video/123456",
        "platform": "tiktok",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.READ_ONLY,
        "governed_by": NodeGovernance.BRAND_OFFICIAL,
        "view_count": 2500000,
        "performance_delta": "+850%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "K-POP Dance", "emotion": "Joy", "hook": "0:03-0:08"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_003",
        "title": "한복 변신 트랜지션 👘",
        "source_video_url": "https://www.tiktok.com/@hanbokqueen/video/789012",
        "platform": "tiktok",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 3200000,
        "performance_delta": "+1200%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "Transition Magic", "emotion": "Awe", "hook": "0:04-0:07"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_005",
        "title": "두바이 초콜릿 ASMR 먹방 🍫",
        "source_video_url": "https://www.tiktok.com/@dubai.chocolate/video/7318234567890123",
        "platform": "tiktok",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 15000000,
        "performance_delta": "+2847%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "ASMR Mukbang", "emotion": "Satisfaction", "hook": "0:02-0:06"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_006",
        "title": "한강 라면 야경 브이로그 🍜",
        "source_video_url": "https://www.tiktok.com/@seoul_nightlife/video/7319876543210",
        "platform": "tiktok",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 8500000,
        "performance_delta": "+523%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "Night Vlog", "emotion": "Cozy", "hook": "0:01-0:04"},
        "is_published": True,
    },
    
    # === Instagram Reels ===
    {
        "node_id": "viral_outlier_002",
        "title": "불닭볶음면 챌린지 리믹스 🔥",
        "source_video_url": "https://www.instagram.com/reels/abcxyz",
        "platform": "instagram",
        "layer": NodeLayer.FORK,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.CREATOR_VERIFIED,
        "view_count": 1870000,
        "performance_delta": "+425%",
        "genealogy_depth": 1,
        "gemini_analysis": {"style": "Mukbang Reaction", "emotion": "Surprise", "hook": "0:02-0:05"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_007",
        "title": "NewJeans 'Super Shy' 커버 댄스 💃",
        "source_video_url": "https://www.instagram.com/reel/CzX1234567890/",
        "platform": "instagram",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 22000000,
        "performance_delta": "+1,247%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "K-Pop Cover", "emotion": "Energetic", "hook": "0:02-0:08"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_008",
        "title": "서울 야경 드론 촬영 🌃",
        "source_video_url": "https://www.instagram.com/reel/CzY9876543210/",
        "platform": "instagram",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 6700000,
        "performance_delta": "+445%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "Aerial Photography", "emotion": "Awe", "hook": "0:03-0:07"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_010",
        "title": "GRWM 데일리 메이크업 💄",
        "source_video_url": "https://www.instagram.com/reel/CzA111222333/",
        "platform": "instagram",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 9400000,
        "performance_delta": "+556%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "Beauty Tutorial", "emotion": "Calm", "hook": "0:01-0:05"},
        "is_published": True,
    },
    
    # === YouTube Shorts ===
    {
        "node_id": "viral_outlier_009",
        "title": "강릉 카페 투어 ☕️",
        "source_video_url": "https://www.youtube.com/shorts/Abc123DefGhi",
        "platform": "youtube",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 5200000,
        "performance_delta": "+312%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "Cafe Tour", "emotion": "Relaxing", "hook": "0:02-0:06"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_011",
        "title": "편의점 신상 리뷰 2024 🛒",
        "source_video_url": "https://www.youtube.com/shorts/Xyz789AbcDef",
        "platform": "youtube",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 4300000,
        "performance_delta": "+289%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "Product Review", "emotion": "Curious", "hook": "0:01-0:04"},
        "is_published": True,
    },
    {
        "node_id": "viral_outlier_012",
        "title": "애견 카페 강아지 힐링 🐶",
        "source_video_url": "https://www.youtube.com/shorts/PetCafe123456",
        "platform": "youtube",
        "layer": NodeLayer.MASTER,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 3900000,
        "performance_delta": "+234%",
        "genealogy_depth": 0,
        "gemini_analysis": {"style": "Pet Content", "emotion": "Heartwarming", "hook": "0:02-0:05"},
        "is_published": True,
    },
    
    # === Forks for diversity ===
    {
        "node_id": "viral_outlier_004",
        "title": "소주 vs 막걸리 밈 배틀 🍶",
        "source_video_url": "https://www.tiktok.com/@drinkkorea/video/345678",
        "platform": "tiktok",
        "layer": NodeLayer.FORK_OF_FORK,
        "permission": NodePermission.FULL_EDIT,
        "governed_by": NodeGovernance.OPEN_COMMUNITY,
        "view_count": 980000,
        "performance_delta": "+180%",
        "genealogy_depth": 2,
        "gemini_analysis": {"style": "Comedy Skit", "emotion": "Fun", "hook": "0:01-0:04"},
        "is_published": True,
    },
]


async def get_or_create_admin_user(session: AsyncSession) -> User:
    """Get or create an admin user for seeding"""
    from sqlalchemy import select
    
    result = await session.execute(select(User).where(User.firebase_uid == "seed_admin_uid"))
    admin = result.scalar_one_or_none()
    
    if not admin:
        admin = User(
            firebase_uid="seed_admin_uid",
            email="admin@komission.ai",
            name="Komission Admin",
            role="admin",
            k_points=10000,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        print("✅ Created admin user")
    else:
        print("ℹ️ Admin user already exists")
    
    return admin


async def seed_outliers():
    """Main seed function"""
    print("🌱 Starting seed process...")
    print(f"   Will seed {len(OUTLIER_SEEDS)} outlier nodes")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables ensured")
    
    async with AsyncSessionLocal() as session:
        admin = await get_or_create_admin_user(session)
        
        from sqlalchemy import select
        existing = await session.execute(
            select(RemixNode).where(RemixNode.node_id.like("viral_outlier_%"))
        )
        existing_ids = {node.node_id for node in existing.scalars().all()}
        
        created_count = 0
        skipped_count = 0
        for seed in OUTLIER_SEEDS:
            if seed["node_id"] in existing_ids:
                print(f"🔄 Updating {seed['node_id']} (forcing Korean title)")
                # Find the node to update
                stmt = select(RemixNode).where(RemixNode.node_id == seed["node_id"])
                result = await session.execute(stmt)
                node = result.scalar_one()
                
                # Update fields
                node.title = seed["title"]
                node.gemini_analysis = seed["gemini_analysis"]
                node.view_count = seed["view_count"]
                skipped_count += 1 # Technically updated, but using this counter
            else:    
                node = RemixNode(
                    node_id=seed["node_id"],
                    title=seed["title"],
                    source_video_url=seed["source_video_url"],
                    platform=seed["platform"],
                    layer=seed["layer"],
                    permission=seed["permission"],
                    governed_by=seed["governed_by"],
                    view_count=seed["view_count"],
                    performance_delta=seed["performance_delta"],
                    genealogy_depth=seed["genealogy_depth"],
                    gemini_analysis=seed["gemini_analysis"],
                    is_published=seed["is_published"],
                    created_by=admin.id,
                    owner_type="admin",
                )
                session.add(node)
                created_count += 1
                print(f"✅ Created: {seed['title']}")
        
        await session.commit()
        print(f"\n🎉 Seed complete!")
        print(f"   Created: {created_count} new nodes")
        print(f"   Skipped: {skipped_count} existing nodes")


if __name__ == "__main__":
    asyncio.run(seed_outliers())
