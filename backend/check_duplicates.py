
import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def check_duplicates():
    async with async_session_maker() as session:
        try:
            print("Checking for duplicate video_urls in outlier_items...")
            query = text("""
                SELECT video_url, COUNT(*), array_agg(id), array_agg(title), array_agg(external_id), array_agg(source_id)
                FROM outlier_items
                GROUP BY video_url
                HAVING COUNT(*) > 1
            """)
            result = await session.execute(query)
            duplicates = result.fetchall()
            
            if not duplicates:
                print("No duplicates found by video_url.")
            else:
                print(f"Found {len(duplicates)} duplicate groups:")
                for row in duplicates:
                    url, count, ids, titles, ext_ids, source_ids = row
                    print(f"\nURL: {url}")
                    print(f"Count: {count}")
                    for id_, title, ext_id, source_id in zip(ids, titles, ext_ids, source_ids):
                        print(f"  - ID: {id_}")
                        print(f"    Title: {title}")
                        print(f"    ExtID: {ext_id}")
                        print(f"    Source: {source_id}")
                        
        except Exception as e:
            print(f"Error checking duplicates: {e}")

if __name__ == "__main__":
    asyncio.run(check_duplicates())
