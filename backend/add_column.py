
import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def add_column():
    async with async_session_maker() as session:
        try:
            print("Adding campaign_eligible column to outlier_items table...")
            await session.execute(text("ALTER TABLE outlier_items ADD COLUMN IF NOT EXISTS campaign_eligible BOOLEAN DEFAULT FALSE"))
            await session.commit()
            print("Successfully added campaign_eligible column.")
        except Exception as e:
            print(f"Error adding column: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(add_column())
