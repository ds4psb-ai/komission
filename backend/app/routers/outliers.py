"""
Outliers API Router - Evidence Loop Phase 1
Handles outlier source management and candidate crawling
"""
import hashlib
import csv
import io
import asyncio
import math
from app.utils.time import utcnow, days_ago

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models import (
    OutlierSource,
    OutlierItem,
    OutlierItemStatus,
    RemixNode,
    NodeLayer,
    NodePermission,
    NodeGovernance,
)
from app.routers.auth import require_curator, get_current_user, get_current_user_optional, User
from app.services.remix_nodes import generate_remix_node_id
from app.schemas.evidence import (
    OutlierSourceCreate,
    OutlierSourceResponse,
    OutlierItemCreate,
    OutlierItemManualCreate,
    OutlierItemResponse,
    OutlierCandidatesResponse,
    OutlierPromoteRequest,
    OutlierRejectRequest,
)

router = APIRouter(prefix="/outliers", tags=["Outliers"])


# ==================
# URL RESOLUTION API
# ==================
@router.get("/utils/resolve-url")
async def resolve_short_url(url: str):
    """
    Resolve TikTok short URLs (vt.tiktok.com, vm.tiktok.com) to full URLs.
    Returns the resolved canonical URL with extracted video ID.
    
    Used by frontend to embed TikTok videos from short links.
    """
    from app.services.social_metadata import normalize_url
    from app.utils.url_normalizer import normalize_video_url
    
    result = normalize_url(url, expand_short=True)
    return {
        "original_url": url,
        "canonical_url": normalize_video_url(result["canonical_url"], result["platform"]),
        "platform": result["platform"],
        "content_id": result["content_id"],
    }


# ==================
# AUTO-ANALYSIS HELPER
# ==================
def trigger_auto_analysis(node_id: str, video_url: str, outlier_item_id: str = None):
    """
    Background task to trigger Gemini analysis after promote.
    Uses sync wrapper for async operations.
    
    Now also saves to normalized viral_kicks tables.
    """
    async def _run_analysis():
        from app.services.gemini_pipeline import gemini_pipeline
        from app.services.vdg_2pass.vdg_db_saver import vdg_db_saver
        from app.database import async_session_maker
        from app.models import RemixNode
        
        try:
            print(f"🚀 Auto-analyzing node {node_id}...")
            result = await gemini_pipeline.analyze_video_v4(video_url, node_id)
            
            # Save result to database
            async with async_session_maker() as db:
                stmt = select(RemixNode).where(RemixNode.node_id == node_id)
                db_result = await db.execute(stmt)
                node = db_result.scalar_one_or_none()
                
                if node:
                    vdg_data = result.model_dump()
                    node.gemini_analysis = vdg_data
                    await db.commit()
                    print(f"✅ Auto-analysis complete for {node_id}")
                    
                    # P1-1: Save to normalized viral_kicks tables
                    try:
                        save_result = await vdg_db_saver.save_vdg_to_db(
                            db=db,
                            node_id=node_id,
                            vdg_data=vdg_data,
                            video_path=None,  # Already deleted after pipeline
                            outlier_item_id=outlier_item_id,
                        )
                        print(f"💾 VDG DB saved: {save_result['kicks_saved']} kicks, "
                              f"{save_result['keyframes_saved']} keyframes")
                        print(f"🏁 Full VDG analysis complete for {node_id}")
                    except Exception as e:
                        print(f"⚠️ VDG DB save failed (analysis still saved): {e}")
                        print(f"🏁 VDG analysis complete for {node_id} (DB save failed)")
                else:
                    print(f"⚠️ Node {node_id} not found for analysis save")
        except Exception as e:
            print(f"❌ Auto-analysis failed for {node_id}: {e}")
    
    # Run async function in new event loop (background task context)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_run_analysis())
        else:
            asyncio.run(_run_analysis())
    except RuntimeError:
        asyncio.run(_run_analysis())


def _temporal_phase_for_age(age_days: int) -> str:
    """
    Determine temporal phase based on pattern age.
    
    T0 (0-7 days): Fresh pattern, 100% homage works
    T1 (8-14 days): Early decay, 95% homage
    T2 (15-28 days): Mid decay, 90% homage
    T3 (29-42 days): Late decay, 85% homage
    T4 (43+ days): Stale, high creativity needed
    """
    if age_days <= 7:
        return "T0"
    if age_days <= 14:
        return "T1"
    if age_days <= 28:
        return "T2"
    if age_days <= 42:
        return "T3"
    return "T4"


def _calculate_burstiness(item) -> float:
    """
    Calculate burstiness index: how much this video outperformed creator's average.
    Higher = more bursty/viral spike.
    
    Formula: log2(views / creator_avg + 1) normalized to 0-1 range
    """
    if not item:
        return 0.0
    views = item.view_count or 0
    creator_avg = item.creator_avg_views or 1
    if creator_avg <= 0:
        creator_avg = 1
    
    # Log ratio scaled to 0-1 range (cap at 10x = ~1.0)
    ratio = views / creator_avg
    burst = min(1.0, math.log2(ratio + 1) / 3.32)  # 3.32 = log2(10)
    return round(burst, 4)


async def _get_or_create_source(db: AsyncSession, name: str) -> OutlierSource:
    result = await db.execute(select(OutlierSource).where(OutlierSource.name == name))
    source = result.scalar_one_or_none()
    if source:
        return source

    source = OutlierSource(
        name=name,
        base_url="manual://",
        auth_type="none",
        crawl_interval_hours=24,
    )
    db.add(source)
    await db.flush()
    return source


# ==================
# OUTLIER SOURCES
# ==================

