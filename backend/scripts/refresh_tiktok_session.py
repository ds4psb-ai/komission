#!/usr/bin/env python3
"""
Headful TikTok session refresh for comment/list API.

Usage:
  python backend/scripts/refresh_tiktok_session.py
  python backend/scripts/refresh_tiktok_session.py --url "https://vt.tiktok.com/..." --output /path/to/state.json
"""
from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional

from playwright.async_api import async_playwright


async def refresh_session(
    url: str,
    output: Path,
    user_data_dir: Path,
    channel: Optional[str],
    max_rounds: int,
    wait_ms: int,
) -> None:
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=False,
            channel=channel or None,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ],
            viewport={"width": 1280, "height": 720},
            locale="en-US",
        )

        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        latest: Dict[str, Any] = {"text": None, "headers": None}

        async def handle_response(response) -> None:
            if "api/comment/list" not in response.url:
                return
            try:
                text = await response.text()
                headers = await response.all_headers()
            except Exception:
                return
            latest["text"] = text
            latest["headers"] = headers

        page.on("response", lambda response: asyncio.create_task(handle_response(response)))

        print("\nIf you see a verification slider, please solve it in the browser window.")
        print("Then click the comment icon if comments are not open.")
        print("Waiting for a non-blocked comment/list response...\n")

        for _ in range(max_rounds):
            # Try to open comment panel
            for selector in [
                '[data-e2e="comment-icon"]',
                '[data-e2e="browse-comment"]',
                'button[aria-label*="Comment"]',
                'button:has-text("Comments")',
                'button:has-text("댓글")',
            ]:
                try:
                    locator = page.locator(selector)
                    if await locator.first.is_visible():
                        await locator.first.click()
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Scroll to trigger loading
            try:
                await page.mouse.wheel(0, 1200)
            except Exception:
                pass

            await page.wait_for_timeout(wait_ms)

            text = latest.get("text")
            headers = latest.get("headers") or {}
            if text and not headers.get("bdturing-verify"):
                print("Received non-blocked comment/list response.")
                break

        text = latest.get("text")
        headers = latest.get("headers") or {}
        if not text or headers.get("bdturing-verify"):
            print("Still blocked by bdturing or empty response.")
            print("Keep the browser open and retry manually. Press Ctrl+C to exit.")
            while True:
                await page.wait_for_timeout(10000)
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            await context.storage_state(path=str(output))
            print(f"Saved storage state to: {output}")
            await context.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh TikTok session state (headful)")
    parser.add_argument(
        "--url",
        default=os.getenv("TIKTOK_SESSION_URL", "https://www.tiktok.com"),
        help="TikTok video URL to open",
    )
    parser.add_argument(
        "--output",
        default=os.getenv(
            "TIKTOK_COOKIE_FILE",
            "/Users/ted/komission/.tmp/tiktok_storage_state.json",
        ),
        help="Path to save storage state JSON",
    )
    parser.add_argument(
        "--user-data-dir",
        default=os.getenv(
            "TIKTOK_PLAYWRIGHT_USER_DATA_DIR",
            "/Users/ted/komission/.tmp/tiktok_headful_profile",
        ),
        help="Persistent profile directory for Playwright",
    )
    parser.add_argument(
        "--channel",
        default=os.getenv("TIKTOK_PLAYWRIGHT_CHANNEL", "chrome"),
        help="Playwright channel (chrome/chromium)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=int(os.getenv("TIKTOK_SESSION_ROUNDS", "120")),
        help="Number of retry rounds before waiting indefinitely",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=int(os.getenv("TIKTOK_SESSION_WAIT_MS", "2000")),
        help="Wait time per round in ms",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        refresh_session(
            url=args.url,
            output=Path(args.output),
            user_data_dir=Path(args.user_data_dir),
            channel=args.channel,
            max_rounds=args.rounds,
            wait_ms=args.wait_ms,
        )
    )


if __name__ == "__main__":
    main()
