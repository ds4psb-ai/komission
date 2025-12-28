#!/usr/bin/env python3
"""
Export TikTok cookies (including httpOnly sessionid) using a persistent Playwright profile.

Usage:
  PYTHONPATH=/Users/ted/komission/backend venv/bin/python backend/scripts/export_tiktok_cookies.py
"""
import asyncio
import json
import os
import time
from pathlib import Path

from playwright.async_api import async_playwright


def _default_paths() -> tuple[Path, Path]:
    base_dir = Path(__file__).resolve().parents[1]
    profile_dir = Path(os.getenv("TIKTOK_COOKIE_PROFILE_DIR", str(base_dir / ".tiktok_profile")))
    out_path = Path(os.getenv("TIKTOK_COOKIE_OUT", str(base_dir / "tiktok_cookies_auto.json")))
    return profile_dir, out_path


async def export_cookies() -> int:
    profile_dir, out_path = _default_paths()
    timeout_sec = int(os.getenv("TIKTOK_COOKIE_TIMEOUT_SEC", "300"))
    poll_sec = int(os.getenv("TIKTOK_COOKIE_POLL_SEC", "3"))
    channel = os.getenv("TIKTOK_PLAYWRIGHT_CHANNEL", "chrome")

    print(f"[cookie-export] profile_dir={profile_dir}")
    print(f"[cookie-export] output={out_path}")
    print("[cookie-export] Launching browser for TikTok login...")

    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            channel=channel or None,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.tiktok.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        print("[cookie-export] If not logged in, please login in the opened window.")
        print("[cookie-export] Waiting for session cookies (sessionid/sessionid_ss)...")

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            cookies = await context.cookies()
            tiktok_cookies = [
                c for c in cookies if "tiktok" in (c.get("domain") or "").lower()
            ]
            has_session = any(
                c.get("name") in ("sessionid", "sessionid_ss") for c in tiktok_cookies
            )
            if has_session:
                data = {
                    "metadata": {
                        "exported_at": time.time(),
                        "source": f"playwright_persistent:{channel}",
                        "count": len(tiktok_cookies),
                    },
                    "cookies": [
                        {
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": c.get("domain"),
                            "path": c.get("path", "/"),
                            "secure": bool(c.get("secure", False)),
                            "httpOnly": bool(c.get("httpOnly", False)),
                            "sameSite": c.get("sameSite", "Lax"),
                        }
                        for c in tiktok_cookies
                    ],
                }
                out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print(f"[cookie-export] ✅ Saved {len(tiktok_cookies)} cookies")
                await context.close()
                return 0

            await page.wait_for_timeout(poll_sec * 1000)

        print("[cookie-export] ❌ Timed out waiting for session cookies.")
        print("[cookie-export] Keep the browser open and re-run if login is not complete.")
        await context.close()
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(export_cookies()))