@router.post("/sources", response_model=OutlierSourceResponse)
async def create_source(
    source: OutlierSourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """크롤링 소스 등록"""
    new_source = OutlierSource(
        name=source.name,
        base_url=source.base_url,
        auth_type=source.auth_type,
        auth_config=source.auth_config,
        crawl_interval_hours=source.crawl_interval_hours,
    )
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    return OutlierSourceResponse(
        id=str(new_source.id),
        name=new_source.name,
        base_url=new_source.base_url,
        auth_type=new_source.auth_type,
        last_crawled=new_source.last_crawled,
        is_active=new_source.is_active,
        created_at=new_source.created_at,
    )


@router.get("/sources", response_model=List[OutlierSourceResponse])
async def list_sources(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """등록된 소스 목록 조회"""
    query = select(OutlierSource)
    if active_only:
        query = query.where(OutlierSource.is_active == True)
    result = await db.execute(query)
    sources = result.scalars().all()
    return [
        OutlierSourceResponse(
            id=str(s.id),
            name=s.name,
            base_url=s.base_url,
            auth_type=s.auth_type,
            last_crawled=s.last_crawled,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in sources
    ]


# ==================
# OUTLIER ITEMS LIST (for frontend)
# ==================

@router.get("/")
@router.get("")
async def list_outliers(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    tier: Optional[str] = None,
    status: Optional[str] = None,
    freshness: Optional[str] = Query(default="7d"),
    sort_by: Optional[str] = Query(default="outlier_score"),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    아웃라이어 목록 조회 (프론트엔드용)
    프론트엔드에서 /api/v1/outliers 호출 시 사용
    """
    query = select(OutlierItem)
    
    # Filters
    if category:
        query = query.where(OutlierItem.category == category)
    if platform:
        query = query.where(OutlierItem.platform == platform)
    if tier:
        query = query.where(OutlierItem.outlier_tier == tier)
    if status:
        # Map status string to enum (case-insensitive)
        status_upper = status.upper()
        status_enum = getattr(OutlierItemStatus, status_upper, None)
        if status_enum:
            query = query.where(OutlierItem.status == status_enum)
    
    # Freshness filter
    if freshness == "24h":
        from datetime import timedelta
        cutoff = utcnow() - timedelta(hours=24)
        query = query.where(OutlierItem.crawled_at >= cutoff)
    elif freshness == "7d":
        cutoff = days_ago(7)
        query = query.where(OutlierItem.crawled_at >= cutoff)
    elif freshness == "30d":
        cutoff = days_ago(30)
        query = query.where(OutlierItem.crawled_at >= cutoff)
    
    # Sorting
    if sort_by == "view_count":
        query = query.order_by(OutlierItem.view_count.desc())
    elif sort_by == "crawled_at":
        query = query.order_by(OutlierItem.crawled_at.desc())
    else:
        query = query.order_by(OutlierItem.outlier_score.desc().nullslast())
    
    query = query.limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "total": len(items),
        "items": [
            {
                "id": str(i.id),
                "external_id": i.external_id,
                "video_url": i.video_url,
                "platform": i.platform,
                "category": i.category,
                "title": i.title,
                "thumbnail_url": i.thumbnail_url,
                "view_count": i.view_count or 0,
                "like_count": i.like_count or 0,
                "share_count": i.share_count or 0,
                "outlier_score": i.outlier_score or 0,
                "outlier_tier": i.outlier_tier or "C",
                "creator_avg_views": 10000,  # TODO: Calculate from creator data
                "engagement_rate": (i.like_count or 0) / max(i.view_count or 1, 1),
                "crawled_at": i.crawled_at.isoformat() if i.crawled_at else None,
                "status": i.status.value.lower() if i.status else "pending",
                # VDG Analysis Gate
                "analysis_status": i.analysis_status or "pending",
                "promoted_to_node_id": str(i.promoted_to_node_id) if i.promoted_to_node_id else None,
                "best_comments_count": len(i.best_comments) if i.best_comments else 0,
                # VDG Analysis Data (from raw_payload)
                "vdg_analysis": (i.raw_payload or {}).get("vdg_analysis") if i.raw_payload else None,
            }
            for i in items
        ],
    }


# ==================
# OUTLIER ITEMS (CANDIDATES)
# ==================

@router.post("/items", response_model=OutlierItemResponse)
async def create_item(
    item: OutlierItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """아웃라이어 후보 수동 등록 (크롤러 또는 수동)
    
    video_url 기준으로 중복 체크 수행
    """
    # Check for duplicate video_url
    existing = await db.execute(
        select(OutlierItem).where(OutlierItem.video_url == item.video_url)
    )
    existing_item = existing.scalar_one_or_none()
    if existing_item:
        return _item_to_response(existing_item)  # Return existing instead of error
    
    new_item = OutlierItem(
        source_id=UUID(item.source_id),
        external_id=item.external_id,
        video_url=item.video_url,
        title=item.title,
        thumbnail_url=item.thumbnail_url,
        platform=item.platform,
        category=item.category,
        view_count=item.view_count,
        like_count=item.like_count,
        share_count=item.share_count,
        growth_rate=item.growth_rate,
        status=OutlierItemStatus.PENDING,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return _item_to_response(new_item)


@router.post("/items/manual", response_model=OutlierItemResponse)
async def create_item_manual(
    item: OutlierItemManualCreate,
    current_user: User = Depends(require_curator),
    db: AsyncSession = Depends(get_db)
):
    """관리자 수동 아웃라이어 등록 (링크 기반)
    
    TikTok URL인 경우 자동으로 메타데이터 추출:
    - view_count, like_count, share_count
    - thumbnail_url (oEmbed 사용)
    - title (description)
    """
    external_id = f"manual_{hashlib.sha256(item.video_url.encode('utf-8')).hexdigest()}"
    existing = await db.execute(
        select(OutlierItem).where(OutlierItem.external_id == external_id)
    )
    existing_item = existing.scalar_one_or_none()
    if existing_item:
        return _item_to_response(existing_item)

    source_name = (item.source_name or "manual").strip() or "manual"
    source = await _get_or_create_source(db, source_name)
    
    # TikTok 메타데이터 자동 추출
    view_count = item.view_count or 0
    like_count = item.like_count
    share_count = item.share_count
    thumbnail_url = item.thumbnail_url
    title = item.title
    comment_count = 0
    
    if 'tiktok' in item.platform.lower():
        try:
            from app.services.tiktok_extractor import extract_tiktok_complete
            import httpx
            
            print(f"🔍 TikTok 메타데이터 자동 추출: {item.video_url[:50]}...")
            tiktok_data = await extract_tiktok_complete(item.video_url, include_comments=False)
            
            # 추출 성공 시 메타데이터 사용
            if tiktok_data.get('view_count', 0) > 0:
                view_count = tiktok_data['view_count']
                like_count = tiktok_data.get('like_count', like_count)
                share_count = tiktok_data.get('share_count', share_count)
                title = tiktok_data.get('title') or title
                print(f"✅ 추출 성공: {view_count:,} views, {like_count:,} likes")
            
            # oEmbed로 썸네일 가져오기
            if not thumbnail_url:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        oembed_url = f"https://www.tiktok.com/oembed?url={item.video_url}"
                        resp = await client.get(oembed_url)
                        if resp.status_code == 200:
                            oembed_data = resp.json()
                            thumbnail_url = oembed_data.get('thumbnail_url')
                            if thumbnail_url:
                                print(f"📷 썸네일: {thumbnail_url[:50]}...")
                except Exception as te:
                    print(f"⚠️ oEmbed 실패: {te}")
                    
        except Exception as e:
            print(f"⚠️ TikTok 메타데이터 추출 실패: {e}")
            # 실패해도 계속 진행 (기본값 사용)

    elif 'youtube' in item.platform.lower():
        # YouTube 메타데이터 자동 추출 (Data API v3)
        try:
            from app.crawlers.youtube import YouTubeCrawler
            import re
            
            # video_id 추출
            video_id_match = re.search(r'(?:v=|shorts/|youtu\.be/)([^&?/]+)', item.video_url)
            if video_id_match:
                video_id = video_id_match.group(1)
                print(f"🔍 YouTube 메타데이터 자동 추출: {video_id}...")
                
                with YouTubeCrawler() as crawler:
                    details = crawler._get_video_details([video_id])
                    
                    if details:
                        video = details[0]
                        snippet = video.get('snippet', {})
                        statistics = video.get('statistics', {})
                        
                        view_count = int(statistics.get('viewCount', 0))
                        like_count = int(statistics.get('likeCount', 0))
                        comment_count = int(statistics.get('commentCount', 0))
                        title = snippet.get('title') or title
                        
                        # 썸네일: maxres > high > medium
                        thumbs = snippet.get('thumbnails', {})
                        thumbnail_url = (
                            thumbs.get('maxres', {}).get('url') or
                            thumbs.get('high', {}).get('url') or
                            thumbs.get('medium', {}).get('url') or
                            thumbnail_url
                        )
                        
                        print(f"✅ YouTube 추출: {view_count:,} views, {like_count:,} likes")
                        
        except Exception as e:
            print(f"⚠️ YouTube 메타데이터 추출 실패: {e}")

    # P0: outlier_score 자동 계산
    outlier_score = None
    outlier_tier = 'C'  # 기본값
    
    if view_count and view_count > 0:
        # 크리에이터 평균 조회수 추정 (없으면 10,000 기본값)
        creator_avg_views = 10000
        
        # 추출된 작성자 ID로 기존 데이터 조회 시도
        if 'tiktok' in item.platform.lower():
            try:
                # 같은 플랫폼의 기존 아이템들 평균 조회수 참조
                from sqlalchemy import func as sqlfunc
                avg_result = await db.execute(
                    select(sqlfunc.avg(OutlierItem.view_count))
                    .where(OutlierItem.platform == 'tiktok')
                    .where(OutlierItem.view_count > 0)
                )
                db_avg = avg_result.scalar()
                if db_avg and db_avg > 0:
                    creator_avg_views = int(db_avg * 0.1)  # 평균의 10%를 기준으로
            except Exception:
                pass
        
        # outlier_score 계산 (조회수 / 크리에이터 평균)
        outlier_score = round(view_count / max(creator_avg_views, 1), 2)
        
        # tier 자동 결정
        if outlier_score >= 500:
            outlier_tier = 'S'
        elif outlier_score >= 200:
            outlier_tier = 'A'
        elif outlier_score >= 100:
            outlier_tier = 'B'
        else:
            outlier_tier = 'C'
        
        print(f"📊 자동 계산: score={outlier_score}x, tier={outlier_tier}")

    new_item = OutlierItem(
        source_id=source.id,
        external_id=external_id,
        video_url=item.video_url,
        title=title,
        thumbnail_url=thumbnail_url,
        platform=item.platform,
        category=item.category,
        view_count=view_count,
        like_count=like_count,
        share_count=share_count,
        outlier_score=outlier_score,
        outlier_tier=outlier_tier,
        growth_rate=item.growth_rate,
        status=OutlierItemStatus.PENDING,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return _item_to_response(new_item)


# ==================
# GET INDIVIDUAL ITEM
# ==================

@router.get("/items/{item_id}")
async def get_outlier_item(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single outlier item by ID.
    Used by /video/[id] page to display video details.
    
    If item is promoted, includes gemini_analysis from the RemixNode
    for displaying Hook, Shotlist, Audio, Timing guide.
    """
    try:
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == item_uuid)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Base response
    response = {
        "id": str(item.id),
        "source_id": str(item.source_id),
        "external_id": item.external_id,
        "video_url": item.video_url,
        "title": item.title,
        "thumbnail_url": item.thumbnail_url,
        "platform": item.platform,
        "category": item.category,
        "view_count": item.view_count,
        "like_count": item.like_count,
        "growth_rate": item.growth_rate,
        "status": item.status.value.lower() if item.status else None,
        "promoted_to_node_id": str(item.promoted_to_node_id) if item.promoted_to_node_id else None,
        "crawled_at": item.crawled_at.isoformat() if item.crawled_at else None,
        "outlier_tier": item.outlier_tier,
        "outlier_score": item.outlier_score,
        "creator_avg_views": item.creator_avg_views,
        "engagement_rate": item.engagement_rate,
        "best_comments": item.best_comments,
        "analysis_status": item.analysis_status,
    }
    
    # If promoted, fetch VDG analysis from RemixNode
    if item.promoted_to_node_id:
        node_result = await db.execute(
            select(RemixNode).where(RemixNode.id == item.promoted_to_node_id)
        )
        node = node_result.scalar_one_or_none()
        
        if node and node.gemini_analysis:
            analysis = node.gemini_analysis
            
            # Transform gemini_analysis to frontend VideoAnalysis format
            response["analysis"] = {
                "hook_pattern": _extract_hook_pattern(analysis),
                "hook_score": _extract_hook_score(analysis),
                "hook_duration_sec": _extract_hook_duration(analysis),
                "visual_patterns": _extract_visual_patterns(analysis),
                "audio_pattern": _extract_audio_pattern(analysis),
                "shotlist": _extract_shotlist(analysis),
                "timing": _extract_timing(analysis),
                "do_not": _extract_do_not(analysis),
                "invariant": _extract_invariant(analysis),
                "variable": _extract_variable(analysis),
                "best_comment": item.best_comments[0] if item.best_comments else None,
            }
            
            # L2 Integration: Try to generate DirectorPack from VDG for richer guides
            try:
                from app.services.vdg_2pass.director_compiler import compile_director_pack
                from app.schemas.vdg_v4 import VDGv4
                
                # Check if VDG v4 schema available (has hook_genome, scenes)
                if "hook_genome" in analysis and "scenes" in analysis:
                    vdg_v4 = VDGv4(
                        content_id=node.node_id,
                        duration_sec=analysis.get("duration_sec", 0),
                        **{k: v for k, v in analysis.items() 
                           if k not in ["content_id", "duration_sec"]}
                    )
                    director_pack = compile_director_pack(vdg_v4)
                    
                    # Use DirectorPack for richer guide
                    dp_guide = _extract_shooting_guide_from_director_pack(
                        director_pack.model_dump()
                    )
                    
                    # Merge with VDG v3 guide (DirectorPack takes priority)
                    if dp_guide.get("invariant"):
                        response["analysis"]["invariant"] = dp_guide["invariant"]
                    if dp_guide.get("variable"):
                        response["analysis"]["variable"] = dp_guide["variable"]
                    if dp_guide.get("do_not"):
                        response["analysis"]["do_not"] = dp_guide["do_not"]
                    
                    # Add DirectorPack extras
                    response["analysis"]["checkpoints"] = dp_guide.get("checkpoints", [])
                    
                    # Add DirectorPack for coaching integration
                    response["director_pack"] = director_pack.model_dump()
                    
            except Exception as e:
                # Non-fatal: fall back to VDG v3 guide
                import logging
                logging.getLogger(__name__).warning(f"DirectorPack generation failed: {e}")
            
            # Add platform-specific tips
            response["analysis"]["platform_tips"] = _get_platform_specific_tips(
                item.platform or "youtube"
            )
            
            # Raw VDG data with Korean translation for Storyboard UI
            response["raw_vdg"] = _translate_vdg_to_korean(analysis)
    
    return response


# ==================
# KOREAN TRANSLATION LAYER
# ==================

VDG_KOREAN_MAP = {
    # Camera shots
    "LS": "롱샷 (LS)", "MS": "미디엄샷 (MS)", "CU": "클로즈업 (CU)", 
    "ECU": "익스트림 CU", "WS": "와이드샷 (WS)", "MCU": "미디엄 CU",
    "OTS": "오버더숄더", "POV": "1인칭 시점", "FS": "풀샷 (FS)",
    "2-Shot": "투샷", "3-Shot": "쓰리샷", "Group Shot": "그룹샷",
    # Camera moves  
    "zoom_in": "줌인", "zoom_out": "줌아웃", "pan": "패닝", "tilt": "틸트",
    "dolly": "돌리", "track": "트래킹", "static": "고정샷", "handheld": "핸드헬드",
    "track_back": "트래킹백", "shake_effect": "흔들림 효과", "follow": "팔로우샷",
    # Camera angles
    "eye": "아이레벨", "low": "로우앵글", "high": "하이앵글", "dutch": "더치앵글",
    # Narrative roles
    "Action": "액션", "Reaction": "리액션", "Hook": "훅", "Setup": "셋업",
    "Payoff": "페이오프", "Conflict": "갈등", "Resolution": "해결",
    "Main Event": "메인 이벤트", "Full Sketch": "풀 스케치", "Hook & Setup": "훅 & 셋업",
    "Climax": "클라이맥스", "Outro": "아웃트로", "Transition": "전환",
    # Hook patterns
    "pattern_break": "패턴 브레이크", "question": "질문", "reveal": "공개/리빌",
    "transformation": "변신", "unboxing": "언박싱", "challenge": "챌린지",
    # Edit pace
    "real_time": "실시간", "fast": "빠른 편집", "slow": "슬로우", "jump_cut": "점프컷",
    "medium": "보통 속도",
    # Audio events
    "impact_sound": "충격음", "crowd_laughter": "관객 웃음", "speech": "대사",
    "music": "음악", "ambient": "환경음", "sfx": "효과음", "silence": "무음",
    "Laughter": "웃음", "Dialogue": "대화", "Buzzer": "버저음", "Applause": "박수",
    "Voiceover": "내레이션", "Sound Effect": "효과음", "Background Music": "배경 음악",
    # Visual style / Lighting
    "Stage Lighting": "무대 조명", "Natural": "자연광", "Dramatic": "드라마틱 조명",
    "Soft": "소프트 조명", "High Key": "하이키 조명", "Low Key": "로우키 조명",
    "High Key Studio": "스튜디오 조명", "Warm/Indoor": "따뜻한 실내광",
    "Outdoor": "야외광", "Neon": "네온 조명", "Cinematic": "시네마틱",
}

def _translate_term(term: str) -> str:
    """Translate a single English term to Korean"""
    if not term:
        return term
    return VDG_KOREAN_MAP.get(term, term)

def _translate_vdg_to_korean(analysis: dict) -> dict:
    """
    Translate VDG analysis to Korean for Storyboard UI.
    Returns structured scene data with Korean labels.
    """
    result = {
        "title": analysis.get("title", ""),
        "title_ko": analysis.get("title", ""),  # TODO: Translate via API
        "total_duration": 0,
        "scene_count": 0,
        "scenes": [],
    }
    
    scenes = analysis.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []
    scenes = [scene for scene in scenes if isinstance(scene, dict)]
    result["scene_count"] = len(scenes)
    
    for i, scene in enumerate(scenes):
        narrative = scene.get("narrative_unit") or {}
        setting = scene.get("setting") or {}
        visual_style = setting.get("visual_style") or {}
        audio_style = setting.get("audio_style") or {}
        shots = scene.get("shots") or []
        
        # Calculate timing
        time_start = scene.get("time_start")
        time_end = scene.get("time_end")
        try:
            time_start = float(time_start) if time_start is not None else 0.0
        except (TypeError, ValueError):
            time_start = 0.0
        try:
            time_end = float(time_end) if time_end is not None else 0.0
        except (TypeError, ValueError):
            time_end = 0.0

        raw_duration = scene.get("duration_sec")
        try:
            duration = float(raw_duration) if raw_duration is not None else (time_end - time_start)
        except (TypeError, ValueError):
            duration = time_end - time_start
        result["total_duration"] += duration
        
        # Extract camera info from first shot
        camera_info = {}
        if shots:
            cam = shots[0].get("camera", {})
            camera_info = {
                "shot": _translate_term(cam.get("shot", "")),
                "shot_en": cam.get("shot", ""),
                "move": _translate_term(cam.get("move", "")),
                "move_en": cam.get("move", ""),
                "angle": _translate_term(cam.get("angle", "")),
                "angle_en": cam.get("angle", ""),
            }
        
        # Extract audio events
        audio_events = audio_style.get("audio_events") or []
        audio_descriptions = [
            {
                "label": _translate_term(e.get("description", "")),
                "label_en": e.get("description", ""),
                "intensity": e.get("intensity", "medium"),
            }
            for e in audio_events
            if isinstance(e, dict) and e.get("description")
        ]
        
        scene_data = {
            "scene_id": scene.get("scene_id", f"S{i+1:02d}"),
            "scene_number": i + 1,
            # Timing
            "time_start": time_start,
            "time_end": time_end,
            "duration_sec": duration,
            "time_label": f"{int(time_start//60)}:{int(time_start%60):02d} - {int(time_end//60)}:{int(time_end%60):02d}",
            # Narrative
            "role": _translate_term(narrative.get("role", "")),
            "role_en": narrative.get("role", ""),
            "summary": narrative.get("summary", ""),
            "summary_ko": narrative.get("summary", ""),  # TODO: Translate via API
            "dialogue": narrative.get("dialogue", ""),
            "comedic_device": narrative.get("comedic_device", []),
            # Camera
            "camera": camera_info,
            # Setting
            "location": setting.get("location", ""),
            "lighting": _translate_term(visual_style.get("lighting", "")),
            "lighting_en": visual_style.get("lighting", ""),
            "edit_pace": _translate_term(visual_style.get("edit_pace", "")),
            "edit_pace_en": visual_style.get("edit_pace", ""),
            # Audio
            "audio_events": audio_descriptions,
            "music": audio_style.get("music", ""),
            "ambient": audio_style.get("ambient_sound", ""),
        }
        result["scenes"].append(scene_data)
    
    return result


# ==================
# VDG ANALYSIS EXTRACTION HELPERS
# ==================
def _extract_hook_pattern(analysis: dict) -> Optional[str]:
    """Extract hook pattern from gemini_analysis (VDG v3 schema)"""
    # 1. Direct hook_genome field
    hook_genome = analysis.get("hook_genome")
    if isinstance(hook_genome, dict):
        return hook_genome.get("pattern")
    
    # 2. VDG v3: scenes[0].narrative_unit.role (e.g., "Action", "Hook", "Setup")
    if "scenes" in analysis and len(analysis["scenes"]) > 0:
        first_scene = analysis["scenes"][0]
        narrative = first_scene.get("narrative_unit", {})
        if narrative.get("role"):
            return narrative["role"].lower().replace(" ", "_")
        # Fallback to shots[0].camera.move
        shots = first_scene.get("shots", [])
        if shots and shots[0].get("camera", {}).get("move"):
            return shots[0]["camera"]["move"]
    
    # 3. Legacy pattern field
    return analysis.get("pattern")

def _extract_hook_score(analysis: dict) -> Optional[float]:
    """Extract hook strength score"""
    hook_genome = analysis.get("hook_genome")
    if isinstance(hook_genome, dict):
        return hook_genome.get("strength")
    if "metrics" in analysis:
        metrics = analysis["metrics"]
        score = metrics.get("hook_strength")
        if score is None:
            score = metrics.get("predicted_retention_score")
        if score is not None:
            return score
    # VDG v3: Use shots[0].confidence as proxy
    if "scenes" in analysis and len(analysis["scenes"]) > 0:
        shots = analysis["scenes"][0].get("shots", [])
        if shots:
            conf = shots[0].get("confidence")
            if conf == "high":
                return 0.9
            elif conf == "medium":
                return 0.7
            elif conf == "low":
                return 0.5
    return None

def _extract_hook_duration(analysis: dict) -> Optional[float]:
    """Extract hook duration (first scene end time)"""
    hook_genome = analysis.get("hook_genome")
    if isinstance(hook_genome, dict):
        return hook_genome.get("duration_sec")
    # VDG v3: scenes[0].duration_sec or time_end
    if "scenes" in analysis and len(analysis["scenes"]) > 0:
        first_scene = analysis["scenes"][0]
        if "duration_sec" in first_scene:
            try:
                return float(first_scene["duration_sec"])
            except (TypeError, ValueError):
                pass
        if "time_end" in first_scene:
            try:
                return float(first_scene["time_end"])
            except (TypeError, ValueError):
                pass
        # Legacy: end_time
        if "end_time" in first_scene:
            try:
                return float(first_scene["end_time"])
            except (TypeError, ValueError):
                pass
    return None

def _extract_visual_patterns(analysis: dict) -> Optional[List[str]]:
    """Extract visual patterns from VDG scenes with Korean translation"""
    patterns = []
    if "scenes" in analysis:
        for scene in analysis["scenes"][:3]:
            # VDG v3: shots[].camera.shot (LS, MS, CU etc.)
            shots = scene.get("shots", [])
            for shot in shots[:2]:
                camera = shot.get("camera", {})
                if camera.get("shot"):
                    patterns.append(_translate_term(camera["shot"]))
                if camera.get("move"):
                    patterns.append(_translate_term(camera["move"]))
                if camera.get("angle") and camera["angle"] != "eye":
                    patterns.append(_translate_term(camera["angle"]))
            # VDG v3: setting.visual_style
            setting = scene.get("setting", {})
            visual_style = setting.get("visual_style", {})
            if visual_style.get("lighting"):
                patterns.append(_translate_term(visual_style["lighting"]))
            if visual_style.get("edit_pace"):
                patterns.append(_translate_term(visual_style["edit_pace"]))
            # Legacy: visual_elements
            if "visual_elements" in scene:
                patterns.extend([_translate_term(v) for v in scene["visual_elements"][:2]])
    return list(dict.fromkeys(patterns))[:6] if patterns else None  # Dedupe

def _extract_audio_pattern(analysis: dict) -> Optional[str]:
    """Extract audio pattern from VDG with Korean translation"""
    # Direct audio field
    audio = analysis.get("audio")
    if isinstance(audio, dict):
        pattern = audio.get("type") or audio.get("style")
        return _translate_term(pattern) if pattern else None
    if isinstance(audio, str):
        return _translate_term(audio) if audio else None
    # VDG v3: scenes[].setting.audio_style
    if "scenes" in analysis:
        for scene in analysis["scenes"]:
            setting = scene.get("setting", {})
            audio_style = setting.get("audio_style", {})
            if audio_style.get("music"):
                return _translate_term(audio_style["music"])
            if audio_style.get("tone"):
                return _translate_term(audio_style["tone"])
            # Check audio_events
            events = audio_style.get("audio_events", [])
            if events:
                descriptions = [
                    _translate_term(e.get("description"))
                    for e in events
                    if isinstance(e, dict) and e.get("description")
                ]
                if descriptions:
                    return ", ".join(descriptions[:2])
            # Legacy
            if "audio" in scene:
                return _translate_term(scene["audio"])
    return None

def _extract_shotlist(analysis: dict) -> Optional[List[str]]:
    """Extract shotlist with actual scene descriptions from VDG"""
    if "scenes" in analysis:
        shotlist = []
        for i, scene in enumerate(analysis["scenes"]):
            # VDG v3: narrative_unit.summary is the best description
            narrative = scene.get("narrative_unit", {})
            summary = narrative.get("summary")
            
            if summary:
                # Add timing if available
                duration = scene.get("duration_sec")
                if duration:
                    shotlist.append(f"{summary} ({duration}s)")
                else:
                    shotlist.append(summary)
            elif narrative.get("dialogue"):
                # Use dialogue if no summary
                shotlist.append(f"[대사] {narrative['dialogue'][:50]}")
            else:
                # Fallback to scene description or ID
                desc = scene.get("description") or f"Scene {scene.get('scene_id', i+1)}"
                shotlist.append(desc)
        return shotlist if shotlist else None
    # Legacy shotlist field
    if "shotlist" in analysis:
        return analysis["shotlist"]
    return None

def _extract_timing(analysis: dict) -> Optional[List[str]]:
    """Extract timing info from VDG scenes"""
    if "scenes" in analysis:
        timings = []

        def _safe_float(value, fallback: float = 0.0) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return fallback

        for scene in analysis["scenes"]:
            # VDG v3: time_start, time_end, duration_sec
            if "duration_sec" in scene:
                timings.append(f"{scene['duration_sec']}s")
            elif "time_start" in scene and "time_end" in scene:
                start = _safe_float(scene.get("time_start"))
                end = _safe_float(scene.get("time_end"), start)
                duration = end - start
                timings.append(f"{duration:.1f}s")
            else:
                # Legacy: start_time, end_time
                start = _safe_float(scene.get("start_time"))
                end = _safe_float(scene.get("end_time"), start + 2)
                duration = end - start
                timings.append(f"{duration:.1f}s")
        return timings
    return None

def _extract_do_not(analysis: dict) -> Optional[List[str]]:
    """Extract things to avoid"""
    if "warnings" in analysis:
        return analysis["warnings"]
    if "do_not" in analysis:
        return analysis["do_not"]
    # Generate from audio_events if intensity is high
    do_not = []
    if "scenes" in analysis:
        for scene in analysis["scenes"]:
            audio_events = scene.get("setting", {}).get("audio_style", {}).get("audio_events", [])
            for event in audio_events:
                if isinstance(event, dict) and event.get("intensity") == "high":
                    do_not.append(f"과도한 {event.get('description', '효과')} 사용 주의")
    return do_not if do_not else None

def _extract_invariant(analysis: dict) -> Optional[List[str]]:
    """Extract must-keep elements (불변 요소) from VDG analysis - Korean"""
    invariant = []
    
    # Hook pattern translation map
    hook_ko_map = {
        "pattern_break": "패턴 브레이크",
        "visual_reaction": "시각적 리액션",
        "unboxing": "언박싱",
        "transformation": "변신/트랜스폼",
        "reveal": "공개/리빌",
        "action": "액션",
        "setup": "셋업",
        "question": "질문 유도",
        "challenge": "챌린지",
        "comparison": "비교",
        "countdown": "카운트다운",
    }
    
    # 1. Hook pattern is always invariant
    hook_pattern = _extract_hook_pattern(analysis)
    if hook_pattern:
        hook_ko = hook_ko_map.get(hook_pattern.lower(), hook_pattern)
        invariant.append(f"🎣 훅: {hook_ko}")
    
    # 2. Hook duration
    hook_dur = _extract_hook_duration(analysis)
    if hook_dur:
        invariant.append(f"⏱️ 처음 {hook_dur}초 안에 훅 완성")
    
    # 3. First scene's key elements from VDG v3
    if "scenes" in analysis and len(analysis["scenes"]) > 0:
        first = analysis["scenes"][0]
        narrative = first.get("narrative_unit", {})
        
        # Opening action/setup - use Korean role
        role = narrative.get("role", "")
        role_ko = _translate_term(role)
        if role_ko and narrative.get("summary"):
            invariant.append(f"🎬 오프닝 ({role_ko}): 이 구성 유지")
        
        # Camera style - translate
        shots = first.get("shots", [])
        if shots and shots[0].get("camera", {}).get("shot"):
            cam = shots[0]["camera"]
            shot_ko = _translate_term(cam.get("shot", ""))
            move_ko = _translate_term(cam.get("move", ""))
            cam_desc = f"{shot_ko} {move_ko}".strip()
            if cam_desc:
                invariant.append(f"📷 카메라워크: {cam_desc}")
    
    # 4. Pacing from metrics
    if "metrics" in analysis:
        metrics = analysis["metrics"]
        if metrics.get("pacing"):
            invariant.append(f"🎵 편집 리듬: {_translate_term(metrics['pacing'])}")
    
    return invariant if invariant else None


# ==================
# DIRECTOR PACK BASED SHOOTING GUIDE (L2 Integration)
# ==================

def _extract_shooting_guide_from_director_pack(director_pack: dict) -> dict:
    """
    DirectorPack → 촬영 가이드 추출 (L2 Integration)
    
    VDG v4.0 DirectorPack의 DNAInvariant, MutationSlot, ForbiddenMutation을
    카드 상세의 가이드로 변환
    
    Returns:
        {
            "invariant": [...],  # 필수 요소 (DNAInvariant)
            "variable": [...],    # 변주 가능 (MutationSlot)
            "do_not": [...],      # 금지 사항 (ForbiddenMutation)
            "checkpoints": [...]  # 시간별 체크포인트
        }
    """
    guide = {
        "invariant": [],
        "variable": [],
        "do_not": [],
        "checkpoints": [],
    }
    
    # Priority emoji map
    priority_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "⚪",
    }
    
    # Domain emoji map
    domain_emoji = {
        "hook": "🎣",
        "timing": "⏱️",
        "composition": "📷",
        "pacing": "🎵",
        "audio": "🎤",
    }
    
    # 1. DNAInvariant → 필수 요소
    dna_invariants = director_pack.get("dna_invariants", [])
    for rule in dna_invariants[:5]:  # Top 5
        emoji = priority_emoji.get(rule.get("priority", "medium"), "")
        domain = rule.get("domain", "")
        domain_ico = domain_emoji.get(domain, "📌")
        
        # Use coach_line (friendly tone) or check_hint
        templates = rule.get("coach_line_templates", {})
        text = (
            templates.get("friendly") or 
            templates.get("neutral") or 
            rule.get("check_hint") or
            rule.get("description", "")
        )
        
        if text:
            guide["invariant"].append(f"{emoji}{domain_ico} {text}")
    
    # 2. MutationSlot → 변주 가능 요소
    mutation_slots = director_pack.get("mutation_slots", [])
    for slot in mutation_slots[:3]:
        slot_type = slot.get("slot_type", "")
        slot_guide = slot.get("guide", "")
        options = slot.get("options", [])
        
        if slot_guide:
            options_str = ", ".join(options[:3]) if options else "자유롭게"
            guide["variable"].append(f"🎨 {slot_type}: {slot_guide} ({options_str})")
    
    # 3. ForbiddenMutation → 금지 사항
    forbidden = director_pack.get("forbidden_mutations", [])
    for fm in forbidden[:3]:
        reason = fm.get("reason", "")
        if reason:
            guide["do_not"].append(f"❌ {reason}")
    
    # 4. Checkpoints → 시간별 가이드
    checkpoints = director_pack.get("checkpoints", [])
    for cp in checkpoints[:5]:
        t_window = cp.get("t_window", [0, 0])
        note = cp.get("note", "")
        if note and cp.get("checkpoint_id") != "overall":
            guide["checkpoints"].append(f"⏰ {t_window[0]:.0f}-{t_window[1]:.0f}초: {note}")
    
    return guide


def _get_platform_specific_tips(platform: str) -> List[str]:
    """
    플랫폼별 추가 팁 (Shorts vs TikTok 차이)
    """
    tips = {
        "youtube": [
            "🎬 쇼츠: 첫 1초가 생명, Thumbnail = 첫 프레임",
            "📱 세로 9:16 필수, 60초 이내",
        ],
        "tiktok": [
            "🎵 틱톡: 트렌딩 사운드 활용이 핵심",
            "🔄 듀엣/스티치 가능한 포맷 고려",
            "📱 세로 9:16, 15/30/60초 권장",
        ],
        "instagram": [
            "📸 릴스: 첫 3초 안에 주제 명확히",
            "🏷️ 해시태그 활용 중요",
        ],
    }
    return tips.get(platform.lower(), [])


def _extract_variable(analysis: dict) -> Optional[List[str]]:
    """Extract creative variation elements (가변 요소) - Korean"""
    variable = []
    
    # From commerce tag
    if "commerce" in analysis:
        variable.append("🛒 소재: 제품/서비스 변경 가능")
    
    # Multiple scenes = middle scenes can vary
    if "scenes" in analysis and len(analysis["scenes"]) > 1:
        variable.append("🎞️ 중간 씬: 자유롭게 변주 가능")
        
        # Check if there are different scene roles - translate to Korean
        roles = set()
        for scene in analysis["scenes"]:
            role = scene.get("narrative_unit", {}).get("role")
            if role:
                roles.add(_translate_term(role))  # Translate to Korean
        if len(roles) > 1:
            roles_str = " → ".join(list(roles)[:3])
            variable.append(f"📝 구성: {roles_str} 순서 유지 권장")
    
    # Default suggestions if empty
    if len(variable) == 0:
        variable = [
            "🎨 소재: 자유롭게 변경 가능",
            "👤 인물: 성별/연령 변경 가능",
            "📍 배경: 장소/환경 변경 가능",
        ]
    
    return variable


@router.get("/candidates", response_model=OutlierCandidatesResponse)
async def list_candidates(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = Query(default="pending"),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """후보 아웃라이어 목록 조회 (선별 대상)"""
    query = select(OutlierItem).order_by(OutlierItem.view_count.desc())
    
    if category:
        query = query.where(OutlierItem.category == category)
    if platform:
        query = query.where(OutlierItem.platform == platform)
    if status:
        try:
            status_enum = OutlierItemStatus(status)
            query = query.where(OutlierItem.status == status_enum)
        except ValueError:
            pass
    
    query = query.limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return OutlierCandidatesResponse(
        total=len(items),
        candidates=[_item_to_response(i) for i in items],
    )


@router.patch("/items/{item_id}/status")
async def update_item_status(
    item_id: str,
    new_status: str,
    db: AsyncSession = Depends(get_db)
):
    """후보 상태 변경 (selected, rejected, promoted)"""
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == UUID(item_id))
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Outlier item not found")
    
    status_enum = getattr(OutlierItemStatus, new_status.upper(), None)
    if not status_enum:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    item.status = status_enum
    
    await db.commit()
    return {"updated": True, "new_status": new_status}


@router.post("/items/{item_id}/promote")
async def promote_to_parent(
    item_id: str,
    background_tasks: BackgroundTasks,
    request: OutlierPromoteRequest = None,  # Optional Request Body
    current_user: Optional[User] = Depends(get_current_user_optional),  # 인증 선택사항
    db: AsyncSession = Depends(get_db)
):
    """
    아웃라이어를 Parent RemixNode로 승격
    자동으로 Gemini 분석 실행
    """
    # 비로그인 사용자를 위한 데모 유저 처리
    if not current_user:
        # 데모/게스트 유저 생성 또는 조회
        demo_email = "demo@komission.ai"
        result = await db.execute(select(User).where(User.email == demo_email))
        current_user = result.scalar_one_or_none()
        if not current_user:
            from app.models import User as UserModel
            current_user = UserModel(
                email=demo_email,
                firebase_uid="demo_guest",
                name="Demo User",
                role="user",
                is_active=True,
            )
            db.add(current_user)
            await db.flush()
    
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == UUID(item_id))
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Outlier item not found")
    
    if item.status == OutlierItemStatus.PROMOTED:
        raise HTTPException(status_code=400, detail="Already promoted")

    node_id = await generate_remix_node_id(db)
    node = RemixNode(
        node_id=node_id,
        title=item.title or "Untitled Outlier",
        source_video_url=item.video_url,
        platform=item.platform,
        layer=NodeLayer.MASTER,
        permission=NodePermission.READ_ONLY,
        governed_by=NodeGovernance.OPEN_COMMUNITY,
        view_count=item.view_count or 0,
        created_by=current_user.id,
        owner_type=current_user.role,
    )
    db.add(node)
    await db.flush()

    item.status = OutlierItemStatus.PROMOTED
    item.promoted_to_node_id = node.id
    if request and request.campaign_eligible:
        item.campaign_eligible = True
    
    # 큐레이션 결정 기록 (학습용)
    from app.services.curation_service import record_curation_decision
    from app.models import CurationDecisionType
    
    decision_type = (
        CurationDecisionType.CAMPAIGN if (request and request.campaign_eligible)
        else CurationDecisionType.NORMAL
    )

    matched_rule_id = getattr(request, "matched_rule_id", None) if request else None
    rule_followed = getattr(request, "rule_followed", None) if request else None
    if matched_rule_id and rule_followed is None:
        raise HTTPException(
            status_code=400,
            detail="rule_followed is required when matched_rule_id is set",
        )
    if rule_followed is not None and not matched_rule_id:
        raise HTTPException(
            status_code=400,
            detail="matched_rule_id is required when rule_followed is set",
        )
    
    await record_curation_decision(
        db,
        outlier_item_id=item.id,
        remix_node_id=node.id,
        curator_id=current_user.id,
        decision_type=decision_type,
        curator_notes=getattr(request, "notes", None) if request else None,
        matched_rule_id=matched_rule_id,
        rule_followed=rule_followed,
    )
    
    # VDG 분석 자동 실행 (승격 즉시)
    item.analysis_status = "analyzing"
    await db.commit()
    await db.refresh(node)

    # ✅ Auto-analysis ENABLED - VDG 분석 즉시 시작
    if item.video_url:
        background_tasks.add_task(
            _run_vdg_analysis_with_comments,
            item_id=str(item.id),
            node_id=node.node_id,
            video_url=item.video_url,
            platform=item.platform,
        )

    return {
        "promoted": True,
        "item_id": item_id,
        "node_id": node.node_id,
        "remix_id": str(node.id),
        "analysis_status": "analyzing",  # 즉시 분석 시작
        "decision_type": decision_type.value,
        "message": "VDG 분석이 자동으로 시작됩니다.",
    }


@router.post("/items/{item_id}/reject")
async def reject_outlier_item(
    item_id: str,
    request: OutlierRejectRequest = None,
    current_user: User = Depends(require_curator),
    db: AsyncSession = Depends(get_db),
):
    """
    아웃라이어 아이템 거부 및 결정 기록
    """
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == UUID(item_id))
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Outlier item not found")

    if item.status == OutlierItemStatus.PROMOTED:
        raise HTTPException(status_code=400, detail="Already promoted")

    if item.status == OutlierItemStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Already rejected")

    matched_rule_id = getattr(request, "matched_rule_id", None) if request else None
    rule_followed = getattr(request, "rule_followed", None) if request else None
    if matched_rule_id and rule_followed is None:
        raise HTTPException(
            status_code=400,
            detail="rule_followed is required when matched_rule_id is set",
        )
    if rule_followed is not None and not matched_rule_id:
        raise HTTPException(
            status_code=400,
            detail="matched_rule_id is required when rule_followed is set",
        )

    item.status = OutlierItemStatus.REJECTED

    from app.services.curation_service import record_curation_decision
    from app.models import CurationDecisionType

    await record_curation_decision(
        db,
        outlier_item_id=item.id,
        remix_node_id=None,
        curator_id=current_user.id,
        decision_type=CurationDecisionType.REJECTED,
        curator_notes=getattr(request, "notes", None) if request else None,
        matched_rule_id=matched_rule_id,
        rule_followed=rule_followed,
    )

    await db.commit()

    return {
        "rejected": True,
        "item_id": item_id,
        "decision_type": CurationDecisionType.REJECTED.value,
    }


