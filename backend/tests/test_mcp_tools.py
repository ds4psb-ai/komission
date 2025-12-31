"""
MCP 도구 실제 실행 테스트
FastMCP decorator 래핑을 고려한 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Fixtures import
pytest_plugins = ['tests.conftest_mcp']


class TestSearchPatternsToolImport:
    """search_patterns 도구 import 테스트"""
    
    def test_search_patterns_registered(self):
        """search_patterns가 MCP에 등록됨"""
        from app.mcp import mcp
        assert 'search_patterns' in mcp._tool_manager._tools
    
    def test_search_patterns_has_correct_description(self):
        """도구 설명이 올바름"""
        from app.mcp import mcp
        tool = mcp._tool_manager._tools.get('search_patterns')
        assert tool is not None
        # description 또는 docstring 존재
        assert tool.fn.__doc__ is not None or hasattr(tool, 'description')


class TestSmartPatternAnalysisToolImport:
    """smart_pattern_analysis 도구 import 테스트"""
    
    def test_smart_pattern_analysis_registered(self):
        """smart_pattern_analysis가 MCP에 등록됨"""
        from app.mcp import mcp
        assert 'smart_pattern_analysis' in mcp._tool_manager._tools
    
    def test_smart_pattern_analysis_parameters(self):
        """도구 파라미터 검증"""
        from app.mcp import mcp
        import inspect
        
        tool = mcp._tool_manager._tools.get('smart_pattern_analysis')
        sig = inspect.signature(tool.fn)
        
        # 필수 파라미터 확인 (ctx 제거됨 - 데이터 반환 방식)
        params = list(sig.parameters.keys())
        assert 'outlier_id' in params
        assert 'analysis_type' in params


class TestAIBatchAnalysisToolImport:
    """ai_batch_analysis 도구 import 테스트"""
    
    def test_ai_batch_analysis_registered(self):
        """ai_batch_analysis가 MCP에 등록됨"""
        from app.mcp import mcp
        assert 'ai_batch_analysis' in mcp._tool_manager._tools
    
    def test_ai_batch_analysis_parameters(self):
        """도구 파라미터 검증"""
        from app.mcp import mcp
        import inspect
        
        tool = mcp._tool_manager._tools.get('ai_batch_analysis')
        sig = inspect.signature(tool.fn)
        
        params = list(sig.parameters.keys())
        assert 'outlier_ids' in params
        assert 'focus' in params  # summary_focus -> focus 로 변경됨


class TestGenerateSourcePackToolImport:
    """generate_source_pack 도구 import 테스트"""
    
    def test_generate_source_pack_registered(self):
        """generate_source_pack가 MCP에 등록됨"""
        from app.mcp import mcp
        assert 'generate_source_pack' in mcp._tool_manager._tools
    
    def test_generate_source_pack_has_elicitation_logic(self):
        """Elicitation 로직이 코드에 포함됨"""
        from app.mcp.tools.pack_generator import generate_source_pack
        import inspect
        
        source = inspect.getsource(generate_source_pack.fn)
        assert 'elicit' in source.lower()


class TestReanalyzeVDGToolImport:
    """reanalyze_vdg 도구 import 테스트"""
    
    def test_reanalyze_vdg_registered(self):
        """reanalyze_vdg가 MCP에 등록됨"""
        from app.mcp import mcp
        assert 'reanalyze_vdg' in mcp._tool_manager._tools
    
    def test_reanalyze_vdg_is_background_task(self):
        """Background Task로 설정됨"""
        from app.mcp import mcp
        
        tool = mcp._tool_manager._tools.get('reanalyze_vdg')
        # task_config가 있는지 확인
        assert hasattr(tool, 'task_config') or 'Progress' in str(tool.fn.__code__.co_varnames)


class TestMCPResourcesImport:
    """MCP 리소스 등록 테스트"""
    
    def test_all_resources_registered(self):
        """모든 리소스 등록됨"""
        from app.mcp import mcp
        
        rm = mcp._resource_manager
        templates = rm._templates if hasattr(rm, '_templates') else {}
        
        expected_patterns = [
            'patterns/{cluster_id}',
            'recurrence/{cluster_id}',
            'comments/{outlier_id}',
            'evidence/{pattern_id}',
            'vdg/{outlier_id}',
            'director-pack/{outlier_id}',
        ]
        
        template_uris = [str(uri) for uri in templates.keys()]
        
        for pattern in expected_patterns:
            found = any(pattern in uri for uri in template_uris)
            assert found, f"Resource pattern {pattern} not found"


class TestMCPPromptsImport:
    """MCP 프롬프트 등록 테스트"""
    
    def test_all_prompts_registered(self):
        """모든 프롬프트 등록됨"""
        from app.mcp import mcp
        
        prompts = mcp._prompt_manager._prompts
        
        expected_prompts = [
            'explain_recommendation',
            'shooting_guide',
            'risk_summary',
        ]
        
        for prompt_name in expected_prompts:
            assert prompt_name in prompts, f"Prompt {prompt_name} not registered"
    
    def test_prompts_have_function(self):
        """프롬프트 함수가 callable"""
        from app.mcp import mcp
        
        prompts = mcp._prompt_manager._prompts
        
        for name, prompt in prompts.items():
            assert hasattr(prompt, 'fn') or callable(prompt)


class TestValidators:
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
    
    def test_validate_uuid_none(self):
        """None 입력"""
        from app.mcp.utils.validators import validate_uuid
        result = validate_uuid(None)
        assert result is None
    
    def test_validate_uuid_empty(self):
        """빈 문자열"""
        from app.mcp.utils.validators import validate_uuid
        result = validate_uuid('')
        assert result is None
    
    def test_safe_format_number_normal(self):
        """정상 숫자 포맷팅"""
        from app.mcp.utils.validators import safe_format_number
        assert safe_format_number(1000) == '1,000'
        assert safe_format_number(1000000) == '1,000,000'
    
    def test_safe_format_number_none(self):
        """None 입력"""
        from app.mcp.utils.validators import safe_format_number
        assert safe_format_number(None) == 'N/A'
    
    def test_safe_format_number_string(self):
        """문자열 입력"""
        from app.mcp.utils.validators import safe_format_number
        assert safe_format_number('invalid') == 'N/A'
    
    def test_safe_format_number_zero(self):
        """0 입력"""
        from app.mcp.utils.validators import safe_format_number
        assert safe_format_number(0) == '0'
    
    def test_safe_format_number_negative(self):
        """음수 입력"""
        from app.mcp.utils.validators import safe_format_number
        assert safe_format_number(-1000) == '-1,000'


class TestHTTPServerModule:
    """HTTP 서버 모듈 테스트"""
    
    def test_http_app_created(self):
        """HTTP 앱 생성됨"""
        from app.mcp.http_server import app
        assert app is not None
    
    def test_http_app_has_route(self):
        """HTTP 앱에 라우트 존재"""
        from app.mcp.http_server import app
        assert len(app.routes) > 0
    
    def test_http_app_type(self):
        """HTTP 앱 타입 확인"""
        from app.mcp.http_server import app
        assert 'Starlette' in type(app).__name__ or 'ASGI' in type(app).__name__


class TestFastAPIMount:
    """FastAPI MCP 마운트 테스트"""
    
    def test_mcp_mounted_on_fastapi(self):
        """MCP가 FastAPI에 마운트됨"""
        from app.main import app
        
        # Mount된 앱 확인
        mcp_found = False
        for route in app.routes:
            if hasattr(route, 'path') and '/mcp' in route.path:
                mcp_found = True
                break
        
        assert mcp_found, "MCP not mounted on FastAPI"
    
    def test_health_includes_mcp_status(self):
        """Health check에 MCP 상태 포함"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "mcp" in data.get("services", {})


