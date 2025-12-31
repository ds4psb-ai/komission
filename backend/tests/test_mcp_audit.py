"""
MCP Audit Logging 테스트
"""
import pytest
import time


class TestAuditEntry:
    """AuditEntry 클래스 테스트"""
    
    def test_audit_entry_creation(self):
        """AuditEntry 생성"""
        from app.mcp.middleware.audit import AuditEntry
        
        entry = AuditEntry(
            tool_name="search_patterns",
            params={"query": "beauty"},
            duration_ms=100.5,
            success=True
        )
        
        assert entry.tool_name == "search_patterns"
        assert entry.params == {"query": "beauty"}
        assert entry.success is True
        assert entry.duration_ms == 100.5
    
    def test_audit_entry_to_dict(self):
        """to_dict 변환"""
        from app.mcp.middleware.audit import AuditEntry
        
        entry = AuditEntry(
            tool_name="test_tool",
            params={"id": "123"},
            duration_ms=50.0,
            success=True,
            result_preview="Test result"
        )
        
        data = entry.to_dict()
        
        assert data["tool"] == "test_tool"
        assert data["success"] is True
        assert data["result_preview"] == "Test result"
        assert "timestamp" in data
    
    def test_audit_entry_to_json(self):
        """JSON 직렬화"""
        from app.mcp.middleware.audit import AuditEntry
        
        entry = AuditEntry(
            tool_name="test",
            params={},
            duration_ms=10.0,
            success=True
        )
        
        json_str = entry.to_json()
        
        assert '"tool": "test"' in json_str
        assert '"success": true' in json_str
    
    def test_audit_entry_error_case(self):
        """에러 케이스"""
        from app.mcp.middleware.audit import AuditEntry
        
        entry = AuditEntry(
            tool_name="failed_tool",
            params={},
            duration_ms=5.0,
            success=False,
            error="Something went wrong"
        )
        
        assert entry.success is False
        assert entry.error == "Something went wrong"


class TestMCPAuditLogger:
    """MCPAuditLogger 클래스 테스트"""
    
    def test_log_and_get_recent(self):
        """로그 기록 및 조회"""
        from app.mcp.middleware.audit import MCPAuditLogger, AuditEntry
        
        # 초기화
        MCPAuditLogger.clear()
        
        # 로그 추가
        entry1 = AuditEntry("tool1", {"a": 1}, duration_ms=10.0, success=True)
        entry2 = AuditEntry("tool2", {"b": 2}, duration_ms=20.0, success=True)
        
        MCPAuditLogger.log(entry1)
        MCPAuditLogger.log(entry2)
        
        # 조회
        recent = MCPAuditLogger.get_recent(10)
        
        assert len(recent) == 2
        assert recent[0]["tool"] == "tool1"
        assert recent[1]["tool"] == "tool2"
    
    def test_get_stats(self):
        """통계 조회"""
        from app.mcp.middleware.audit import MCPAuditLogger, AuditEntry
        
        MCPAuditLogger.clear()
        
        # 3개 성공, 1개 실패
        for i in range(3):
            MCPAuditLogger.log(AuditEntry(f"tool{i}", {}, duration_ms=100.0, success=True))
        MCPAuditLogger.log(AuditEntry("fail", {}, duration_ms=50.0, success=False))
        
        stats = MCPAuditLogger.get_stats()
        
        assert stats["total_calls"] == 4
        assert stats["success_rate"] == 75.0  # 3/4 * 100
    
    def test_clear(self):
        """로그 초기화"""
        from app.mcp.middleware.audit import MCPAuditLogger, AuditEntry
        
        MCPAuditLogger.log(AuditEntry("test", {}, duration_ms=1.0, success=True))
        assert MCPAuditLogger.get_stats()["total_calls"] > 0
        
        MCPAuditLogger.clear()
        
        assert MCPAuditLogger.get_stats()["total_calls"] == 0


class TestServerAuditFunctions:
    """server.py 감사 함수 테스트"""
    
    def test_log_tool_call_success(self):
        """log_tool_call 성공 케이스"""
        from app.mcp.server import log_tool_call
        from app.mcp.middleware.audit import MCPAuditLogger
        
        MCPAuditLogger.clear()
        
        start_time = time.time() - 0.05  # 50ms 전
        entry = log_tool_call(
            tool_name="search_patterns",
            params={"query": "test"},
            start_time=start_time,
            result="Test result"
        )
        
        assert entry.tool_name == "search_patterns"
        assert entry.success is True
        assert entry.duration_ms > 0  # 양수면 OK
    
    def test_log_tool_call_error(self):
        """log_tool_call 에러 케이스"""
        from app.mcp.server import log_tool_call
        from app.mcp.middleware.audit import MCPAuditLogger
        
        MCPAuditLogger.clear()
        
        start_time = time.time()
        entry = log_tool_call(
            tool_name="failed_tool",
            params={},
            start_time=start_time,
            error=ValueError("Test error")
        )
        
        assert entry.success is False
        assert "Test error" in entry.error
    
    def test_get_audit_stats(self):
        """get_audit_stats 함수"""
        from app.mcp.server import get_audit_stats
        
        stats = get_audit_stats()
        
        assert "total_calls" in stats
        assert "success_rate" in stats
        assert "avg_duration_ms" in stats
    
    def test_get_recent_logs(self):
        """get_recent_logs 함수"""
        from app.mcp.server import get_recent_logs
        
        logs = get_recent_logs(10)
        
        assert isinstance(logs, list)


class TestMCPAuditRouter:
    """MCP Audit API 라우터 테스트"""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    def test_audit_stats_endpoint(self, client):
        """통계 엔드포인트"""
        response = client.get("/api/v1/mcp/audit/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_calls" in data
        assert "success_rate" in data
    
    def test_audit_logs_endpoint(self, client):
        """로그 조회 엔드포인트"""
        response = client.get("/api/v1/mcp/audit/logs?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "count" in data