def _item_to_response(item: OutlierItem) -> OutlierItemResponse:
    return OutlierItemResponse(
        id=str(item.id),
        source_id=str(item.source_id),
        external_id=item.external_id,
        video_url=item.video_url,
        title=item.title,
        thumbnail_url=item.thumbnail_url,
        platform=item.platform,
        category=item.category,
        view_count=item.view_count,
        like_count=item.like_count,
        growth_rate=item.growth_rate,
        status=item.status.value.lower() if item.status else "pending",
        promoted_to_node_id=str(item.promoted_to_node_id) if item.promoted_to_node_id else None,
        campaign_eligible=item.campaign_eligible,
        crawled_at=item.crawled_at,
    )


# ==================
# CSV BULK UPLOAD (FR-001)
# ==================

FIELD_ALIASES = {
    "source_url": ["source_url", "url", "link", "video_url", "post_url"],
    "title": ["title", "caption", "name", "headline"],
    "platform": ["platform", "platform_name"],
    "category": ["category", "vertical", "genre"],
    "views": ["views", "view_count", "plays"],
    "growth_rate": ["growth_rate", "growth", "velocity"],
}


def _resolve_field(row: dict, key: str) -> str:
    """Flexible field resolution with aliases"""
    for alias in FIELD_ALIASES.get(key, [key]):
        if alias in row and row[alias]:
            return str(row[alias]).strip()
    return ""


