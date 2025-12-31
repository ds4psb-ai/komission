"""
MCP E2E HTTP 테스트
FastAPI + MCP 마운트 경로를 고려한 테스트
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Health 엔드포인트 테스트"""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_health_returns_ok(self, client):
        """헬스체크 성공"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_health_includes_mcp(self, client):
        """헬스체크에 MCP 상태 포함"""
        response = client.get("/health")
        data = response.json()
        assert "services" in data
        assert "mcp" in data["services"]


class TestMCPMount:
    """MCP 마운트 테스트"""
    
    def test_mcp_mounted_in_routes(self):
        """FastAPI routes에 MCP 포함"""
        from app.main import app
        
        mcp_found = False
        for route in app.routes:
            path = getattr(route, 'path', '')
            if '/mcp' in path:
                mcp_found = True
                break
        
        assert mcp_found, "MCP not found in FastAPI routes"
    
    def test_mcp_app_type(self):
        """MCP 앱 타입 확인"""
        from app.mcp.http_server import app as mcp_app
        assert 'Starlette' in type(mcp_app).__name__


class TestFrontendFilesExist:
    """Frontend MCP 파일 존재 테스트"""
    
    def test_mcp_client_exists(self):
        """mcp-client.ts 존재"""
        import os
        assert os.path.exists("/Users/ted/komission/frontend/src/lib/mcp-client.ts")
    
    def test_mcp_hooks_exists(self):
        """mcp-hooks.ts 존재"""
        import os
        assert os.path.exists("/Users/ted/komission/frontend/src/lib/mcp-hooks.ts")
    
    def test_ai_analysis_panel_exists(self):
        """AIAnalysisPanel.tsx 존재"""
        import os
        assert os.path.exists("/Users/ted/komission/frontend/src/components/mcp/AIAnalysisPanel.tsx")
    
    def test_batch_analysis_modal_exists(self):
        """BatchAnalysisModal.tsx 존재"""
        import os
        assert os.path.exists("/Users/ted/komission/frontend/src/components/mcp/BatchAnalysisModal.tsx")
    
    def test_mcp_index_exists(self):
        """index.ts 존재"""
        import os
        assert os.path.exists("/Users/ted/komission/frontend/src/components/mcp/index.ts")


class TestMCPServerImport:
    """MCP 서버 import 테스트"""
    
    def test_mcp_package_import(self):
        """MCP 패키지 import 성공"""
        from app.mcp import mcp
        assert mcp is not None
        assert mcp.name == "Komission"
    
    def test_mcp_http_server_import(self):
        """HTTP 서버 import 성공"""
        from app.mcp.http_server import app
        assert app is not None
    
    def test_legacy_wrapper_import(self):
        """레거시 래퍼 호환"""
        from app.mcp_server import mcp as legacy_mcp
        from app.mcp import mcp
        assert legacy_mcp is mcp


class TestMCPToolsRegistration:
    """MCP 도구 등록 테스트"""
    
    def test_expected_tools_count(self):
        """도구 개수 확인"""
        from app.mcp import mcp
        tools = mcp._tool_manager._tools
        assert len(tools) >= 5
    
    def test_all_tools_registered(self):
        """모든 도구 등록"""
        from app.mcp import mcp
        tools = mcp._tool_manager._tools
        
        expected = [
            'search_patterns',
            'generate_source_pack',
            'reanalyze_vdg',
            'smart_pattern_analysis',
            'ai_batch_analysis'
        ]
        
        for tool_name in expected:
            assert tool_name in tools, f"{tool_name} not registered"


class TestMCPResourcesRegistration:
    """MCP 리소스 등록 테스트"""
    
    def test_expected_resources_count(self):
        """리소스 개수 확인"""
        from app.mcp import mcp
        rm = mcp._resource_manager
        templates = rm._templates if hasattr(rm, '_templates') else {}
        assert len(templates) >= 6


class TestMCPPromptsRegistration:
    """MCP 프롬프트 등록 테스트"""
    
    def test_expected_prompts_count(self):
        """프롬프트 개수 확인"""
        from app.mcp import mcp
        prompts = mcp._prompt_manager._prompts
        assert len(prompts) >= 3
    
    def test_all_prompts_registered(self):
        """모든 프롬프트 등록"""
        from app.mcp import mcp
        prompts = mcp._prompt_manager._prompts
        
        expected = ['explain_recommendation', 'shooting_guide', 'risk_summary']
        
        for prompt_name in expected:
            assert prompt_name in prompts, f"{prompt_name} not registered"
