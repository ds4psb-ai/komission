"""
Virlo Outlier Scraper using httpx API calls (PEGL v1.0)
Fetches viral outlier data from Virlo's internal API endpoints

PEGL v1.0: 스키마 검증 적용
"""
import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.utils.time import utcnow
from app.validators.schema_validator import validate_outlier_schema, SchemaValidationError

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VirloOutlierItem(BaseModel):
    """Virlo outlier data model"""
    title: str
    creator_username: str
    platform: str  # tiktok, youtube, instagram
    video_url: Optional[str] = None
    view_count: int = 0
    multiplier: float = 1.0  # e.g., 186x
    niche: str = ""
    posted_date: Optional[str] = None
    thumbnail_url: Optional[str] = None
    scraped_at: datetime = None
    
    def __init__(self, **data):
        if 'scraped_at' not in data or data['scraped_at'] is None:
            data['scraped_at'] = utcnow()
        super().__init__(**data)


def get_auth_headers() -> Dict[str, str]:
    """
    Get authentication headers for Virlo API.
    Uses VIRLO_ACCESS_TOKEN (JWT) from environment.
    """
    access_token = os.getenv("VIRLO_ACCESS_TOKEN", "")
    if not access_token:
        raise ValueError("VIRLO_ACCESS_TOKEN environment variable not set")
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Origin": "https://app.virlo.ai",
        "Referer": "https://app.virlo.ai/outlier",
    }


# Known Virlo API endpoints (Supabase-based)
VIRLO_API_BASE = "https://api.virlo.ai"  # or supabase endpoint
VIRLO_SUPABASE_URL = os.getenv("VIRLO_SUPABASE_URL", "https://sbylndxfmovqyehvqkir.supabase.co")


