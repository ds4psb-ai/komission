"""
MCP Audit Logging Middleware
도구 호출 로깅 및 사용량 추적
"""
import time
import json
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger("mcp.audit")
logger.setLevel(logging.INFO)

# 파일 핸들러 추가 (선택)
# handler = logging.FileHandler("mcp_audit.log")
# handler.setFormatter(logging.Formatter('%(asctime)s|%(message)s'))
# logger.addHandler(handler)


class AuditEntry:
    """감사 로그 항목"""
    def __init__(
        self,
        tool_name: str,
        params: dict,
        user_id: str = None,
        duration_ms: float = 0,
        success: bool = True,
        error: str = None,
        result_preview: str = None
    ):
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.tool_name = tool_name
        self.params = params
        self.user_id = user_id
        self.duration_ms = duration_ms
        self.success = success
        self.error = error
        self.result_preview = result_preview[:200] if result_preview else None
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "tool": self.tool_name,
            "params": self.params,
            "user_id": self.user_id,
            "duration_ms": round(self.duration_ms, 2),
            "success": self.success,
            "error": self.error,
            "result_preview": self.result_preview
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def audit_tool_call(func: Callable) -> Callable:
    """도구 호출 감사 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        tool_name = func.__name__
        
        # 파라미터 추출 (민감 정보 필터링)
        params = {k: v for k, v in kwargs.items() if k != 'ctx'}
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # 결과 프리뷰 생성
            result_preview = None
            if isinstance(result, str):
                result_preview = result
            elif hasattr(result, 'model_dump_json'):
                result_preview = result.model_dump_json()
            
            entry = AuditEntry(
                tool_name=tool_name,
                params=params,
                duration_ms=duration_ms,
                success=True,
                result_preview=result_preview
            )
            
            logger.info(entry.to_json())
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            entry = AuditEntry(
                tool_name=tool_name,
                params=params,
                duration_ms=duration_ms,
                success=False,
                error=str(e)[:200]
            )
            
            logger.error(entry.to_json())
            raise
    
    return wrapper


class MCPAuditLogger:
    """MCP 감사 로거 (중앙 집중식)"""
    
    _entries: list[AuditEntry] = []
    _max_entries: int = 10000
    
    @classmethod
    def log(cls, entry: AuditEntry):
        """로그 항목 추가"""
        cls._entries.append(entry)
        logger.info(entry.to_json())
        
        # 메모리 관리
        if len(cls._entries) > cls._max_entries:
            cls._entries = cls._entries[-cls._max_entries:]
    
    @classmethod
    def get_recent(cls, limit: int = 100) -> list[dict]:
        """최근 로그 조회"""
        return [e.to_dict() for e in cls._entries[-limit:]]
    
    @classmethod
    def get_stats(cls) -> dict:
        """통계 조회"""
        if not cls._entries:
            return {"total_calls": 0, "success_rate": 0, "avg_duration_ms": 0}
        
        total = len(cls._entries)
        success = sum(1 for e in cls._entries if e.success)
        avg_duration = sum(e.duration_ms for e in cls._entries) / total
        
        return {
            "total_calls": total,
            "success_rate": round(success / total * 100, 1),
            "avg_duration_ms": round(avg_duration, 2)
        }
    
    @classmethod
    def clear(cls):
        """로그 초기화"""
        cls._entries = []
