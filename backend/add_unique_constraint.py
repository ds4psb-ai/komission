
import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def add_unique_constraint():
    async with async_session_maker() as session:
        try:
            print("Adding UNIQUE constraint to video_url in outlier_items...")
            # First check if constraint already exists
            check_query = text("""
                SELECT COUNT(*) FROM pg_constraint 
                WHERE conname = 'outlier_items_video_url_key'
            """)
            result = await session.execute(check_query)
            if result.scalar() > 0:
                print("UNIQUE constraint already exists.")
                return
            
            # Add index first (for performance)
            await session.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_outlier_items_video_url ON outlier_items(video_url)"
            ))
            
            # Add unique constraint
            await session.execute(text(
                "ALTER TABLE outlier_items ADD CONSTRAINT outlier_items_video_url_key UNIQUE (video_url)"
            ))
            await session.commit()
            print("Successfully added UNIQUE constraint to video_url.")
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(add_unique_constraint())