def _infer_platform(url: str) -> str:
    """Infer platform from URL"""
    lowered = (url or "").lower()
    if "tiktok" in lowered:
        return "tiktok"
    if "instagram" in lowered:
        return "instagram"
    if "youtu" in lowered:
        return "youtube"
    return "unknown"


def _parse_number(value: str) -> Optional[int]:
    """Parse number from string"""
    if not value:
        return None
    text = value.strip().replace(",", "")
    try:
        return int(float(text))
    except ValueError:
        return None


@router.post("/items/bulk-csv")
async def bulk_upload_csv(
    file: UploadFile = File(...),
    source_name: str = Form(default="csv_upload"),
    default_category: str = Form(default="unknown"),
    default_platform: Optional[str] = Form(default=None),
    current_user: User = Depends(require_curator),
    db: AsyncSession = Depends(get_db)
):
    """
    CSV 파일에서 아웃라이어 일괄 등록 (FR-001)
    
    CSV 필수 컬럼: source_url (또는 url, video_url), title (또는 caption)
    선택 컬럼: platform, category, views, growth_rate
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    content = await file.read()
    text = content.decode('utf-8')
    
    # Get or create source
    source = await _get_or_create_source(db, source_name)
    
    reader = csv.DictReader(io.StringIO(text))
    inserted = 0
    skipped = 0
    
    for raw_row in reader:
        # Normalize keys to lowercase
        row = {k.strip().lower(): v for k, v in raw_row.items()}
        
        source_url = _resolve_field(row, "source_url")
        title = _resolve_field(row, "title")
        
        if not source_url or not title:
            skipped += 1
            continue
        
        # Generate external_id from URL hash
        external_id = f"{source_name}_{hashlib.sha256(source_url.encode()).hexdigest()[:12]}"
        
        # Check for duplicates by video_url (more robust than external_id)
        existing = await db.execute(
            select(OutlierItem).where(OutlierItem.video_url == source_url)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        
        platform = _resolve_field(row, "platform") or default_platform or _infer_platform(source_url)
        category = _resolve_field(row, "category") or default_category
        views = _parse_number(_resolve_field(row, "views")) or 0
        growth_rate = _resolve_field(row, "growth_rate") or None
        
        item = OutlierItem(
            source_id=source.id,
            external_id=external_id,
            video_url=source_url,
            title=title,
            platform=platform,
            category=category,
            view_count=views,
            growth_rate=growth_rate,
            status=OutlierItemStatus.PENDING,
        )
        db.add(item)
        inserted += 1
    
    await db.commit()
    
    return {
        "status": "success",
        "inserted": inserted,
        "skipped": skipped,
        "source_name": source_name,
    }


# ==================
# ADMIN VDG ANALYSIS APPROVAL
# ==================

@router.post("/items/{item_id}/approve")
async def approve_vdg_analysis(
    item_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_curator),  # Admin/Curator only
    db: AsyncSession = Depends(get_db)
):
    """
    [Admin Only] VDG 분석 승인 및 실행
    
    1. 베스트 댓글 추출 (YouTube/TikTok API)
    2. Gemini VDG 분석 실행 (댓글 컨텍스트 포함)
    3. 결과 저장
    
    비용이 발생하는 Gemini API 호출을 Admin 승인 후에만 실행함.
    """
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == UUID(item_id))
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Outlier item not found")
    
    if item.status != OutlierItemStatus.PROMOTED:
        raise HTTPException(
            status_code=400, 
            detail="Item must be promoted first before VDG analysis"
        )
    
    if item.analysis_status == "completed":
        raise HTTPException(status_code=400, detail="Analysis already completed")
    
    if item.analysis_status == "analyzing":
        raise HTTPException(status_code=400, detail="Analysis already in progress")
    
    # Update approval status
    item.analysis_status = "approved"
    item.approved_by = current_user.id
    item.approved_at = utcnow()
    await db.commit()
    
    # Get promoted node
    if not item.promoted_to_node_id:
        raise HTTPException(status_code=400, detail="No promoted node found")
    
    node_result = await db.execute(
        select(RemixNode).where(RemixNode.id == item.promoted_to_node_id)
    )
    node = node_result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Promoted node not found")
    
    # Trigger analysis with best comments in background
    if item.video_url:
        background_tasks.add_task(
            _run_vdg_analysis_with_comments,
            item_id=str(item.id),
            node_id=node.node_id,
            video_url=item.video_url,
            platform=item.platform,
        )
    
    return {
        "approved": True,
        "item_id": item_id,
        "node_id": node.node_id,
        "analysis_status": "approved",
        "approved_by": str(current_user.id),
        "message": "VDG 분석이 시작됩니다. 베스트 댓글 추출 후 Gemini 분석이 실행됩니다.",
    }


async def _run_vdg_analysis_with_comments(
    item_id: str,
    node_id: str,
    video_url: str,
    platform: str
):
    """
    Background task: Best comments extraction + VDG analysis + Clustering + NotebookLibrary
    
    Pipeline:
    1. Extract best comments
    2. Run Gemini VDG analysis
    3. Save to RemixNode
    4. Assign cluster based on microbeat similarity
    5. Create NotebookLibraryEntry
    """
    from app.services.gemini_pipeline import gemini_pipeline
    from app.services.clustering import PatternClusteringService
    from app.database import async_session_maker
    from app.models import RemixNode, OutlierItem, NotebookLibraryEntry, PatternCluster
    
    try:
        async with async_session_maker() as db:
            # 1. Fetch item first
            item_result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == UUID(item_id))
            )
            item = item_result.scalar_one_or_none()
            
            # 2. Check if manual comments already exist - SKIP EXTRACTION
            best_comments = []
            existing_comments = item.best_comments if item else None

            def _normalize_comments(raw):
                if raw is None:
                    return None
                if isinstance(raw, list):
                    return raw
                if isinstance(raw, dict):
                    nested = raw.get("comments")
                    if isinstance(nested, list):
                        return nested
                if isinstance(raw, str):
                    import json as json_module
                    for _ in range(2):  # Handle double-encoded JSON
                        try:
                            raw = json_module.loads(raw)
                        except Exception:
                            return None
                        if isinstance(raw, list):
                            return raw
                        if isinstance(raw, dict):
                            nested = raw.get("comments")
                            if isinstance(nested, list):
                                return nested
                        if not isinstance(raw, str):
                            break
                return None

            normalized_comments = _normalize_comments(existing_comments)
            if normalized_comments and len(normalized_comments) > 0:
                best_comments = normalized_comments
                print(f"✅ Using existing manual comments: {len(best_comments)} for {node_id}")
                # Normalize stored value if needed
                if item and normalized_comments is not existing_comments:
                    item.best_comments = normalized_comments
                    item.comments_missing_reason = None
                    await db.commit()
                # Mark as analyzing now that we confirmed comments exist
                if item and item.analysis_status != "analyzing":
                    item.analysis_status = "analyzing"
                    await db.commit()
            else:
                # 3. Extract best comments (TikTok: TikTokUnifiedExtractor, Others: comment_extractor)
                try:
                    if platform.lower() == "tiktok":
                        # Use sophisticated TikTok extractor (UNIVERSAL_DATA JSON parsing)
                        from app.services.tiktok_extractor import extract_tiktok_complete
                        tiktok_data = await extract_tiktok_complete(video_url, include_comments=True)
                        best_comments = tiktok_data.get("top_comments", [])
                        print(f"📝 TikTok unified extractor: {len(best_comments)} comments, source={tiktok_data.get('source')}")
                    else:
                        # YouTube/Instagram: use comment_extractor
                        from app.services.comment_extractor import extract_best_comments
                        best_comments = await extract_best_comments(video_url, platform, limit=10)
                    
                    if not best_comments:
                        raise ValueError("No comments extracted - empty result")
                    
                    # Save best comments to OutlierItem and mark as analyzing
                    if item:
                        item.best_comments = best_comments
                        item.analysis_status = "analyzing"  # Set analyzing AFTER comments confirmed
                        await db.commit()
                    print(f"📝 Extracted {len(best_comments)} best comments for {node_id}")
                
                except Exception as e:
                    # TIER-BASED GATE: S/A tier → manual review, others → block
                    print(f"❌ Comment extraction failed: {e}")
                    
                    # Check if this is a high-value item (S/A tier)
                    is_high_value = False
                    if item:
                        is_high_value = (
                            item.outlier_tier in ['S', 'A'] or 
                            (item.outlier_score is not None and item.outlier_score >= 100)
                        )
                        item.comments_missing_reason = str(e)[:200]
                    
                    if is_high_value:
                        # S/A tier: Queue for manual review
                        print(f"⚠️ High-value item (S/A tier) - queued for manual comment review")
                        if item:
                            item.analysis_status = "comments_pending_review"
                            await db.commit()
                        raise HTTPException(
                            status_code=202,
                            detail=f"High-value item queued for manual comment review. Use PATCH /outliers/items/{item_id}/comments to add comments manually."
                        )
                    else:
                        # B/C tier or no tier: Block VDG
                        print(f"🚫 Low-value item - blocking VDG analysis")
                        if item:
                            item.analysis_status = "comments_failed"
                            await db.commit()
                        raise HTTPException(
                            status_code=503,
                            detail=f"Comment extraction required before VDG analysis: {e}"
                        )
            
            # 3. Run VDG analysis with comment context (only proceeds if comments exist)
            print(f"🚀 Starting VDG v4 analysis for {node_id} with {len(best_comments)} comments...")
            result = await gemini_pipeline.analyze_video_v4(
                video_url, 
                node_id,
                audience_comments=best_comments  # Pass comments to pipeline
            )
            vdg_snapshot = result.model_dump()
            
            # 4. Save analysis result to RemixNode
            node_result = await db.execute(
                select(RemixNode).where(RemixNode.node_id == node_id)
            )
            node = node_result.scalar_one_or_none()
            
            if node:
                node.gemini_analysis = vdg_snapshot

            # 4.0 Attach VDG snapshot/features to curation decision
            from app.services.curation_service import update_curation_decision_with_vdg

            if item:
                await update_curation_decision_with_vdg(
                    db,
                    outlier_item_id=item.id,
                    remix_node_id=node.id if node else None,
                    vdg_analysis=vdg_snapshot,
                )

            await db.commit()
            
            # 4.1 Save VDG quality score to OutlierItem
            try:
                from app.validators.vdg_quality_validator import validate_vdg_quality
                quality_result = validate_vdg_quality(vdg_snapshot)
                if item:
                    item.vdg_quality_score = quality_result.score
                    item.vdg_quality_valid = quality_result.is_valid
                    item.vdg_quality_issues = quality_result.issues[:5]
                    await db.commit()
                    print(f"📊 VDG quality: score={quality_result.score}, valid={quality_result.is_valid}")
            except Exception as e:
                print(f"⚠️ VDG quality validation failed (non-fatal): {e}")
            
            print(f"✅ VDG analysis complete for {node_id}")
            
            # 5. Cluster assignment based on microbeat sequence similarity
            try:
                clustering_service = PatternClusteringService(db)
                cluster_id, is_new = await clustering_service.get_or_create_cluster(
                    result.model_dump(),
                    similarity_threshold=0.75
                )
                print(f"📊 Assigned to cluster: {cluster_id} (new={is_new})")
                
                # 6. Create NotebookLibraryEntry
                category = item.category if item else "unknown"
                temporal_phase = None
                variant_age_days = None
                novelty_decay_score = None
                burstiness_index = None
                reference_time = item.crawled_at if item and item.crawled_at else utcnow()
                if cluster_id:
                    first_seen_result = await db.execute(
                        select(func.min(NotebookLibraryEntry.created_at))
                        .where(NotebookLibraryEntry.cluster_id == cluster_id)
                    )
                    first_seen = first_seen_result.scalar_one_or_none()
                    if first_seen:
                        age_days = max(0, (reference_time - first_seen).days)
                    else:
                        age_days = 0
                else:
                    age_days = 0
                temporal_phase = _temporal_phase_for_age(age_days)
                variant_age_days = age_days
                novelty_decay_score = round(max(0.2, math.exp(-age_days / 21)), 4)
                burstiness_index = _calculate_burstiness(item)

                # 6.1 Merge OutlierItem real metrics into VDG (v3.3)
                vdg_data = result.model_dump()
                if item:
                    vdg_data["metrics"] = {
                        "view_count": item.view_count or 0,
                        "like_count": item.like_count or 0,
                        "comment_count": len(item.best_comments or []),
                        "share_count": item.share_count,
                        "hashtags": [],  # Could be extracted from crawler
                        "outlier_tier": item.outlier_tier,
                        "outlier_score": item.outlier_score,
                        "creator_avg_views": item.creator_avg_views,
                    }
                    vdg_data["upload_date"] = (
                        item.upload_date.isoformat() if item.upload_date 
                        else (item.crawled_at.isoformat() if item.crawled_at else None)
                    )

                library_entry = NotebookLibraryEntry(
                    source_url=video_url,
                    platform=platform,
                    category=category,
                    summary={
                        "title": result.title if hasattr(result, 'title') else node_id,
                        "hook_pattern": result.hook_genome.pattern if hasattr(result, 'hook_genome') else "",
                        "platform": platform,
                        "view_count": item.view_count if item else 0,
                        "outlier_tier": item.outlier_tier if item else None,
                    },
                    cluster_id=cluster_id,
                    parent_node_id=node.id if node else None,
                    analysis_schema=vdg_data,  # Now includes real metrics
                    schema_version="v3.3",
                    temporal_phase=temporal_phase,
                    variant_age_days=variant_age_days,
                    novelty_decay_score=novelty_decay_score,
                    burstiness_index=burstiness_index,
                )
                db.add(library_entry)
                await db.commit()
                print(f"📚 Created NotebookLibraryEntry for cluster {cluster_id}")
                
                # 6.1 Create initial EvidenceSnapshot (kickstart evidence loop)
                from app.models import EvidenceSnapshot
                
                if node:
                    # Extract key patterns for depth1_summary
                    hook_pattern = result.hook_genome.pattern if hasattr(result, 'hook_genome') else "unknown"
                    depth1_summary = {
                        "hook": {
                            hook_pattern: {
                                "success_rate": 0.5,  # Initial baseline
                                "sample_count": 1,
                                "avg_delta": "baseline"
                            }
                        }
                    }
                    
                    evidence = EvidenceSnapshot(
                        parent_node_id=node.id,
                        snapshot_date=utcnow(),
                        period="baseline",
                        depth1_summary=depth1_summary,
                        top_mutation_type="hook",
                        top_mutation_pattern=hook_pattern,
                        sample_count=1,
                        confidence=0.5,
                    )
                    db.add(evidence)
                    await db.commit()
                    print(f"📊 Created initial EvidenceSnapshot for {node_id}")
                
            except Exception as e:
                print(f"⚠️ Clustering/Library entry failed (non-fatal): {e}")
            
            # 7. Update OutlierItem status to completed
            if item:
                item.analysis_status = "completed"
                await db.commit()
            
    except Exception as e:
        print(f"❌ VDG analysis failed for {node_id}: {e}")
        # Mark as failed
        try:
            async with async_session_maker() as db:
                item_result = await db.execute(
                    select(OutlierItem).where(OutlierItem.id == UUID(item_id))
                )
                item = item_result.scalar_one_or_none()
                if item:
                    # Preserve important statuses (don't overwrite manual review status)
                    if item.analysis_status not in ["comments_pending_review", "comments_failed"]:
                        item.analysis_status = "pending"  # Reset to pending for retry
                    await db.commit()
        except:
            pass


# ==================
# MANUAL COMMENT INPUT (Admin/Curator)
# ==================
from pydantic import BaseModel

class ManualCommentsInput(BaseModel):
    """Manual comment input for items pending review"""
    comments: List[dict]  # [{"text": "...", "likes": 100}, ...]
    
    class Config:
        json_schema_extra = {
            "example": {
                "comments": [
                    {"text": "This is amazing!", "likes": 1500},
                    {"text": "How did they do this?", "likes": 800},
                ]
            }
        }


@router.patch("/items/{item_id}/comments")
async def add_manual_comments(
    item_id: str,
    input: ManualCommentsInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_curator),
):
    """
    Add manual comments to an outlier item pending review.
    
    For S/A tier items where automatic comment extraction failed,
    curators can manually add comments to unblock VDG analysis.
    
    After adding comments, call POST /items/{item_id}/approve again
    to proceed with VDG analysis.
    """
    from uuid import UUID
    
    # Get item
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == UUID(item_id))
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.analysis_status not in ["comments_pending_review", "comments_failed", "pending"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Item is not pending comment review. Current status: {item.analysis_status}"
        )
    
    if not input.comments or len(input.comments) == 0:
        raise HTTPException(status_code=400, detail="At least one comment is required")
    
    # Save comments
    item.best_comments = input.comments
    item.analysis_status = "comments_ready"
    item.comments_missing_reason = None  # Clear the failure reason
    await db.commit()
    
    return {
        "success": True,
        "item_id": item_id,
        "comments_count": len(input.comments),
        "analysis_status": item.analysis_status,
        "message": "Comments added. You can now call POST /items/{item_id}/approve to run VDG analysis."
    }


@router.get("/items/pending-comments")
async def list_pending_comment_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_curator),
    limit: int = Query(50, le=100),
):
    """
    List all items pending manual comment review.
    These are S/A tier items where comment extraction failed.
    """
    result = await db.execute(
        select(OutlierItem)
        .where(OutlierItem.analysis_status == "comments_pending_review")
        .order_by(OutlierItem.outlier_score.desc().nullslast())
        .limit(limit)
    )
    items = result.scalars().all()
    
    return {
        "count": len(items),
        "items": [
            {
                "id": str(item.id),
                "video_url": item.video_url,
                "title": item.title,
                "platform": item.platform,
                "outlier_tier": item.outlier_tier,
                "outlier_score": item.outlier_score,
                "comments_missing_reason": item.comments_missing_reason,
                "crawled_at": item.crawled_at.isoformat() if item.crawled_at else None,
            }
            for item in items
        ]
    }


# ==================
# P1-2: KICK CURATION API
# ==================

from app.models import ViralKick, ViralKickStatus, KeyframeEvidence, CommentEvidence


@router.get("/kicks")
async def list_kicks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_curator),
    status: Optional[str] = Query(None),
    proof_ready: Optional[bool] = Query(None),
    mechanism: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """
    List viral kicks with filters for curation.
    
    Filters:
    - status: pending | approved | rejected | needs_review
    - proof_ready: true | false
    - mechanism: partial match
    - min_confidence: 0.0 - 1.0
    
    Returns kicks sorted by confidence (desc)
    """
    query = select(ViralKick)
    
    if status:
        query = query.where(ViralKick.status == status)
    
    if proof_ready is not None:
        query = query.where(ViralKick.proof_ready == proof_ready)
    
    if mechanism:
        query = query.where(ViralKick.mechanism.ilike(f"%{mechanism}%"))
    
    if min_confidence > 0:
        query = query.where(ViralKick.confidence >= min_confidence)
    
    query = query.order_by(ViralKick.confidence.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    kicks = result.scalars().all()
    
    # Count total
    count_query = select(func.count(ViralKick.id))
    if status:
        count_query = count_query.where(ViralKick.status == status)
    if proof_ready is not None:
        count_query = count_query.where(ViralKick.proof_ready == proof_ready)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "kicks": [
            {
                "id": str(kick.id),
                "kick_id": kick.kick_id,
                "node_id": str(kick.node_id),
                "kick_index": kick.kick_index,
                "title": kick.title,
                "mechanism": kick.mechanism,
                "creator_instruction": kick.creator_instruction,
                "start_ms": kick.start_ms,
                "end_ms": kick.end_ms,
                "confidence": kick.confidence,
                "proof_ready": kick.proof_ready,
                "missing_reason": kick.missing_reason,
                "status": kick.status.value if hasattr(kick.status, 'value') else kick.status,
                "comment_evidence_count": len(kick.comment_evidence_ids or []),
                "frame_evidence_count": len(kick.frame_evidence_ids or []),
                "created_at": kick.created_at.isoformat() if kick.created_at else None,
            }
            for kick in kicks
        ]
    }


@router.get("/kicks/{kick_id}")
async def get_kick_detail(
    kick_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed kick information with evidences.
    """
    # First try by kick_id string
    result = await db.execute(
        select(ViralKick).where(ViralKick.kick_id == kick_id)
    )
    kick = result.scalar_one_or_none()
    
    if not kick:
        # Try by UUID
        try:
            kick_uuid = uuid.UUID(kick_id)
            result = await db.execute(
                select(ViralKick).where(ViralKick.id == kick_uuid)
            )
            kick = result.scalar_one_or_none()
        except ValueError:
            pass
    
    if not kick:
        raise HTTPException(404, "Kick not found")
    
    # Get keyframes
    kf_result = await db.execute(
        select(KeyframeEvidence).where(KeyframeEvidence.kick_id == kick.id)
    )
    keyframes = kf_result.scalars().all()
    
    return {
        "kick": {
            "id": str(kick.id),
            "kick_id": kick.kick_id,
            "node_id": str(kick.node_id),
            "kick_index": kick.kick_index,
            "title": kick.title,
            "mechanism": kick.mechanism,
            "creator_instruction": kick.creator_instruction,
            "start_ms": kick.start_ms,
            "end_ms": kick.end_ms,
            "peak_ms": kick.peak_ms,
            "confidence": kick.confidence,
            "proof_ready": kick.proof_ready,
            "missing_reason": kick.missing_reason,
            "status": kick.status.value if hasattr(kick.status, 'value') else kick.status,
            "comment_evidence_ids": kick.comment_evidence_ids,
            "frame_evidence_ids": kick.frame_evidence_ids,
            "evidence_comment_ranks": kick.evidence_comment_ranks,
            "reviewed_by": str(kick.reviewed_by) if kick.reviewed_by else None,
            "reviewed_at": kick.reviewed_at.isoformat() if kick.reviewed_at else None,
            "review_notes": kick.review_notes,
            "created_at": kick.created_at.isoformat() if kick.created_at else None,
        },
        "keyframes": [
            {
                "evidence_id": kf.evidence_id,
                "role": kf.role,
                "t_ms": kf.t_ms,
                "what_to_see": kf.what_to_see,
                "blur_score": kf.blur_score,
                "brightness": kf.brightness,
                "motion_proxy": kf.motion_proxy,
                "verified": kf.verified,
            }
            for kf in keyframes
        ]
    }


