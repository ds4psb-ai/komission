
import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def check_sources():
    async with async_session_maker() as session:
        try:
            print("Checking outlier_sources...")
            query = text("SELECT id, name, base_url FROM outlier_sources")
            result = await session.execute(query)
            sources = result.fetchall()
            
            for row in sources:
                id_, name, url = row
                print(f"ID: {id_}, Name: {name}, URL: {url}")
                        
        except Exception as e:
            print(f"Error checking sources: {e}")

if __name__ == "__main__":
    asyncio.run(check_sources())
