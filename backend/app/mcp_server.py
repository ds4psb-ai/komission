"""
Komission MCP Server - 레거시 호환 래퍼
FastMCP 2.14+ 기반 MCP 서버 구현 (MCP 2025-11-25 스펙)

이 파일은 기존 호환성을 위한 래퍼입니다.
실제 구현은 app.mcp 패키지로 모듈화되어 있습니다.

Resources (읽기 전용):
- komission://patterns/{cluster_id}
- komission://comments/{outlier_id}
- komission://evidence/{pattern_id}
- komission://recurrence/{cluster_id}
- komission://vdg/{outlier_id}
- komission://director-pack/{outlier_id}

Tools (실행):
- search_patterns
- generate_source_pack
- reanalyze_vdg
- smart_pattern_analysis (LLM Sampling)
- ai_batch_analysis (LLM Sampling)

Prompts (템플릿):
- explain_recommendation
- shooting_guide
- risk_summary
"""

# 모듈화된 MCP 패키지에서 모든 것을 임포트
from app.mcp import mcp, get_logger

# 개별 함수도 기존 호환을 위해 export
from app.mcp.resources.patterns import get_pattern, get_recurrence
from app.mcp.resources.outliers import get_comments, get_evidence, get_vdg
from app.mcp.resources.director_pack import get_director_pack
from app.mcp.tools.search import search_patterns
from app.mcp.tools.pack_generator import generate_source_pack
from app.mcp.tools.vdg_tools import reanalyze_vdg
from app.mcp.tools.smart_analysis import smart_pattern_analysis, ai_batch_analysis
from app.mcp.prompts.recommendation import explain_recommendation
from app.mcp.prompts.shooting import shooting_guide
from app.mcp.prompts.risk import risk_summary

# Utils도 export (기존 코드 호환용)
from app.mcp.utils.validators import validate_uuid, safe_format_number
from app.mcp.utils.formatters import format_comments

# 로거
logger = get_logger()

# ==================
# Server Entry Point
# ==================

if __name__ == "__main__":
    # Run as standalone MCP server
    mcp.run()