from pydantic import BaseModel


class KickReviewRequest(BaseModel):
    """Kick review request"""
    action: str  # "approve" | "reject" | "needs_review"
    notes: Optional[str] = None


@router.post("/kicks/{kick_id}/review")
async def review_kick(
    kick_id: str,
    request: KickReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_curator),
):
    """
    Review (approve/reject) a viral kick.
    
    Actions:
    - approve: Mark as approved for promotion
    - reject: Mark as rejected with notes
    - needs_review: Flag for further review
    """
    # Find kick
    result = await db.execute(
        select(ViralKick).where(ViralKick.kick_id == kick_id)
    )
    kick = result.scalar_one_or_none()
    
    if not kick:
        try:
            kick_uuid = uuid.UUID(kick_id)
            result = await db.execute(
                select(ViralKick).where(ViralKick.id == kick_uuid)
            )
            kick = result.scalar_one_or_none()
        except ValueError:
            pass
    
    if not kick:
        raise HTTPException(404, "Kick not found")
    
    # Update status
    action_to_status = {
        "approve": ViralKickStatus.APPROVED,
        "reject": ViralKickStatus.REJECTED,
        "needs_review": ViralKickStatus.NEEDS_REVIEW,
    }
    
    if request.action not in action_to_status:
        raise HTTPException(400, f"Invalid action: {request.action}")
    
    kick.status = action_to_status[request.action]
    kick.reviewed_by = current_user.id
    kick.reviewed_at = utcnow()
    kick.review_notes = request.notes
    
    await db.commit()
    await db.refresh(kick)
    
    return {
        "success": True,
        "kick_id": kick.kick_id,
        "new_status": kick.status.value if hasattr(kick.status, 'value') else kick.status,
        "reviewed_by": current_user.email,
    }


