"""
MCP Tools - AI 기반 스마트 분석 도구
Claude Desktop 호환 - 데이터 반환 방식

핵심 원리:
- 서버는 구조화된 데이터만 반환
- Claude Desktop이 자체 모델로 분석/포매팅
- 사용자 Claude Pro 구독 활용 (서버 비용 $0)
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import OutlierItem, RemixNode
from app.mcp.server import mcp, get_logger
from app.mcp.utils.validators import validate_uuid, safe_format_number

logger = get_logger()


@mcp.tool(
    tags=["analysis", "pattern", "data-provider"],
)
async def smart_pattern_analysis(
    outlier_id: str,
    analysis_type: str = "full"
) -> str:
    """
    패턴 분석용 구조화 데이터 제공
    
    Claude Desktop이 이 데이터를 받아서 자체 분석합니다.
    서버 API 비용 없이 고품질 AI 분석이 가능합니다.
    
    Args:
        outlier_id: 분석할 아웃라이어 UUID
        analysis_type: 데이터 범위 (full, basic, vdg_only)
    
    Returns:
        구조화된 패턴 데이터 (Claude가 분석할 원본)
    """
    logger.info(f"Tool call: smart_pattern_analysis(outlier_id='{outlier_id}', type='{analysis_type}')")
    
    # Validate UUID
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        return "❌ Error: Invalid outlier ID format. Expected UUID."
    
    try:
        async with AsyncSessionLocal() as db:
            # 아웃라이어 조회
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                return f"❌ Error: Outlier '{outlier_id}' not found."
            
            # VDG 분석 데이터 조회
            vdg_data = None
            if outlier.promoted_to_node_id:
                node_result = await db.execute(
                    select(RemixNode).where(RemixNode.id == outlier.promoted_to_node_id)
                )
                node = node_result.scalar_one_or_none()
                if node and node.gemini_analysis:
                    vdg_data = node.gemini_analysis
            
            # 구조화된 데이터 반환 (Claude가 분석할 원본)
            data = f"""
# 📊 패턴 분석 데이터

## 기본 정보
- **ID**: {outlier.id}
- **제목**: {outlier.title or 'Untitled'}
- **플랫폼**: {outlier.platform}
- **카테고리**: {outlier.category}
- **Tier**: {outlier.outlier_tier}
- **Score**: {outlier.outlier_score or 0:.1f}

## 성과 지표
- **조회수**: {safe_format_number(outlier.view_count)}
- **좋아요**: {safe_format_number(outlier.like_count)}
- **공유**: {safe_format_number(outlier.share_count)}
- **성장률**: {outlier.growth_rate if outlier.growth_rate else 'N/A'}%
- **참여율**: {outlier.engagement_rate if outlier.engagement_rate else 'N/A'}%

## 크리에이터 비교
- **크리에이터 평균 조회수**: {safe_format_number(outlier.creator_avg_views)}
- **아웃라이어 배율**: {(outlier.view_count or 0) / max(outlier.creator_avg_views or 1, 1):.1f}x

## 영상 링크
- **원본**: {outlier.video_url or 'N/A'}
"""

            if vdg_data and analysis_type in ("full", "vdg_only"):
                data += f"""
## VDG 분석 (Video DNA Genome)
- **훅 타입**: {vdg_data.get('hook_genome', {}).get('hook_type', 'N/A')}
- **훅 지속시간**: {vdg_data.get('hook_genome', {}).get('duration', 'N/A')}초
- **씬 개수**: {len(vdg_data.get('scenes', []))}
- **콘텐츠 전략**: {vdg_data.get('content_strategy', 'N/A')}
"""

            data += """
---
💡 **분석 요청**: 위 데이터를 바탕으로 이 패턴이 왜 성공했는지, 
어떻게 재현할 수 있는지 분석해주세요.
"""
            
            return data
                
    except SQLAlchemyError as e:
        logger.error(f"Database error in smart_pattern_analysis: {e}")
        return "❌ Database error: Unable to fetch outlier data."
    except Exception as e:
        logger.error(f"Unexpected error in smart_pattern_analysis: {e}")
        return f"❌ Error: {str(e)[:100]}"


@mcp.tool(
    tags=["analysis", "batch", "data-provider"],
)
async def ai_batch_analysis(
    outlier_ids: list[str],
    focus: str = "comparison"
) -> str:
    """
    여러 패턴의 배치 분석 데이터 제공
    
    Claude Desktop이 여러 패턴을 비교 분석합니다.
    
    Args:
        outlier_ids: 분석할 아웃라이어 UUID 목록 (2-10개)
        focus: 분석 초점 (comparison, trends, strategy)
    
    Returns:
        비교 분석용 구조화된 데이터
    """
    logger.info(f"Tool call: ai_batch_analysis(count={len(outlier_ids)}, focus='{focus}')")
    
    if len(outlier_ids) > 10:
        return "❌ Error: Maximum 10 outliers per batch analysis."
    
    if len(outlier_ids) < 2:
        return "❌ Error: At least 2 outliers required for batch analysis."
    
    try:
        async with AsyncSessionLocal() as db:
            # 유효한 UUID만 필터
            valid_uuids = [validate_uuid(oid) for oid in outlier_ids if validate_uuid(oid)]
            
            if len(valid_uuids) < 2:
                return "❌ Error: At least 2 valid UUIDs required."
            
            # 아웃라이어 조회
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id.in_(valid_uuids))
            )
            outliers = result.scalars().all()
            
            if len(outliers) < 2:
                return "❌ Error: At least 2 outliers found required."
            
            # 배치 데이터 구성
            data = f"""
