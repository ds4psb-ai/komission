#!/bin/bash
# Virlo 크롤링 스크립트 (2025-12-31)
# Usage: ./scripts/run_virlo_bridge.sh [limit] [mode]
#   mode: discover (기본) 또는 bridge

set -e

cd "$(dirname "$0")/.."

# 환경변수 로드
source venv/bin/activate
set -a
source .env
set +a

LIMIT=${1:-50}
MODE=${2:-bridge}

echo "=== Virlo Crawler ==="
echo "Mode: $MODE"
echo "Limit: $LIMIT"
echo "Token: ${VIRLO_ACCESS_TOKEN:0:50}..."
echo ""

if [ "$MODE" == "bridge" ]; then
    echo "Running Virlo → Ops Pipeline Bridge..."
    python -c "
import asyncio
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

from app.services.virlo_scraper import discover_and_enrich_urls

async def main():
    result = await discover_and_enrich_urls(limit=$LIMIT, platform_filter='tiktok')
    print()
    print('=== RESULT ===')
    for k, v in result.items():
        print(f'  {k}: {v}')

asyncio.run(main())
"
else
    echo "Running Virlo Discovery Only..."
    python -m app.services.virlo_scraper $LIMIT discover
fi

echo ""
echo "=== Done ==="