@router.get("/kicks/stats/summary")
async def get_kick_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_curator),
):
    """
    Get kick curation statistics.
    """
    from sqlalchemy import case
    
    stats_query = select(
        func.count(ViralKick.id).label("total"),
        func.count(case((ViralKick.status == ViralKickStatus.PENDING, 1))).label("pending"),
        func.count(case((ViralKick.status == ViralKickStatus.APPROVED, 1))).label("approved"),
        func.count(case((ViralKick.status == ViralKickStatus.REJECTED, 1))).label("rejected"),
        func.count(case((ViralKick.status == ViralKickStatus.NEEDS_REVIEW, 1))).label("needs_review"),
        func.count(case((ViralKick.proof_ready == True, 1))).label("proof_ready"),
        func.avg(ViralKick.confidence).label("avg_confidence"),
    )
    
    result = await db.execute(stats_query)
    row = result.one()
    
    return {
        "total": row.total,
        "by_status": {
            "pending": row.pending,
            "approved": row.approved,
            "rejected": row.rejected,
            "needs_review": row.needs_review,
        },
        "proof_ready": row.proof_ready,
        "avg_confidence": round(float(row.avg_confidence or 0), 3),
    }


# ==================
# P1-3: CLUSTER TEST API
# ==================

@router.post("/clusters/test")
async def run_cluster_test(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_curator),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0),
    limit: int = Query(500, le=1000),
):
    """
    Run cluster test on proof-ready kicks.
    
    Only kicks with proof_ready=true and confidence >= min_confidence
    are included in clustering.
    
    Returns cluster assignments and quality metrics.
    """
    from app.services.vdg_2pass.cluster_test import cluster_test_service
    
    result = await cluster_test_service.run_test(
        db=db,
        min_confidence=min_confidence,
        limit=limit,
    )
    
    return result


