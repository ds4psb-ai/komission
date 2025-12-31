"""
MCP HTTP Server
Streamable HTTP Transport를 통한 원격 MCP 서버 접근

사용법:
    # 개발 모드
    python -m app.mcp.http_server
    
    # 또는 uvicorn으로 직접 실행
    uvicorn app.mcp.http_server:app --host 0.0.0.0 --port 8080
"""
import os
import logging
from app.mcp import mcp

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MCP-HTTP] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Starlette ASGI 앱 생성
app = mcp.http_app()

# 환경 변수에서 설정 읽기
HOST = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_HTTP_PORT", "8080"))


def main():
    """HTTP 서버 실행"""
    import uvicorn
    
    logger.info(f"Starting Komission MCP HTTP Server on {HOST}:{PORT}")
    logger.info(f"Resources: 6, Tools: 5, Prompts: 3")
    logger.info("Transport: Streamable HTTP (MCP 2025-11-25)")
    
    uvicorn.run(
        "app.mcp.http_server:app",
        host=HOST,
        port=PORT,
        log_level="info",
        reload=os.getenv("MCP_DEBUG", "false").lower() == "true"
    )


if __name__ == "__main__":
    main()
