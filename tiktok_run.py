import asyncio
import json

from app.services.tiktok_extractor import extract_tiktok_complete

URL = "https://www.tiktok.com/@haircutsalon27/video/7585084792698342686"

async def main():
    result = await extract_tiktok_complete(URL, include_comments=True)
    output = {
        "comments": len(result.get("top_comments", [])),
        "source": result.get("source"),
        "sample_comments": result.get("top_comments", [])[:3],
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