@router.get("/clusters/test/summary")
async def get_cluster_test_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_curator),
):
    """
    Get quick cluster test summary without running full test.
    Just counts potential candidates.
    """
    # Count proof-ready kicks
    proof_ready_count = await db.execute(
        select(func.count(ViralKick.id))
        .where(ViralKick.proof_ready == True)
    )
    total_proof_ready = proof_ready_count.scalar() or 0
    
    # Count high-confidence (>=0.7)
    high_conf_count = await db.execute(
        select(func.count(ViralKick.id))
        .where(ViralKick.proof_ready == True)
        .where(ViralKick.confidence >= 0.7)
    )
    high_conf = high_conf_count.scalar() or 0
    
    # Count distinct nodes
    distinct_nodes = await db.execute(
        select(func.count(func.distinct(ViralKick.node_id)))
        .where(ViralKick.proof_ready == True)
    )
    node_count = distinct_nodes.scalar() or 0
    
    return {
        "proof_ready_kicks": total_proof_ready,
        "high_confidence_kicks": high_conf,
        "distinct_nodes": node_count,
        "cluster_ready": total_proof_ready >= 10,
        "message": f"{total_proof_ready} kicks ready for clustering" if total_proof_ready >= 10 
                   else f"Need at least 10 proof-ready kicks (currently {total_proof_ready})",
    }
