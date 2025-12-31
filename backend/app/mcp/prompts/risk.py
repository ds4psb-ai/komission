"""
MCP Prompts - 리스크 분석 템플릿
"""
from app.mcp.server import mcp


@mcp.prompt()
def risk_summary(pattern_id: str, risk_tags: str, comments_analysis: str) -> str:
    """
    리스크 정리 템플릿
    
    Generate a risk assessment for a pattern.
    """
    return f"""
Analyze the risks for the following pattern:

**Pattern ID**: {pattern_id}
**Known Risk Tags**: {risk_tags}
**Comments Analysis**: {comments_analysis}

Please provide:
1. Risk level assessment (Low/Medium/High)
2. Specific risks identified
3. Mitigation strategies
4. Creator recommendations
"""
