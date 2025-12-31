"""
MCP Prompts - 추천 관련 템플릿
"""
from app.mcp.server import mcp


@mcp.prompt()
def explain_recommendation(pattern_id: str, tier: str, evidence_summary: str) -> str:
    """
    추천 이유 설명 템플릿
    
    Generate an explanation for why a pattern was recommended.
    """
    return f"""
Based on the following evidence, explain why this pattern is recommended:

**Pattern ID**: {pattern_id}
**Tier**: {tier}

**Evidence**:
{evidence_summary}

Please provide:
1. A clear, concise explanation of why this pattern works
2. Key success factors from the evidence
3. Potential risks or considerations
4. Actionable tips for creators
"""
