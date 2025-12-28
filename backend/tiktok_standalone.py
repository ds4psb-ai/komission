"""
TikTok Extraction Standalone Service
DB 없이 TikTok 추출만 테스트하기 위한 경량 서비스
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="TikTok Extractor",
    description="Standalone TikTok metadata + comments extraction service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tiktok-extractor"}


@app.get("/")
async def root():
    return {
        "service": "TikTok Extractor",
        "endpoints": [
            "GET /health",
            "POST /extract?url=<tiktok_url>",
            "POST /metadata?url=<tiktok_url>",
        ]
    }


@app.post("/extract")
async def extract_tiktok(url: str, include_comments: bool = True):
    """
    TikTok 통합 추출 (메타데이터 + 댓글)
    Short URL(vt.tiktok.com 등) 지원을 위해 리디렉션 해소 후 추출
    """
    import httpx
    from app.services.tiktok_extractor import extract_tiktok_complete
    
    # Resolve short URL if needed
    if "vt.tiktok.com" in url or "vm.tiktok.com" in url or "/t/" in url:
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.head(url)
                if resp.status_code == 200:
                    print(f"🔗 Resolved URL: {url} -> {resp.url}")
                    url = str(resp.url)
        except Exception as e:
            print(f"⚠️ Failed to resolve URL: {e}")

    result = await extract_tiktok_complete(url, include_comments)
    return {
        "success": result.get("source") not in ["fetch_error", "unknown"],
        "data": result
    }


@app.post("/metadata")
async def extract_metadata(url: str):
    """
    TikTok 메타데이터만 추출
    """
    from app.services.tiktok_metadata import extract_tiktok_metadata
    
    result = await extract_tiktok_metadata(url)
    return {
        "success": result.get("source") not in ["http_error", "request_error", "fetch_error", "unknown"],
        "data": result
    }


# ========== DEBUG ENDPOINTS ==========

@app.get("/debug/env")
async def debug_env():
    """환경변수 및 Playwright 상태 확인"""
    from pathlib import Path
    
    cookie_files = list(Path("/app").glob("tiktok_cookies*.json"))
    playwright_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "NOT_SET")
    browsers_exist = Path(playwright_path).exists() if playwright_path != "NOT_SET" else False
    
    return {
        "playwright_browsers_path": playwright_path,
        "browsers_dir_exists": browsers_exist,
        "home": os.environ.get("HOME"),
        "cookie_env": os.environ.get("TIKTOK_COOKIE_FILE"),
        "proxy_env": os.environ.get("TIKTOK_PROXY"),
        "cookie_files_found": [str(f) for f in cookie_files],
    }


@app.post("/debug/playwright-html")
async def debug_playwright_html(url: str):
    """Playwright로 HTML 수집 - 실제 추출 경로와 동일하게 테스트"""
    from playwright.async_api import async_playwright
    import base64
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            html = await page.content()
            screenshot = await page.screenshot(full_page=False)
            final_url = page.url
            await browser.close()
            
            return {
                "success": True,
                "final_url": final_url,
                "html_length": len(html),
                "html_preview": html[:3000],
                "screenshot_b64": base64.b64encode(screenshot).decode()[:1000] + "...",
                "contains_captcha": "captcha" in html.lower(),
                "contains_challenge": "challenge" in html.lower(),
                "contains_video_data": "UNIVERSAL_DATA" in html or "SIGI_STATE" in html,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
