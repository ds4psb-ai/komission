"""
MCP 감사 로그 조회 API
/api/v1/mcp/audit 엔드포인트
"""
from fastapi import APIRouter, Query

from app.mcp.server import get_audit_stats, get_recent_logs

router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.get("/audit/stats")
async def get_mcp_audit_stats():
    """
    MCP 도구 호출 통계 조회
    
    Returns:
        total_calls: 총 호출 수
        success_rate: 성공률 (%)
        avg_duration_ms: 평균 응답 시간 (ms)
    """
    return get_audit_stats()


@router.get("/audit/logs")
async def get_mcp_audit_logs(
    limit: int = Query(default=100, ge=1, le=1000)
):
    """
    최근 MCP 도구 호출 로그 조회
    
    Args:
        limit: 조회할 로그 수 (최대 1000)
    
    Returns:
        logs: 로그 목록 (최신순)
    """
    logs = get_recent_logs(limit)
    return {"logs": logs, "count": len(logs)}