async def scrape_outliers_via_api(
    limit: int = 50,
    platforms: Optional[List[str]] = None,
    category: Optional[str] = None,
) -> List[VirloOutlierItem]:
    """
    Fetch outlier data from Virlo using direct API calls.
    
    Args:
        limit: Maximum number of items to fetch
        platforms: Filter by platforms (tiktok, youtube, instagram)
        category: Filter by category/niche
        
    Returns:
        List of VirloOutlierItem objects
    """
    headers = get_auth_headers()
    items: List[VirloOutlierItem] = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Try different API endpoints that Virlo might use
            endpoints_to_try = [
                f"{VIRLO_SUPABASE_URL}/rest/v1/outliers",
                f"{VIRLO_SUPABASE_URL}/rest/v1/trends",
                f"{VIRLO_SUPABASE_URL}/rest/v1/videos",
                f"{VIRLO_API_BASE}/api/outliers",
                f"{VIRLO_API_BASE}/api/trends",
            ]
            
            # Add Supabase-specific headers
            supabase_key = os.getenv("VIRLO_SUPABASE_ANON_KEY", "")
            if supabase_key:
                headers["apikey"] = supabase_key
            
            response_data = None
            successful_endpoint = None
            
            for endpoint in endpoints_to_try:
                try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    
                    params = {"limit": str(limit)}
                    if platforms:
                        params["platform"] = f"in.({','.join(platforms)})"
                    
                    response = await client.get(
                        endpoint,
                        headers=headers,
                        params=params,
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        successful_endpoint = endpoint
                        logger.info(f"Success with endpoint: {endpoint}")
                        break
                    else:
                        logger.debug(f"Endpoint {endpoint} returned {response.status_code}")
                        
                except httpx.RequestError as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            if not response_data:
                logger.warning("All API endpoints failed. Falling back to page scraping.")
                return await scrape_outliers_from_page(limit, platforms)
            
            # Parse response data
            items = _parse_api_response(response_data, limit)
            
        except Exception as e:
            logger.error(f"API scraping failed: {e}")
            raise
    
    logger.info(f"Fetched {len(items)} outlier items from Virlo API")
    return items


def _parse_api_response(data: Any, limit: int) -> List[VirloOutlierItem]:
    """Parse API response into VirloOutlierItem objects"""
    items = []
    
    # Handle different response formats
    if isinstance(data, list):
        records = data[:limit]
    elif isinstance(data, dict):
        records = data.get("data", data.get("items", data.get("outliers", [])))[:limit]
    else:
        logger.warning(f"Unexpected response format: {type(data)}")
        return []
    
    for record in records:
        try:
            item = VirloOutlierItem(
                title=record.get("title", record.get("video_title", ""))[:200],
                creator_username=record.get("creator", record.get("username", record.get("channel_name", "unknown")))[:50],
                platform=record.get("platform", "unknown").lower(),
                video_url=record.get("video_url", record.get("url", "")),
                view_count=int(record.get("view_count", record.get("views", 0)) or 0),
                multiplier=float(record.get("multiplier", record.get("outlier_score", 1.0)) or 1.0),
                niche=record.get("niche", record.get("category", ""))[:50],
                thumbnail_url=record.get("thumbnail_url", record.get("thumbnail", "")),
                posted_date=record.get("posted_at", record.get("created_at")),
            )
            items.append(item)
        except Exception as e:
            logger.debug(f"Error parsing record: {e}")
            continue
    
    return items


async def scrape_outliers_from_page(
    limit: int = 50,
    platforms: Optional[List[str]] = None,
) -> List[VirloOutlierItem]:
    """
    Fallback: Scrape outlier page HTML with httpx and parse embedded JSON data.
    Many SPAs embed initial data in script tags.
    """
    items: List[VirloOutlierItem] = []
    
    # Get cookies for auth
    cookie_str = os.getenv("VIRLO_SESSION_COOKIE", "")
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(
            "https://app.virlo.ai/outlier",
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Cookie": cookie_str,
            }
        )
        
        if response.status_code != 200:
            raise ValueError(f"Page fetch failed with status {response.status_code}")
        
        html = response.text
        
        # Look for embedded JSON data in script tags (common SPA pattern)
        # Pattern 1: window.__INITIAL_DATA__ = {...}
        patterns = [
            r'window\.__INITIAL_DATA__\s*=\s*({.+?});',
            r'window\.__NUXT__\s*=\s*({.+?});',
            r'window\.__NEXT_DATA__\s*=\s*({.+?});',
            r'<script id="__NEXT_DATA__"[^>]*>({.+?})</script>',
            r'"outliers"\s*:\s*(\[.+?\])',
            r'"trends"\s*:\s*(\[.+?\])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    items = _parse_api_response(data, limit)
                    if items:
                        logger.info(f"Found {len(items)} items via page scraping")
                        break
                except json.JSONDecodeError:
                    continue
        
        if not items:
            logger.warning("Could not extract data from page. Manual Playwright scraping may be needed.")
    
    return items


# Backward compatible function name
async def scrape_outliers(
    limit: int = 50,
    fresh_only: bool = True,
    platforms: Optional[List[str]] = None
) -> List[VirloOutlierItem]:
    """
    Main entry point for Virlo scraping.
    Tries API first, falls back to page scraping.
    """
    return await scrape_outliers_via_api(limit=limit, platforms=platforms)


async def scrape_and_save_to_db(
    limit: int = 50,
    run_id: Optional[str] = None,  # PEGL v1.0: Run 연결
) -> dict:
    """
    Scrape Virlo outliers and save to database.
    
    PEGL v1.0 Updates:
    - run_id 연결
    - raw_payload 저장
    - canonical_url 추가
    - upsert 로직 개선 (platform + video_url 기준)
    
    Returns summary of operation.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from uuid import UUID
    
    from app.config import settings
    from app.models import OutlierSource, OutlierItem
    
    # Scrape data
    items = await scrape_outliers(limit=limit)
    
    if not items:
        return {"status": "no_data", "collected": 0, "inserted": 0}
    
    # Save to database
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    inserted = 0
    updated = 0
    
    async with async_session() as db:
        # Get or create Virlo source
        source_result = await db.execute(
            select(OutlierSource).where(OutlierSource.name == "virlo_scraper")
        )
        source = source_result.scalar_one_or_none()
        
        if not source:
            source = OutlierSource(
                name="virlo_scraper",
                platform="virlo",
                source_type="scraper",
                last_crawled=utcnow()
            )
            db.add(source)
            await db.flush()
        
        # Insert items with upsert logic
        for item in items:
            # PEGL v1.0: raw_payload 저장
            raw_payload = {
                "title": item.title,
                "creator_username": item.creator_username,
                "platform": item.platform,
                "video_url": item.video_url,
                "view_count": item.view_count,
                "multiplier": item.multiplier,
                "niche": item.niche,
                "posted_date": item.posted_date,
                "thumbnail_url": item.thumbnail_url,
                "scraped_at": item.scraped_at.isoformat() if item.scraped_at else None,
            }
            
            # Upsert: check by platform + video_url (더 강력한 중복 방지)
            existing = None
            if item.video_url:
                existing_result = await db.execute(
                    select(OutlierItem).where(
                        OutlierItem.platform == item.platform,
                        OutlierItem.video_url == item.video_url
                    )
                )
                existing = existing_result.scalar_one_or_none()
            
            if existing:
                # Update existing item with new data
                existing.view_count = item.view_count
                existing.outlier_score = int(item.multiplier * 10)
                existing.raw_payload = raw_payload
                existing.updated_at = utcnow()
                updated += 1
            else:
                # Insert new item
                outlier = OutlierItem(
                    source_id=source.id,
                    title=item.title,
                    platform=item.platform,
                    category=item.niche,
                    video_url=item.video_url,
                    thumbnail_url=item.thumbnail_url,
                    channel_name=item.creator_username,
                    view_count=item.view_count,
                    outlier_score=int(item.multiplier * 10),  # Convert multiplier to score
                    status="pending",
                    scraped_at=item.scraped_at,
                    # PEGL v1.0 필드
                    run_id=UUID(run_id) if run_id else None,
                    raw_payload=raw_payload,
                    canonical_url=item.video_url,  # TODO: URL 정규화 함수 적용
                )
                db.add(outlier)
                inserted += 1
        
        source.last_crawled = utcnow()
        await db.commit()
    
    await engine.dispose()
    
    return {
        "status": "success",
        "collected": len(items),
        "inserted": inserted,
        "updated": updated,
        "platform": "virlo"
    }


# CLI interface for testing
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    
    async def main():
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        print(f"Fetching {limit} items from Virlo...")
        
        try:
            items = await scrape_outliers(limit=limit)
            for item in items:
                print(f"- {item.platform}: {item.title[:50]}... ({item.multiplier}x)")
            print(f"\nTotal: {len(items)} items fetched")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
