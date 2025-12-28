#!/bin/bash
# TikTok Cookie Refresh Script
# Run this periodically (e.g., cron every 30 mins) to maintain fresh session cookies
#
# Usage:
#   ./scripts/refresh-tiktok-cookies.sh
#
# Cron example (every 30 mins):
#   */30 * * * * /path/to/komission/backend/scripts/refresh-tiktok-cookies.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

# Activate venv if exists
if [ -f "./venv/bin/activate" ]; then
    source ./venv/bin/activate
fi

echo "=== TikTok Cookie Refresh ==="
echo "Time: $(date)"

# Check current cookie status and refresh if needed
python3 -c "
import asyncio
import json
import sys
sys.path.insert(0, '.')

from app.services.comment_extractor import CommentExtractor

async def main():
    extractor = CommentExtractor()
    
    # Check current status
    status = extractor.get_cookie_status()
    print(f'Current status: {status[\"status\"]}')
    
    if status.get('needs_refresh', True):
        print('Refreshing cookies...')
        cookie_path = await extractor._try_export_chrome_cookies()
        if cookie_path:
            # Verify new status
            new_status = extractor.get_cookie_status()
            print(f'New status: {new_status[\"status\"]}')
            print(f'Cookie count: {new_status.get(\"count\", 0)}')
            print(f'Source: {new_status.get(\"source\", \"unknown\")}')
        else:
            print('Failed to export cookies (browser may not be available)')
            sys.exit(1)
    else:
        print(f'Cookies still fresh (age: {status.get(\"age_hours\", 0):.1f} hours)')
        print(f'Cookie count: {status.get(\"count\", 0)}')

asyncio.run(main())
"

echo "=== Done ==="
