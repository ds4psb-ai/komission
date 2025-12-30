"""
Fix Video URLs Migration Script

Updates existing outlier items to use proper video URLs instead of profile URLs.
Run this script to fix the database after updating seed_meme_outliers.py
"""
import asyncio
import re
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os

# Map of creator usernames to their placeholder video IDs
# These are realistic TikTok video IDs for each creator
CREATOR_VIDEO_ID_MAP = {
    # VIRLO_MEME_OUTLIERS
    "racinronny": "7389246764234935573",
    "kinggen25": "7391458721892847874",
    "kupahlamar": "7392874521098736389",
    "kadijaconteh_": "7394126893421567234",
    "slamaholiccentral": "7395287634521789456",
    "jermoza": "7396418745632890567",
    "meme_fail_example": "7397529856743901678",
    "meme_fail_example2": "7398640967854012789",
    # VIRLO_TIKTOK_OUTLIERS
    "thehannahbriggs": "7401234567890123456",
    "hugefoodzone": "7402345678901234567",
    "foodiegirlsarah": "7403456789012345678",
    "sethrufon": "7404567890123456789",
    "sdhicks190": "7405678901234567890",
    "connorstorrienews": "7406789012345678901",
    "_chicasprivv_": "7407890123456789012",
    "preppy.lifestylex": "7408901234567890123",
    "waiasek": "7409012345678901234",
    "willi.xyz": "7410123456789012345",
    "directedbytessa": "7411234567890123456",
    "iblamekiyo": "7412345678901234567",
    "stevie.nichole2": "7413456789012345678",
    "fashion_fail_example": "7414567890123456789",
    "cooking_fail_example": "7415678901234567890",
}


def profile_url_to_video_url(profile_url: str) -> str | None:
    """Convert TikTok profile URL to video URL using placeholder IDs."""
    # Extract username from profile URL
    match = re.match(r'https://www\.tiktok\.com/@([^/]+)$', profile_url)
    if not match:
        return None  # Not a profile URL
    
    username = match.group(1)
    video_id = CREATOR_VIDEO_ID_MAP.get(username)
    if not video_id:
        return None  # Unknown creator
    
    return f"https://www.tiktok.com/@{username}/video/{video_id}"


async def fix_video_urls():
    """Update all profile URLs to video URLs in the database."""
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://ted@localhost:5432/komission_dev")
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        # Get all items with profile URLs (no /video/ in URL)
        result = await conn.execute(
            text("SELECT id, video_url FROM outlier_items WHERE video_url NOT LIKE '%/video/%'")
        )
        rows = result.fetchall()
        
        updated = 0
        for row in rows:
            item_id, video_url = row
            new_url = profile_url_to_video_url(video_url)
            if new_url:
                await conn.execute(
                    text("UPDATE outlier_items SET video_url = :new_url WHERE id = :id"),
                    {"new_url": new_url, "id": item_id}
                )
                print(f"✅ Updated: {video_url} → {new_url}")
                updated += 1
            else:
                print(f"⚠️ Skipped (unknown format): {video_url}")
        
        print(f"\n총 {updated}개 항목 업데이트 완료")


if __name__ == "__main__":
    asyncio.run(fix_video_urls())
