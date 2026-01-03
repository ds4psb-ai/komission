"""
Virlo Outlier Scraper using httpx API calls (PEGL v1.0)
Fetches viral outlier data from Virlo's internal API endpoints

PEGL v1.0: 스키마 검증 적용
2025-12-31: 하드닝 - Enum 수정, 에러 핸들링 강화
"""
import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.utils.time import utcnow
from app.utils.url_normalizer import normalize_video_url, get_external_id
from app.validators.schema_validator import validate_outlier_schema, SchemaValidationError
from app.models import OutlierItemStatus  # 하드닝: Enum import

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


def get_proxy_url() -> Optional[str]:
    """
    Build NordVPN SOCKS5 proxy URL from environment variables.
    
    Required env vars:
        NORDVPN_SOCKS_HOST: Server hostname (e.g., us.socks.nordhold.net)
        NORDVPN_SOCKS_USER: SOCKS5 username from NordVPN dashboard
        NORDVPN_SOCKS_PASS: SOCKS5 password from NordVPN dashboard
    
    Returns:
        socks5h:// URL for httpx proxy, or None if not configured
    """
    host = os.getenv("NORDVPN_SOCKS_HOST")  # e.g., us.socks.nordhold.net
    user = os.getenv("NORDVPN_SOCKS_USER")  
    passwd = os.getenv("NORDVPN_SOCKS_PASS")
    
    if host and user and passwd:
        # Use socks5h:// for remote DNS resolution (prevents DNS leaks)
        return f"socks5h://{user}:{passwd}@{host}:1080"
    return None


# Known Virlo API endpoints (Supabase-based)
VIRLO_API_BASE = "https://api.virlo.ai"  # or supabase endpoint
VIRLO_SUPABASE_URL = os.getenv("VIRLO_SUPABASE_URL", "https://kttfukgfcwvmtgggucyo.supabase.co")
# Supabase anonymous key for Virlo (public, safe to commit)
VIRLO_SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0dGZ1a2dmY3d2bXRnZ2d1Y3lvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxMjYyNDMsImV4cCI6MjA1OTcwMjI0M30.CdQL7FaJdMqBNXXhC2EqXhEamuYBzu9MqdESIzqQ-fA"
# Virlo Supabase Storage bucket for thumbnails
VIRLO_THUMBNAIL_STORAGE_URL = f"{VIRLO_SUPABASE_URL}/storage/v1/object/public/thumbnails"


