"""
Komission MCP Server Package
FastMCP 2.14+ 기반 모듈화된 MCP 서버 (MCP 2025-11-25 스펙)

사용법:
    from app.mcp import mcp
    
    if __name__ == "__main__":
        mcp.run()
"""
# 서버 인스턴스 임포트
from app.mcp.server import mcp, get_logger

# Resources 등록
from app.mcp.resources import patterns
from app.mcp.resources import outliers
from app.mcp.resources import director_pack

# Tools 등록
from app.mcp.tools import search
from app.mcp.tools import pack_generator
from app.mcp.tools import vdg_tools
from app.mcp.tools import smart_analysis  # Claude Desktop 호환 데이터 제공

# Prompts 등록
from app.mcp.prompts import recommendation
from app.mcp.prompts import shooting
from app.mcp.prompts import risk

__all__ = ["mcp", "get_logger"]
