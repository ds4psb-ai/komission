"""
TikTok Comments Backfill Script
Fills best_comments for TikTok items that have 0 comments
"""
import asyncio
import json
from sqlalchemy import text
from app.database import async_session_maker
from app.services.comment_extractor import extract_best_comments

async def backfill(limit: int = 50):
    async with async_session_maker() as db:
        # Get TikTok items without comments
        result = await db.execute(text('''
            SELECT id, video_url, title FROM outlier_items
            WHERE platform = 'tiktok'
            AND (best_comments IS NULL OR jsonb_array_length(best_comments) = 0)
            ORDER BY view_count DESC
            LIMIT :limit
        '''), {'limit': limit})
        items = result.fetchall()
        
        print(f"📋 Found {len(items)} TikTok items without comments")
        
        success = 0
        failed = 0
        
        for i, item in enumerate(items, 1):
            try:
                comments = await extract_best_comments(item.video_url, 'tiktok', limit=10)
                if comments:
                    await db.execute(text('''
                        UPDATE outlier_items 
                        SET best_comments = :comments
                        WHERE id = :id
                    '''), {'comments': json.dumps(comments), 'id': str(item.id)})
                    success += 1
                    title = item.title[:30] + '...' if item.title and len(item.title) > 30 else item.title
                    print(f'✅ [{i}/{len(items)}] {len(comments)} comments: {title}')
                else:
                    print(f'⚠️ [{i}/{len(items)}] 0 comments: {item.video_url[:50]}...')
                await asyncio.sleep(2)  # Rate limit
            except Exception as e:
                failed += 1
                print(f'❌ [{i}/{len(items)}] Error: {str(e)[:50]}')
                await asyncio.sleep(3)  # Extra delay on error
        
        await db.commit()
        print(f"\n📊 Backfill complete: {success} success, {failed} failed")

if __name__ == "__main__":
    asyncio.run(backfill(50))
