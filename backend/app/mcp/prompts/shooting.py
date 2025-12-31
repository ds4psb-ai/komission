"""
MCP Prompts - 촬영 가이드 템플릿
"""
from app.mcp.server import mcp


@mcp.prompt()
def shooting_guide(pattern_summary: str, signature: str, platform: str) -> str:
    """
    촬영 가이드 요약 템플릿
    
    Generate a shooting guide for recreating a pattern.
    """
    return f"""
Create a shooting guide for the following pattern:

**Pattern**: {pattern_summary}
**Signature**: {signature}
**Platform**: {platform}

Please provide:
1. Step-by-step shooting instructions
2. Key timing and transition tips
3. Audio/music recommendations
4. Common mistakes to avoid
5. Equipment suggestions (mobile-friendly)
"""
