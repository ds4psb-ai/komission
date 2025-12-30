
import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def cleanup_duplicates():
    async with async_session_maker() as session:
        try:
            print("Cleaning up duplicate mock items...")
            
            # 1. Identify duplicates
            # Find video_urls that have > 1 occurrences
            # And delete the ones that belong to the mock source
            
            mock_source_id = 'cea4b31c-78d4-420f-ac42-749634dec27e'
            
            # Check how many items are in this source
            count_query = text("SELECT COUNT(*) FROM outlier_items WHERE source_id = :source_id")
            result = await session.execute(count_query, {"source_id": mock_source_id})
            total_mock_items = result.scalar()
            print(f"Total items in mock source ({mock_source_id}): {total_mock_items}")
            
            # Find duplicates that are in the mock source
            # We want to delete items from 'mock_source_id' ONLY IF there are other items with the same video_url
            
            # Actually, user said "Why are there duplicates?".
            # If the mock source contains duplicates of the real source, we should delete the mock ones.
            # If the mock source has items that are NOT duplicates, maybe keep them? 
            # But the user asked "Was it mock from before?", implying they want it cleaned.
            # Safe bet: Delete ALL items from the mock source if they overlap with anything else.
            
            delete_query = text("""
                DELETE FROM outlier_items
                WHERE source_id = :source_id
                AND video_url IN (
                    SELECT video_url
                    FROM outlier_items
                    GROUP BY video_url
                    HAVING COUNT(*) > 1
                )
            """)
            
            result = await session.execute(delete_query, {"source_id": mock_source_id})
            deleted_count = result.rowcount
            await session.commit()
            
            print(f"Successfully deleted {deleted_count} duplicate mock items.")
                        
        except Exception as e:
            print(f"Error cleaning up: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
