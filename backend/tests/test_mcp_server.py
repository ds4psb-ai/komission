"""
MCP Server Tests
Tests for Komission MCP Server (Resources, Tools, Prompts)
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
        """Resources 등록 확인 (5개)"""
        from app.mcp_server import mcp
        resources = list(mcp._resource_manager._templates.keys())
        assert len(resources) == 5
        assert "komission://patterns/{cluster_id}" in resources
        assert "komission://comments/{outlier_id}" in resources
        assert "komission://evidence/{pattern_id}" in resources
        assert "komission://recurrence/{cluster_id}" in resources
        assert "komission://vdg/{outlier_id}" in resources

    @pytest.mark.asyncio
    async def test_tools_registered(self):
        """Tools 등록 확인 (3개)"""
        from app.mcp_server import mcp
        tools = list(mcp._tool_manager._tools.keys())
        assert len(tools) == 3
        assert "search_patterns" in tools
        assert "generate_source_pack" in tools
        assert "reanalyze_vdg" in tools

    @pytest.mark.asyncio
    async def test_prompts_registered(self):
        """Prompts 등록 확인 (3개)"""
        from app.mcp_server import mcp
        prompts = list(mcp._prompt_manager._prompts.keys())
        assert len(prompts) == 3
        assert "explain_recommendation" in prompts
        assert "shooting_guide" in prompts
        assert "risk_summary" in prompts

