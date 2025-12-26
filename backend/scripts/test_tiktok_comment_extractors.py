"""
Compare TikTok comment extraction methods.

Usage:
  python backend/scripts/test_tiktok_comment_extractors.py --url "<tiktok_url>"
  python backend/scripts/test_tiktok_comment_extractors.py --url "<tiktok_url>" --method ytdlp
  python backend/scripts/test_tiktok_comment_extractors.py --url "<tiktok_url>" --method playwright
  python backend/scripts/test_tiktok_comment_extractors.py --url "<tiktok_url>" --method comment_list
"""
import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.services.comment_extractor import CommentExtractor


async def run(url: str, limit: int, method: str) -> None:
    extractor = CommentExtractor()
    comments = await extractor.extract_best_comments(
        url, "tiktok", limit=limit, method=method
    )
    print(f"[{method}] extracted {len(comments)} comments")
    for idx, comment in enumerate(comments, 1):
        text = comment.get("text", "").replace("\n", " ").strip()
        print(f"{idx}. @{comment.get('author', '')} ({comment.get('likes', 0)} likes)")
        print(f"   {text[:160]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test TikTok comment extractors")
    parser.add_argument("--url", required=True, help="TikTok video URL")
    parser.add_argument("--limit", type=int, default=5, help="Number of comments")
    parser.add_argument(
        "--method",
        choices=["auto", "ytdlp", "playwright", "comment_list"],
        default="auto",
        help="Extraction method",
    )
    args = parser.parse_args()

    asyncio.run(run(args.url, args.limit, args.method))


if __name__ == "__main__":
    main()
