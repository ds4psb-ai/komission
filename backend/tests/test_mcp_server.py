"""
MCP Server Tests (Legacy Compatibility)
기존 테스트 파일을 새 MCP 구조에 맞게 업데이트
"""
import pytest


class TestMCPServer:
    """MCP Server 등록 테스트"""

    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self):
        """MCP 서버 초기화 테스트"""
        from app.mcp_server import mcp
        assert mcp.name == "Komission"
        
    @pytest.mark.asyncio
    async def test_resources_registered(self):
        """Resources 등록 확인 (6개)"""
        from app.mcp_server import mcp
        resources = list(mcp._resource_manager._templates.keys())
        assert len(resources) == 6  # 기존 5개 + director-pack 1개
        # URI 형식 확인 (정확한 key 포맷은 FastMCP 버전에 따라 다름)
        resource_uris = [str(r) for r in resources]
        assert any('patterns' in r for r in resource_uris)
        assert any('comments' in r for r in resource_uris)
        assert any('evidence' in r for r in resource_uris)
        assert any('recurrence' in r for r in resource_uris)
        assert any('vdg' in r for r in resource_uris)
        assert any('director-pack' in r for r in resource_uris)

    @pytest.mark.asyncio
    async def test_tools_registered(self):
        """Tools 등록 확인 (6개)"""
        from app.mcp_server import mcp
        tools = list(mcp._tool_manager._tools.keys())
        assert len(tools) == 6  # 기존 3개 + 스마트 분석 3개
        assert "search_patterns" in tools
        assert "generate_source_pack" in tools
        assert "reanalyze_vdg" in tools
        assert "smart_pattern_analysis" in tools
        assert "ai_batch_analysis" in tools
        assert "get_pattern_performance" in tools

    @pytest.mark.asyncio
    async def test_prompts_registered(self):
        """Prompts 등록 확인 (3개)"""
        from app.mcp_server import mcp
        prompts = list(mcp._prompt_manager._prompts.keys())
        assert len(prompts) == 3
        assert "explain_recommendation" in prompts
        assert "shooting_guide" in prompts
        assert "risk_summary" in prompts