# 📊 배치 분석 데이터 ({len(outliers)}개 패턴)

## 분석 초점: {focus}

"""
            # 요약 통계
            total_views = sum(o.view_count or 0 for o in outliers)
            avg_growth = sum(o.growth_rate or 0 for o in outliers) / len(outliers)
            tiers = [o.outlier_tier for o in outliers]
            
            data += f"""## 전체 요약
- **총 조회수**: {safe_format_number(total_views)}
- **평균 성장률**: {avg_growth:.1f}%
- **Tier 분포**: {', '.join(tiers)}

---

"""
            # 개별 패턴 데이터
            for i, o in enumerate(outliers, 1):
                data += f"""### 패턴 {i}: {o.title or 'Untitled'}
| 항목 | 값 |
|------|-----|
| Tier | {o.outlier_tier} (Score: {o.outlier_score or 0:.0f}) |
| 플랫폼 | {o.platform} |
| 카테고리 | {o.category} |
| 조회수 | {safe_format_number(o.view_count)} |
| 성장률 | {o.growth_rate or 'N/A'}% |
| 참여율 | {o.engagement_rate or 'N/A'}% |

"""
            
            focus_prompts = {
                "comparison": "각 패턴의 차이점과 공통점을 분석해주세요.",
                "trends": "이 패턴들에서 발견되는 트렌드를 파악해주세요.",
                "strategy": "이 패턴들을 바탕으로 콘텐츠 전략을 제안해주세요."
            }
            
            data += f"""---
💡 **분석 요청**: {focus_prompts.get(focus, focus_prompts['comparison'])}
"""
            
            return data
                
    except SQLAlchemyError as e:
        logger.error(f"Database error in ai_batch_analysis: {e}")
        return "❌ Database error"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"❌ Error: {str(e)[:100]}"


@mcp.tool(
    tags=["data", "influencer", "performance"],
)
async def get_pattern_performance(
    outlier_id: str,
    period: str = "30d"
) -> str:
    """
    패턴 성과 데이터 조회
    
    Claude Desktop에서 성과 분석 시 사용합니다.
    
    Args:
        outlier_id: 아웃라이어 UUID
        period: 분석 기간 (7d, 30d, 90d)
    
    Returns:
        성과 데이터
    """
    logger.info(f"Tool call: get_pattern_performance(outlier_id='{outlier_id}', period='{period}')")
    
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        return "❌ Invalid UUID format"
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                return f"❌ Outlier not found: {outlier_id}"
            
            # 성과 데이터 반환
            multiplier = (outlier.view_count or 0) / max(outlier.creator_avg_views or 1, 1)
            
            # 타입 안전 변환 (문자열 포함 처리)
            def safe_float(val, default=0.0):
                if val is None:
                    return default
                if isinstance(val, (int, float)):
                    return float(val)
                try:
                    # 숫자만 추출 시도
                    import re
                    match = re.search(r'[\d.]+', str(val))
                    return float(match.group()) if match else default
                except:
                    return default
            
            growth_val = safe_float(outlier.growth_rate)
            engagement_val = safe_float(outlier.engagement_rate)
            
            return f"""
# 📈 성과 데이터 ({period})

## {outlier.title or 'Untitled'}

| 지표 | 값 | 평가 |
|------|-----|-----|
| 조회수 | {safe_format_number(outlier.view_count)} | {'🔥 바이럴' if multiplier > 5 else '⭐ 양호'} |
| 성장률 | {growth_val:.1f}% | {'🚀 급성장' if growth_val > 100 else '📈 성장'} |
| 참여율 | {engagement_val:.1f}% | {'💎 높음' if engagement_val > 5 else '✅ 평균'} |
| 크리에이터 대비 | {multiplier:.1f}x | {'🎯 아웃라이어' if multiplier > 3 else '👍 정상'} |
| Tier | {outlier.outlier_tier} | Score {outlier.outlier_score or 0:.0f} |

---
💡 이 데이터를 바탕으로 성과를 평가해주세요.
"""
                
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)[:100]}"
