"""
Komission MCP Server - Resources & Prompts
FastMCP 2.x 기반 MCP 서버 구현

Resources (읽기 전용):
- komission://patterns/{cluster_id}
- komission://comments/{outlier_id}
- komission://evidence/{pattern_id}
- komission://recurrence/{cluster_id}
- komission://vdg/{outlier_id}

Prompts (템플릿):
- explain_recommendation
- shooting_guide
- risk_summary
"""
import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import OutlierItem, PatternCluster, PatternRecurrenceLink

# Configure logging
logger = logging.getLogger("mcp_server")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s [MCP] %(levelname)s: %(message)s'))
    logger.addHandler(handler)


# Initialize FastMCP server
mcp = FastMCP(
    "Komission",
    instructions="Pattern recommendation system for short-form video creators"
)


# ==================
# Helper Functions
# ==================

def validate_uuid(value: str) -> Optional[UUID]:
    """Validate and convert string to UUID, return None if invalid"""
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def safe_format_number(value, default: str = "N/A") -> str:
    """Safely format number with commas, return default if None"""
    if value is None:
        return default
    try:
        return f"{value:,}"
    except (ValueError, TypeError):
        return str(value)


def format_comments(comments: list) -> str:
    """Format best comments for display with error handling"""
    if not comments:
        return "No comments available"
    
    lines = []
    for i, c in enumerate(comments[:5], 1):
        try:
            text = str(c.get("text", ""))[:100]
            likes = c.get("likes", 0)
            lang = c.get("lang", "ko")
            lines.append(f"{i}. [{lang}] \"{text}...\" (👍 {likes})")
        except Exception as e:
            lines.append(f"{i}. [Error parsing comment: {e}]")
    
    return "\n".join(lines)


# ==================
# Resources (읽기 전용)
# ==================

@mcp.resource("komission://patterns/{cluster_id}")
async def get_pattern(cluster_id: str) -> str:
    """
    Pattern Library 항목 조회
    
    Returns pattern cluster information including:
    - Name and type
    - Member count and average score
    - Recurrence information
    """
    logger.info(f"Resource request: patterns/{cluster_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PatternCluster).where(PatternCluster.cluster_id == cluster_id)
            )
            cluster = result.scalar_one_or_none()
            
            if not cluster:
                logger.warning(f"Pattern cluster not found: {cluster_id}")
                return f"❌ Pattern cluster '{cluster_id}' not found"
            
            logger.info(f"Found pattern: {cluster.cluster_name}")
            return f"""
# Pattern: {cluster.cluster_name}

**ID**: {cluster.cluster_id}
**Type**: {cluster.pattern_type or 'N/A'}
**Members**: {cluster.member_count or 0}
**Avg Score**: {cluster.avg_outlier_score or 'N/A'}

## Recurrence Info
- Ancestor: {cluster.ancestor_cluster_id or 'None (Original)'}
- Score: {cluster.recurrence_score or 0:.2f}
- Count: {cluster.recurrence_count or 0}
- Origin: {cluster.origin_cluster_id or cluster.cluster_id}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_pattern: {e}")
        return f"❌ Database error: Unable to fetch pattern. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in get_pattern: {e}")
        return f"❌ Error fetching pattern: {str(e)[:100]}"


@mcp.resource("komission://comments/{outlier_id}")
async def get_comments(outlier_id: str) -> str:
    """
    베스트 댓글 5개 조회 (수집 시점 스냅샷)
    
    Returns top 5 comments from the outlier video,
    sorted by likes with language tags.
    """
    logger.info(f"Resource request: comments/{outlier_id}")
    
    # Validate UUID
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {outlier_id}")
        return f"❌ Invalid outlier ID format. Expected UUID, got: '{outlier_id[:50]}...'"
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Outlier not found: {outlier_id}")
                return f"❌ Outlier '{outlier_id}' not found"
            
            comments = outlier.best_comments or []
            
            logger.info(f"Found {len(comments)} comments for outlier")
            return f"""
# Best Comments for: {outlier.title or 'Untitled'}

**Platform**: {outlier.platform}
**Views**: {safe_format_number(outlier.view_count)}
**Tier**: {outlier.outlier_tier or 'N/A'}

## Top Comments
{format_comments(comments)}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_comments: {e}")
        return f"❌ Database error: Unable to fetch comments."
    except Exception as e:
        logger.error(f"Unexpected error in get_comments: {e}")
        return f"❌ Error fetching comments: {str(e)[:100]}"