class TestSchemas:
    """Pydantic 스키마 테스트"""
    
    def test_pattern_result_creation(self):
        """PatternResult 생성"""
        from app.mcp.schemas.patterns import PatternResult
        result = PatternResult(id='test', title='Test', tier='S', views=1000)
        assert result.id == 'test'
    
    def test_search_response_creation(self):
        """SearchResponse 생성"""
        from app.mcp.schemas.patterns import SearchResponse, PatternResult, SearchFilters
        response = SearchResponse(
            query='test',
            filters=SearchFilters(),
            count=1,
            results=[PatternResult(id='1', title='T', tier='A', views=100)]
        )
        assert response.count == 1
    
    def test_search_response_serialization(self):
        """SearchResponse JSON 직렬화"""
        from app.mcp.schemas.patterns import SearchResponse, PatternResult, SearchFilters
        response = SearchResponse(
            query='test',
            filters=SearchFilters(),
            count=0,
            results=[]
        )
        json_str = response.model_dump_json()
        assert 'test' in json_str
    
    def test_source_pack_response_creation(self):
        """SourcePackResponse 생성"""
        from app.mcp.schemas.packs import SourcePackResponse
        response = SourcePackResponse(
            name='Test Pack',
            created_at='2025-01-01T00:00:00',
            outlier_count=0,
            sources=[]
        )
        assert response.name == 'Test Pack'


class TestFastMCPFeatures:
    """FastMCP 기능 지원 테스트"""
    
    def test_elicitation_available(self):
        """Elicitation 지원"""
        from fastmcp import Context
        assert hasattr(Context, 'elicit')
    
    def test_sampling_available(self):
        """LLM Sampling 지원"""
        from fastmcp import Context
        assert hasattr(Context, 'sample')
        assert hasattr(Context, 'sample_step')
    
    def test_progress_available(self):
        """Progress 의존성 지원"""
        from fastmcp.dependencies import Progress
        assert Progress is not None
    
    def test_accepted_elicitation_type(self):
        """AcceptedElicitation 타입"""
        from fastmcp.server.context import AcceptedElicitation
        assert AcceptedElicitation is not None
