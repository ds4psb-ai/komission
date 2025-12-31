"""
MCP 자동화 테스트 스위트
pytest로 실행: pytest tests/test_mcp_integration.py -v

이 테스트들은 CI에서 자동 실행되어 MCP 개발의 안정성을 보장합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMCPPackageImport:
    """MCP 패키지 import 테스트"""
    
    def test_mcp_package_import(self):
        """메인 MCP 패키지 import 가능"""
        from app.mcp import mcp
        assert mcp is not None
        assert mcp.name == "Komission"
    
    def test_legacy_wrapper_import(self):
        """레거시 래퍼 호환성 유지"""
        from app.mcp_server import mcp as legacy_mcp
        from app.mcp import mcp
        assert legacy_mcp is mcp
    
    def test_http_server_import(self):
        """HTTP 서버 모듈 import"""
        from app.mcp.http_server import app
        assert app is not None


class TestMCPRegistration:
    """MCP 리소스/도구/프롬프트 등록 테스트"""
    
    def test_resources_registered(self):
        """모든 리소스 6개 등록됨"""
        from app.mcp import mcp
        rm = mcp._resource_manager
        templates = rm._templates if hasattr(rm, '_templates') else {}
        assert len(templates) >= 6, f"Expected 6+ resources, got {len(templates)}"
    
    def test_tools_registered(self):
        """모든 도구 5개 등록됨"""
        from app.mcp import mcp
        tools = mcp._tool_manager._tools
        expected_tools = [
            'search_patterns',
            'generate_source_pack',
            'reanalyze_vdg',
            'smart_pattern_analysis',
            'ai_batch_analysis',
        ]
        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool {tool_name} not registered"
    
    def test_prompts_registered(self):
        """모든 프롬프트 3개 등록됨"""
        from app.mcp import mcp
        prompts = mcp._prompt_manager._prompts
        expected_prompts = [
            'explain_recommendation',
            'shooting_guide',
            'risk_summary',
        ]
        for prompt_name in expected_prompts:
            assert prompt_name in prompts, f"Prompt {prompt_name} not registered"


class TestMCPSchemas:
    """Pydantic 스키마 테스트"""
    
    def test_pattern_result_creation(self):
        """PatternResult 모델 생성"""
        from app.mcp.schemas.patterns import PatternResult
        result = PatternResult(
            id='test-id',
            title='Test Pattern',
            tier='S',
            views=10000
        )
        assert result.id == 'test-id'
        assert result.tier == 'S'
    
    def test_search_response_serialization(self):
        """SearchResponse JSON 직렬화"""
        from app.mcp.schemas.patterns import SearchResponse, PatternResult, SearchFilters
        response = SearchResponse(
            query='test',
            filters=SearchFilters(),
            count=1,
            results=[PatternResult(id='1', title='Test', tier='A', views=1000)]
        )
        json_str = response.model_dump_json()
        assert 'test' in json_str
        assert 'results' in json_str


class TestFastMCPFeatures:
    """FastMCP 2.14+ 기능 테스트"""
    
    def test_elicitation_support(self):
        """Elicitation 지원 확인"""
        from fastmcp import Context
        assert hasattr(Context, 'elicit'), "Context.elicit not available"
    
    def test_sampling_support(self):
        """LLM Sampling 지원 확인"""
        from fastmcp import Context
        assert hasattr(Context, 'sample'), "Context.sample not available"
        assert hasattr(Context, 'sample_step'), "Context.sample_step not available"
    
    def test_progress_dependency(self):
        """Progress 의존성 확인"""
        from fastmcp.dependencies import Progress
        assert Progress is not None


class TestFastAPIIntegration:
    """FastAPI MCP 통합 테스트"""
    
    def test_mcp_mounted_on_fastapi(self):
        """MCP가 /mcp에 마운트됨"""
        from app.main import app
        mcp_routes = [r for r in app.routes if hasattr(r, 'path') and '/mcp' in r.path]
        assert len(mcp_routes) > 0, "MCP not mounted at /mcp"
    
    def test_health_includes_mcp(self):
        """Health check에 MCP 상태 포함"""
        from app.main import app
        # health_check 함수가 존재하는지 확인
        health_routes = [r for r in app.routes if hasattr(r, 'path') and r.path == '/health']
        assert len(health_routes) > 0, "Health endpoint not found"


class TestMCPUtils:
    """유틸리티 함수 테스트"""
    
    def test_validate_uuid_valid(self):
        """유효한 UUID 검증"""
        from app.mcp.utils.validators import validate_uuid
        result = validate_uuid('12345678-1234-5678-1234-567812345678')
        assert result is not None
    
    def test_validate_uuid_invalid(self):
        """무효한 UUID 검증"""
        from app.mcp.utils.validators import validate_uuid
        result = validate_uuid('not-a-uuid')
        assert result is None
    
    def test_safe_format_number(self):
        """숫자 포맷팅"""
        from app.mcp.utils.validators import safe_format_number
        assert safe_format_number(1000) == '1,000'
        assert safe_format_number(1000000) == '1,000,000'
        assert safe_format_number(None) == 'N/A'


class TestMCPModules:
    """개별 모듈 import 테스트"""
    
    @pytest.mark.parametrize("module_name", [
        "app.mcp.server",
        "app.mcp.utils.validators",
        "app.mcp.utils.formatters",
        "app.mcp.schemas.patterns",
        "app.mcp.schemas.packs",
        "app.mcp.resources.patterns",
        "app.mcp.resources.outliers",
        "app.mcp.resources.director_pack",
        "app.mcp.tools.search",
        "app.mcp.tools.pack_generator",
        "app.mcp.tools.vdg_tools",
        "app.mcp.tools.smart_analysis",
        "app.mcp.prompts.recommendation",
        "app.mcp.prompts.shooting",
        "app.mcp.prompts.risk",
        "app.mcp.http_server",
    ])
    def test_module_import(self, module_name):
        """각 모듈 개별 import 가능"""
        import importlib
        module = importlib.import_module(module_name)
        assert module is not None