@mcp.resource("komission://evidence/{pattern_id}")
async def get_evidence(pattern_id: str) -> str:
    """
    Evidence 요약 (댓글+신호+지표 종합)
    
    Returns comprehensive evidence summary including:
    - Engagement metrics
    - Best comments analysis
    - Growth signals
    """
    logger.info(f"Resource request: evidence/{pattern_id}")
    
    # Validate UUID
    uuid_val = validate_uuid(pattern_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {pattern_id}")
        return f"❌ Invalid pattern ID format. Expected UUID."
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Pattern not found: {pattern_id}")
                return f"❌ Pattern '{pattern_id}' not found"
            
            comments = outlier.best_comments or []
            
            # Analyze comment sentiment tags
            tag_counts = {}
            for c in comments:
                try:
                    tag = c.get("tag", "unknown")
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except Exception:
                    pass
            
            tag_summary = ", ".join([f"{k}: {v}" for k, v in tag_counts.items()]) or "No tags"
            
            logger.info(f"Evidence compiled for {pattern_id}")
            return f"""
# Evidence Summary

## Metrics
- **Views**: {safe_format_number(outlier.view_count)}
- **Likes**: {safe_format_number(outlier.like_count)}
- **Shares**: {safe_format_number(outlier.share_count)}
- **Growth Rate**: {outlier.growth_rate or 'N/A'}
- **Engagement Rate**: {outlier.engagement_rate or 'N/A'}

## Outlier Analysis
- **Tier**: {outlier.outlier_tier or 'N/A'}
- **Score**: {outlier.outlier_score or 'N/A'}
- **Creator Avg Views**: {safe_format_number(outlier.creator_avg_views)}

## Comment Signals
- **Total Comments**: {len(comments)}
- **Tag Distribution**: {tag_summary}

## Best Comments
{format_comments(comments)}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_evidence: {e}")
        return f"❌ Database error: Unable to fetch evidence."
    except Exception as e:
        logger.error(f"Unexpected error in get_evidence: {e}")
        return f"❌ Error fetching evidence: {str(e)[:100]}"


@mcp.resource("komission://recurrence/{cluster_id}")
async def get_recurrence(cluster_id: str) -> str:
    """
    재등장 lineage (배치 처리 결과)
    
    Returns pattern recurrence history and relationships.
    Note: This is pre-computed batch data, not real-time matching.
    """
    logger.info(f"Resource request: recurrence/{cluster_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            # Get cluster info
            cluster_result = await db.execute(
                select(PatternCluster).where(PatternCluster.cluster_id == cluster_id)
            )
            cluster = cluster_result.scalar_one_or_none()
            
            if not cluster:
                logger.warning(f"Cluster not found: {cluster_id}")
                return f"❌ Cluster '{cluster_id}' not found"
            
            # Get recurrence links (may be empty if not computed yet)
            try:
                links_result = await db.execute(
                    select(PatternRecurrenceLink)
                    .where(PatternRecurrenceLink.cluster_id_current == cluster_id)
                    .order_by(PatternRecurrenceLink.recurrence_score.desc())
                    .limit(10)
                )
                links = links_result.scalars().all()
            except Exception as link_err:
                logger.warning(f"Error fetching recurrence links: {link_err}")
                links = []
            
            links_text = ""
            if links:
                for link in links:
                    try:
                        links_text += (
                            f"- → {link.cluster_id_ancestor} "
                            f"(score: {link.recurrence_score:.2f}, status: {link.status})\n"
                        )
                    except Exception:
                        links_text += f"- → [Error parsing link]\n"
            else:
                links_text = "No recurrence links found"
            
            logger.info(f"Found {len(links)} recurrence links for {cluster_id}")
            return f"""
# Recurrence Lineage: {cluster_id}

## Current Cluster
- **Name**: {cluster.cluster_name}
- **Ancestor**: {cluster.ancestor_cluster_id or 'None (Original)'}
- **Origin**: {cluster.origin_cluster_id or cluster_id}
- **Recurrence Count**: {cluster.recurrence_count or 0}
- **Recurrence Score**: {cluster.recurrence_score or 0:.2f}
- **Last Recurrence**: {cluster.last_recurrence_at or 'Never'}

## Recurrence Links
{links_text}

> ⚠️ This data is from batch processing. Not real-time matching.
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_recurrence: {e}")
        return f"❌ Database error: Unable to fetch recurrence data."
    except Exception as e:
        logger.error(f"Unexpected error in get_recurrence: {e}")
        return f"❌ Error fetching recurrence: {str(e)[:100]}"


@mcp.resource("komission://vdg/{outlier_id}")
async def get_vdg(outlier_id: str) -> str:
    """
    VDG 분석 결과 조회
    
    Returns Video DNA Genome analysis results including
    quality scores and validation status.
    """
    logger.info(f"Resource request: vdg/{outlier_id}")
    
    # Validate UUID
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {outlier_id}")
        return f"❌ Invalid outlier ID format. Expected UUID."
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Outlier not found: {outlier_id}")
                return f"❌ Outlier '{outlier_id}' not found"
            
            logger.info(f"VDG data retrieved for {outlier_id}")
            return f"""
# VDG Analysis: {outlier.title or 'Untitled'}

## Basic Info
- **Platform**: {outlier.platform or 'N/A'}
- **Category**: {outlier.category or 'N/A'}
- **URL**: {outlier.video_url or 'N/A'}

## Analysis Status
- **Status**: {outlier.analysis_status or 'pending'}
- **Approved**: {outlier.approved_at or 'Not approved'}

## Quality Metrics
- **Quality Score**: {outlier.vdg_quality_score or 'Not analyzed'}
- **Valid**: {outlier.vdg_quality_valid if outlier.vdg_quality_valid is not None else 'Unknown'}
- **Issues**: {outlier.vdg_quality_issues or 'None'}

## Outlier Metrics
- **Tier**: {outlier.outlier_tier or 'N/A'}
- **Score**: {outlier.outlier_score or 'N/A'}
- **Views**: {safe_format_number(outlier.view_count)}
- **Growth**: {outlier.growth_rate or 'N/A'}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_vdg: {e}")
        return f"❌ Database error: Unable to fetch VDG data."
    except Exception as e:
        logger.error(f"Unexpected error in get_vdg: {e}")
        return f"❌ Error fetching VDG: {str(e)[:100]}"


# ==================
# Tools (실행)
# ==================

@mcp.tool()
async def search_patterns(
    query: str,
    category: str = None,
    platform: str = None,
    min_tier: str = "C",
    limit: int = 10
) -> str:
    """
    L1/L2 패턴 검색 (읽기 전용, 자동 승인)
    
    Search for patterns by keyword, category, or platform.
    Returns a list of matching patterns with scores.
    
    Args:
        query: Search keyword (matches title, cluster_name)
        category: Filter by category (beauty, meme, food, etc.)
        platform: Filter by platform (tiktok, youtube, instagram)
        min_tier: Minimum tier to include (S, A, B, C)
        limit: Maximum number of results (default 10, max 50)
    """
    from sqlalchemy import or_, func
    
    logger.info(f"Tool call: search_patterns(query='{query}', platform='{platform}', limit={limit})")
    
    # Input validation
    TIER_PRIORITY = {"S": 1, "A": 2, "B": 3, "C": 4}
    if min_tier not in TIER_PRIORITY:
        min_tier = "C"
    
    # Limit bounds
    limit = max(1, min(limit, 50))
    
    # Sanitize query (basic SQL injection prevention - SQLAlchemy handles this, but belt and suspenders)
    query = (query or "")[:100]  # Limit query length
    
    try:
        async with AsyncSessionLocal() as db:
            # Build query
            stmt = select(OutlierItem).where(
                OutlierItem.analysis_status == "completed",
                OutlierItem.outlier_tier.isnot(None),
            )
            
            # Apply text search
            if query:
                stmt = stmt.where(
                    or_(
                        OutlierItem.title.ilike(f"%{query}%"),
                        OutlierItem.category.ilike(f"%{query}%"),
                    )
                )
            
            # Apply filters
            if category:
                stmt = stmt.where(OutlierItem.category == category)
            if platform:
                stmt = stmt.where(OutlierItem.platform == platform)
            
            # Tier filter
            min_priority = TIER_PRIORITY.get(min_tier, 4)
            allowed_tiers = [t for t, p in TIER_PRIORITY.items() if p <= min_priority]
            stmt = stmt.where(OutlierItem.outlier_tier.in_(allowed_tiers))
            
            # Order by tier and score
            stmt = stmt.order_by(
                func.array_position(['S', 'A', 'B', 'C'], OutlierItem.outlier_tier),
                OutlierItem.outlier_score.desc(),
            ).limit(limit)
            
            result = await db.execute(stmt)
            patterns = result.scalars().all()
            
            if not patterns:
                logger.info("No patterns found")
                return "❌ No patterns found matching your criteria."
            
            logger.info(f"Found {len(patterns)} patterns")
            
            # Format results
            lines = [f"# Search Results for: '{query or 'all'}'\n"]
            lines.append(f"Found {len(patterns)} patterns:\n")
            
            for i, p in enumerate(patterns, 1):
                try:
                    lines.append(
                        f"{i}. **[{p.outlier_tier}]** {p.title or 'Untitled'}\n"
                        f"   - Platform: {p.platform or 'N/A'} | Category: {p.category or 'N/A'}\n"
                        f"   - Score: {p.outlier_score:.0f if p.outlier_score else 0} | Views: {safe_format_number(p.view_count)}\n"
                        f"   - ID: `{p.id}`\n"
                    )
                except Exception as fmt_err:
                    lines.append(f"{i}. [Error formatting result]\n")
            
            return "\n".join(lines)
            
    except SQLAlchemyError as e:
        logger.error(f"Database error in search_patterns: {e}")
        return f"❌ Database error: Unable to search patterns."
    except Exception as e:
        logger.error(f"Unexpected error in search_patterns: {e}")
        return f"❌ Error searching patterns: {str(e)[:100]}"


@mcp.tool()
async def generate_source_pack(
    outlier_ids: list[str],
    pack_name: str,
    include_comments: bool = True,
    include_vdg: bool = True
) -> str:
    """
    NotebookLM 소스팩 생성 (명시적 동의 필요 - 데이터 생성)
    
    Generate a NotebookLM-compatible source pack from selected outliers.
    This creates new data and requires explicit user consent.
    
    Args:
        outlier_ids: List of outlier UUIDs to include
        pack_name: Name for the source pack
        include_comments: Include best comments in pack
        include_vdg: Include VDG analysis data
    """
    from datetime import datetime
    import json
    
    logger.info(f"Tool call: generate_source_pack(count={len(outlier_ids)}, name='{pack_name}')")
    
    # Input validation
    if not outlier_ids or len(outlier_ids) == 0:
        return "❌ Error: No outlier IDs provided."
    
    if len(outlier_ids) > 100:
        return "❌ Error: Maximum 100 outliers per source pack."
    
    if not pack_name or len(pack_name.strip()) == 0:
        return "❌ Error: Pack name is required."
    
    pack_name = pack_name[:100]  # Limit name length
    
    # Validate UUIDs
    valid_uuids = []
    for oid in outlier_ids:
        uuid_val = validate_uuid(oid)
        if uuid_val:
            valid_uuids.append(uuid_val)
    
    if not valid_uuids:
        return "❌ Error: No valid UUIDs provided."
    
    try:
        async with AsyncSessionLocal() as db:
            # Fetch outliers
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id.in_(valid_uuids))
            )
            outliers = result.scalars().all()
            
            if not outliers:
                logger.warning("No outliers found for source pack")
                return "❌ Error: No valid outliers found for the provided IDs."
            
            # Build source pack
            pack_data = {
                "name": pack_name,
                "created_at": datetime.utcnow().isoformat(),
                "outlier_count": len(outliers),
                "sources": []
            }
            
            for outlier in outliers:
                try:
                    source = {
                        "id": str(outlier.id),
                        "title": outlier.title or "Untitled",
                        "platform": outlier.platform or "unknown",
                        "category": outlier.category or "unknown",
                        "tier": outlier.outlier_tier,
                        "score": outlier.outlier_score or 0,
                        "views": outlier.view_count or 0,
                        "growth_rate": outlier.growth_rate,
                        "video_url": outlier.video_url or "",
                    }
                    
                    if include_comments and outlier.best_comments:
                        source["comments"] = outlier.best_comments[:5]
                    
                    if include_vdg:
                        source["vdg"] = {
                            "quality_score": outlier.vdg_quality_score,
                            "quality_valid": outlier.vdg_quality_valid,
                            "analysis_status": outlier.analysis_status,
                        }
                    
                    pack_data["sources"].append(source)
                except Exception as src_err:
                    logger.warning(f"Error processing outlier for pack: {src_err}")
            
            logger.info(f"Generated source pack with {len(pack_data['sources'])} sources")
            
            # Format output
            source_list = []
            for i, s in enumerate(pack_data["sources"]):
                try:
                    source_list.append(
                        f"### {i+1}. {s['title']}\n"
                        f"- **Tier**: {s['tier'] or 'N/A'} | **Score**: {s['score']:.0f}\n"
                        f"- **Platform**: {s['platform']} | **Category**: {s['category']}\n"
                        f"- **Views**: {safe_format_number(s['views'])} | **Growth**: {s['growth_rate'] or 'N/A'}\n"
                        f"- **URL**: {s['video_url']}\n"
                    )
                except Exception:
                    source_list.append(f"### {i+1}. [Error formatting source]\n")
            
            return f"""
# Source Pack Generated: {pack_name}

**Created**: {pack_data['created_at']}
**Sources**: {pack_data['outlier_count']} outliers

## Included Sources

""" + "\n".join(source_list) + f"""

## Pack Data (JSON)

```json
{json.dumps(pack_data, indent=2, default=str)}
```

> ⚠️ This source pack is ready for NotebookLM import.
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in generate_source_pack: {e}")
        return f"❌ Database error: Unable to generate source pack."
    except Exception as e:
        logger.error(f"Unexpected error in generate_source_pack: {e}")
        return f"❌ Error generating source pack: {str(e)[:100]}"


@mcp.tool()
async def reanalyze_vdg(
    outlier_id: str,
    force: bool = False
) -> str:
    """
    VDG 재분석 요청 (명시적 동의 필요 - 비용 발생)
    
    Request a re-analysis of VDG (Video DNA Genome) for an outlier.
    This incurs API costs and requires explicit user consent.
    
    Args:
        outlier_id: UUID of the outlier to re-analyze
        force: Force re-analysis even if already completed
    """
    logger.info(f"Tool call: reanalyze_vdg(outlier_id='{outlier_id}', force={force})")
    
    # Validate UUID
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {outlier_id}")
        return f"❌ Error: Invalid outlier ID format. Expected UUID."
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Outlier not found: {outlier_id}")
                return f"❌ Error: Outlier '{outlier_id}' not found."
            
            # Check current status
            if outlier.analysis_status == "completed" and not force:
                logger.info(f"Outlier already analyzed, force={force}")
                return f"""
# VDG Re-analysis Not Needed

The outlier "{outlier.title or 'Untitled'}" already has a completed VDG analysis.

**Current Status**: {outlier.analysis_status}
**Quality Score**: {outlier.vdg_quality_score or 'N/A'}
**Valid**: {outlier.vdg_quality_valid if outlier.vdg_quality_valid is not None else 'Unknown'}

To force re-analysis, set `force=True`. Note: This will incur additional API costs.
"""
            
            # Queue for re-analysis
            outlier.analysis_status = "pending"
            await db.commit()
            
            logger.info(f"Queued {outlier_id} for VDG re-analysis")
            return f"""
# VDG Re-analysis Queued

**Outlier**: {outlier.title or 'Untitled'}
**ID**: {outlier_id}
**Status**: Queued for re-analysis

The VDG pipeline will process this outlier in the next batch.
Estimated completion: 5-10 minutes.

> ⚠️ This action incurs API costs for Gemini video analysis.
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in reanalyze_vdg: {e}")
        return f"❌ Database error: Unable to queue re-analysis."
    except Exception as e:
        logger.error(f"Unexpected error in reanalyze_vdg: {e}")
        return f"❌ Error queuing re-analysis: {str(e)[:100]}"

# ==================
# Prompts (템플릿)
# ==================

@mcp.prompt()
def explain_recommendation(pattern_id: str, tier: str, evidence_summary: str) -> str:
    """
    추천 이유 설명 템플릿
    
    Generate an explanation for why a pattern was recommended.
    """
    return f"""
Based on the following evidence, explain why this pattern is recommended:

**Pattern ID**: {pattern_id}
**Tier**: {tier}

**Evidence**:
{evidence_summary}

Please provide:
1. A clear, concise explanation of why this pattern works
2. Key success factors from the evidence
3. Potential risks or considerations
4. Actionable tips for creators
"""


@mcp.prompt()
def shooting_guide(pattern_summary: str, signature: str, platform: str) -> str:
    """
    촬영 가이드 요약 템플릿
    
    Generate a shooting guide for recreating a pattern.
    """
    return f"""
Create a shooting guide for the following pattern:

**Pattern**: {pattern_summary}
**Signature**: {signature}
**Platform**: {platform}

Please provide:
1. Step-by-step shooting instructions
2. Key timing and transition tips
3. Audio/music recommendations
4. Common mistakes to avoid
5. Equipment suggestions (mobile-friendly)
"""


@mcp.prompt()
def risk_summary(pattern_id: str, risk_tags: str, comments_analysis: str) -> str:
    """
    리스크 정리 템플릿
    
    Generate a risk assessment for a pattern.
    """
    return f"""
Analyze the risks for the following pattern:

**Pattern ID**: {pattern_id}
**Known Risk Tags**: {risk_tags}
**Comments Analysis**: {comments_analysis}

Please provide:
1. Risk level assessment (Low/Medium/High)
2. Specific risks identified
3. Mitigation strategies
4. Creator recommendations
"""


# ==================
# Server Entry Point
# ==================

if __name__ == "__main__":
    # Run as standalone MCP server
    mcp.run()