def _build_thumbnail_url(filename: Optional[str]) -> str:
    """Build full thumbnail URL from Virlo's filename-only response."""
    if not filename:
        return ""
    # If already a full URL, return as-is
    if filename.startswith("http"):
        return filename
    # Prepend Virlo Supabase storage URL
    return f"{VIRLO_THUMBNAIL_STORAGE_URL}/{filename}"


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
    
    proxy_url = get_proxy_url()
    if proxy_url:
        # Mask password in log
        masked = proxy_url.split('@')[1] if '@' in proxy_url else proxy_url
        logger.info(f"🔀 Using SOCKS5 proxy: {masked}")
    
    async with httpx.AsyncClient(timeout=30.0, proxy=proxy_url) as client:
        try:
            # Use the correct Virlo RPC endpoint (discovered 2025-12-31)
            platform_param = (platforms[0] if platforms else "tiktok")
            
            rpc_body = {
                "limit_param": limit,
                "offset_param": 0,
                "platform_param": platform_param,
                "sort_by_param": "fresh_content",  # faster than most_viral
                "time_filter_param": None,
                "niche_filter_param": category
            }
            
            # Add Supabase-specific headers
            headers["apikey"] = VIRLO_SUPABASE_ANON_KEY
            
            # Use the correct RPC endpoint
            rpc_endpoint = f"{VIRLO_SUPABASE_URL}/rest/v1/rpc/get_viral_outliers_fresh_v2"
            logger.info(f"Calling Virlo RPC: {rpc_endpoint}")
            
            response = await client.post(
                rpc_endpoint,
                headers=headers,
                json=rpc_body,
            )
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Success! Got {len(response_data)} items from Virlo")
                items = _parse_api_response(response_data, limit)
            else:
                logger.warning(f"RPC failed with {response.status_code}: {response.text[:200]}")
                return await scrape_outliers_from_page(limit, platforms)
            
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
        # 하드닝: 첫 번째 레코드 필드 로깅
        if records and isinstance(records[0], dict):
            logger.info(f"API response fields: {list(records[0].keys())}")
            logger.debug(f"First record sample: {records[0]}")
    elif isinstance(data, dict):
        raw_records = data.get("data", data.get("items", data.get("outliers", [])))
        if not isinstance(raw_records, list):
            logger.warning(f"Unexpected records format: {type(raw_records)}")
            return []
        records = raw_records[:limit]
    else:
        logger.warning(f"Unexpected response format: {type(data)}")
        return []
    
    for record in records:
        try:
            # Virlo RPC response fields (2025-12-31 실제 응답 기준):
            # id, url, type, niche, views, authors, view_count, description,
            # publish_date, thumbnail_url, viralityScore, number_of_likes,
            # number_of_shares, number_of_comments
            
            # Get video URL
            video_url = record.get("url") or ""
            
            # Get creator username from 'authors' field
            # Virlo API returns authors as a dict object with username/nickname fields
            authors = record.get("authors")
            if isinstance(authors, dict):
                # New format: authors is an object with username, nickname, avatar_url
                creator = authors.get("username") or authors.get("nickname") or "unknown"
            elif isinstance(authors, list) and len(authors) > 0:
                creator = authors[0] if isinstance(authors[0], str) else str(authors[0])
            elif isinstance(authors, str):
                creator = authors
            else:
                creator = "unknown"
            
            # Get title/description
            title = record.get("description") or f"@{creator}"
            
            # Get niche/category
            niche = record.get("niche") or record.get("type") or "trending"
            
            # Get outlier score - 'viralityScore' is the key field!
            virality_score = record.get("viralityScore")
            if virality_score is not None:
                outlier_score = float(virality_score)
            else:
                outlier_score = 1.0
            
            # Get view count
            view_count = int(record.get("view_count") or record.get("views") or 0)
            
            # Get engagement metrics
            like_count = record.get("number_of_likes")
            share_count = record.get("number_of_shares")
            comment_count = record.get("number_of_comments")
            
            item = VirloOutlierItem(
                title=str(title)[:200] if title else f"@{creator}",
                creator_username=str(creator)[:50] if creator else "unknown",
                platform=str(record.get("type", "tiktok")).lower(),
                video_url=video_url,
                view_count=view_count,
                multiplier=outlier_score,
                niche=str(niche)[:50] if niche else "trending",
                thumbnail_url=_build_thumbnail_url(record.get("thumbnail_url")),
                posted_date=record.get("publish_date"),
            )
            # Store extra metadata for later use
            item._like_count = like_count
            item._share_count = share_count
            item._comment_count = comment_count
            items.append(item)
            
        except Exception as e:
            logger.debug(f"Error parsing record: {e}, record keys: {record.keys() if isinstance(record, dict) else 'N/A'}")
            continue
    
    logger.info(f"Parsed {len(items)} items, sample: {items[0].title[:30] if items else 'none'}...")
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
    
    proxy_url = get_proxy_url()
    if proxy_url:
        masked = proxy_url.split('@')[1] if '@' in proxy_url else proxy_url
        logger.info(f"🔀 Using SOCKS5 proxy for page scrape: {masked}")
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, proxy=proxy_url) as client:
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
    platforms: Optional[List[str]] = None,  # 플랫폼 필터 (tiktok, youtube, instagram)
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
    # UUID는 모듈 레벨에서 import됨
    
    from app.config import settings
    from app.models import OutlierSource, OutlierItem
    
    # Scrape data
    items = await scrape_outliers(limit=limit, platforms=platforms)
    
    if not items:
        return {"status": "no_data", "collected": 0, "inserted": 0}
    
    # Save to database
    engine = create_async_engine(settings.DATABASE_URL)
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
                base_url=VIRLO_SUPABASE_URL,
                auth_type="jwt",
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
            
            canonical_url = normalize_video_url(item.video_url, item.platform) if item.video_url else None
            external_id = get_external_id(canonical_url or item.video_url or "")
            if not external_id:
                seed = item.video_url or item.title or item.creator_username or ""
                external_id = f"virlo_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"

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
            if not existing and external_id:
                existing_result = await db.execute(
                    select(OutlierItem).where(OutlierItem.external_id == external_id)
                )
                existing = existing_result.scalar_one_or_none()
            
            if existing:
                # Update existing item with new data
                existing.view_count = item.view_count
                existing.outlier_score = int(item.multiplier * 10)
                existing.raw_payload = raw_payload
                existing.updated_at = utcnow()
                existing.creator_username = item.creator_username  # Update creator handle
                if canonical_url:
                    existing.canonical_url = canonical_url
                # Parse and update upload_date
                if item.posted_date:
                    try:
                        from dateutil import parser as dateparser
                        existing.upload_date = dateparser.parse(item.posted_date)
                    except Exception:
                        pass
                updated += 1
            else:
                # Parse upload_date from posted_date
                upload_date_parsed = None
                if item.posted_date:
                    try:
                        from dateutil import parser as dateparser
                        upload_date_parsed = dateparser.parse(item.posted_date)
                    except Exception:
                        pass
                
                # Insert new item
                outlier = OutlierItem(
                    source_id=source.id,
                    external_id=external_id,
                    title=item.title,
                    platform=item.platform,
                    category=item.niche,
                    video_url=item.video_url,
                    thumbnail_url=item.thumbnail_url,
                    view_count=item.view_count,
                    outlier_score=int(item.multiplier * 10),  # Convert multiplier to score
                    creator_username=item.creator_username,  # Store creator handle
                    upload_date=upload_date_parsed,  # Store actual video upload date
                    status=OutlierItemStatus.PENDING,  # 하드닝: Enum 사용
                    crawled_at=item.scraped_at or utcnow(),
                    # PEGL v1.0 필드
                    run_id=UUID(run_id) if run_id else None,
                    raw_payload=raw_payload,
                    canonical_url=canonical_url,
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


async def discover_and_enrich_urls(
    limit: int = 50,
    platform_filter: str = "tiktok",
) -> Dict[str, Any]:
    """
    Virlo → TikTok 브릿지: Virlo에서 아웃라이어 발견 후 
    표준 크롤러로 메타데이터 보강하여 Ops 파이프라인에 적재.
    
    Flow:
    1. Virlo API로 아웃라이어 URL 발견
    2. TikTok 크롤러로 완전한 메타데이터 수집
    3. Ops Pipeline (OutlierItem) 저장
    4. VDG 분석 가능 상태로 준비
    
    Returns:
        Dict with discovered URLs and enriched items
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    from app.config import settings
    from app.models import OutlierSource, OutlierItem
    # OutlierItemStatus는 모듈 레벨에서 import됨
    from app.schemas.evidence import OutlierCrawlItem
    
    # Step 1: Virlo에서 아웃라이어 발견
    logger.info(f"Step 1: Discovering outliers from Virlo (limit={limit}, platform={platform_filter})")
    virlo_items = await scrape_outliers(limit=limit, platforms=[platform_filter])
    
    if not virlo_items:
        return {"status": "no_virlo_data", "discovered": 0, "enriched": 0, "inserted": 0}
    
    logger.info(f"Discovered {len(virlo_items)} items from Virlo")
    
    # Step 2: 표준 OutlierCrawlItem으로 변환 (TikTok 크롤러 스키마와 호환)
    enriched_items: List[OutlierCrawlItem] = []
    
    for item in virlo_items:
        if not item.video_url:
            logger.debug(f"Skipping item without URL: {item.title[:30]}...")
            continue
        
        # Virlo 데이터를 OutlierCrawlItem으로 변환
        # 이렇게 하면 run_scheduled_crawl.py의 표준 저장 로직과 호환됨
        
        # Get extra metadata from private attributes
        like_count = getattr(item, '_like_count', None)
        share_count = getattr(item, '_share_count', None)
        comment_count = getattr(item, '_comment_count', None)
        
        canonical_url = normalize_video_url(item.video_url, item.platform) if item.video_url else None
        external_id = get_external_id(canonical_url or item.video_url or "")
        if not external_id:
            seed = item.video_url or item.title or item.creator_username or ""
            external_id = f"virlo_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"

        crawl_item = OutlierCrawlItem(
            source_name="virlo_discovery",
            external_id=external_id,
            video_url=item.video_url,
            platform=item.platform,
            category=item.niche or "trending",
            title=item.title or f"@{item.creator_username}",
            thumbnail_url=item.thumbnail_url,
            view_count=item.view_count,
            like_count=int(like_count) if like_count else None,
            share_count=int(share_count) if share_count else None,
            growth_rate=f"{int(item.multiplier)}x outlier",
            outlier_score=item.multiplier,  # viralityScore 그대로 사용
            outlier_tier=_calculate_tier(item.multiplier),
            creator_avg_views=0,
            engagement_rate=0.0,
            creator_username=item.creator_username,  # 크리에이터 핸들 전달
        )
        enriched_items.append(crawl_item)
    
    logger.info(f"Enriched {len(enriched_items)} items to standard schema")
    
    # Step 3: DB 저장 (표준 Ops 파이프라인)
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    inserted = 0
    skipped_duplicates = 0
    
    async with async_session() as db:
        # Get or create Virlo discovery source
        source_result = await db.execute(
            select(OutlierSource).where(OutlierSource.name == "virlo_discovery")
        )
        source = source_result.scalar_one_or_none()
        
        if not source:
            source = OutlierSource(
                name="virlo_discovery",
                base_url="https://app.virlo.ai",
                auth_type="jwt",
                is_active=True,
                last_crawled=utcnow()
            )
            db.add(source)
            await db.flush()
        
        for item in enriched_items:
            # 중복 체크 (video_url/external_id 기준)
            existing = await db.execute(
                select(OutlierItem).where(OutlierItem.video_url == item.video_url)
            )
            if existing.scalar_one_or_none():
                skipped_duplicates += 1
                continue
            if item.external_id:
                existing = await db.execute(
                    select(OutlierItem).where(OutlierItem.external_id == item.external_id)
                )
                if existing.scalar_one_or_none():
                    skipped_duplicates += 1
                    continue
            
            # PEGL v1.0 raw_payload
            raw_payload = {
                "source": "virlo_discovery",
                "external_id": item.external_id,
                "video_url": item.video_url,
                "platform": item.platform,
                "category": item.category,
                "title": item.title,
                "view_count": item.view_count,
                "outlier_score": item.outlier_score,
                "outlier_tier": item.outlier_tier,
                "growth_rate": item.growth_rate,
                "creator_username": item.creator_username,  # 크리에이터 정보 저장
                "discovered_at": utcnow().isoformat(),
            }
            
            canonical_url = normalize_video_url(item.video_url, item.platform) if item.video_url else None
            outlier = OutlierItem(
                source_id=source.id,
                external_id=item.external_id,
                video_url=item.video_url,
                platform=item.platform,
                category=item.category,
                title=item.title,
                thumbnail_url=item.thumbnail_url,
                view_count=item.view_count,
                like_count=item.like_count,
                share_count=item.share_count,
                growth_rate=item.growth_rate,
                outlier_score=item.outlier_score,
                outlier_tier=item.outlier_tier,
                creator_username=item.creator_username,  # 크리에이터 핸들 저장
                status=OutlierItemStatus.PENDING,  # ← Ops 파이프라인 시작점
                crawled_at=utcnow(),
                raw_payload=raw_payload,
                canonical_url=canonical_url,
            )
            db.add(outlier)
            inserted += 1
        
        source.last_crawled = utcnow()
        await db.commit()
    
    await engine.dispose()
    
    result = {
        "status": "success",
        "discovered": len(virlo_items),
        "enriched": len(enriched_items),
        "inserted": inserted,
        "skipped_duplicates": skipped_duplicates,
        "platform": platform_filter,
        "pipeline_ready": True,  # VDG 분석 준비 완료
    }
    
    logger.info(f"Virlo discovery complete: {result}")
    return result


def _calculate_tier(multiplier: float) -> Optional[str]:
    """Calculate outlier tier from multiplier."""
    if multiplier >= 500: return "S"
    elif multiplier >= 200: return "A"
    elif multiplier >= 100: return "B"
    elif multiplier >= 50: return "C"
    return None


# CLI interface for testing
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    
    async def main():
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        mode = sys.argv[2] if len(sys.argv) > 2 else "discover"
        
        print(f"Mode: {mode}, Limit: {limit}")
        
        try:
            if mode == "bridge":
                # 브릿지 모드: Virlo 발견 → 표준 파이프라인 저장
                result = await discover_and_enrich_urls(limit=limit)
                print(f"\n=== BRIDGE RESULT ===")
                print(result)
            else:
                # 기존 발견 모드
                items = await scrape_outliers(limit=limit)
                for item in items:
                    print(f"- {item.platform}: {item.title[:50]}... ({item.multiplier}x)")
                    print(f"  URL: {item.video_url}")
                print(f"\nTotal: {len(items)} items fetched")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
