"""
MCP 공통 유틸리티 - 포맷터
"""


def format_comments(comments: list) -> str:
    """Format best comments for display with error handling"""
    if not comments:
        return "No comments available"
    
    lines = []
    for i, c in enumerate(comments[:5], 1):
        try:
            text = str(c.get("text", ""))[:100]
            likes = c.get("likes", 0)
            lang = c.get("lang", "ko")
            lines.append(f'{i}. [{lang}] "{text}..." (👍 {likes})')
        except Exception as e:
            lines.append(f"{i}. [Error parsing comment: {e}]")
    
    return "\n".join(lines)
