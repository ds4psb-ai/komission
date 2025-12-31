"""
Komission MCP Server Core
FastMCP 2.14+ 기반 MCP 서버 설정 (MCP 2025-11-25 스펙)
"""
import time
import logging
from fastmcp import FastMCP
from app.mcp.middleware.audit import MCPAuditLogger, AuditEntry

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


def get_logger():
    """Get MCP server logger"""
    return logger


# ===== 감사 로깅 유틸리티 =====

def log_tool_call(tool_name: str, params: dict, start_time: float, result=None, error=None):
    """도구 호출 감사 로그 기록"""
    duration_ms = (time.time() - start_time) * 1000
    
    # 결과 프리뷰 생성
    result_preview = None
    if result is not None:
        if isinstance(result, str):
            result_preview = result[:200]
        elif hasattr(result, 'model_dump_json'):
            result_preview = result.model_dump_json()[:200]
    
    entry = AuditEntry(
        tool_name=tool_name,
        params={k: str(v)[:50] for k, v in params.items() if k not in ('ctx', 'progress')},
        duration_ms=duration_ms,
        success=error is None,
        error=str(error)[:200] if error else None,
        result_preview=result_preview
    )
    
    MCPAuditLogger.log(entry)
    return entry


def get_audit_stats() -> dict:
    """감사 통계 조회"""
    return MCPAuditLogger.get_stats()


def get_recent_logs(limit: int = 100) -> list[dict]:
    """최근 로그 조회"""
    return MCPAuditLogger.get_recent(limit)

