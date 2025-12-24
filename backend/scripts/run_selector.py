import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.services.sheet_manager import SheetManager
from app.services.outlier_selector import OutlierSelector


async def main_async():
    print("Running Outlier Selector...")
    manager = SheetManager()
    selector = OutlierSelector(manager)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        updated = await selector.process_pending_outliers(db)
        await db.commit()

    await engine.dispose()
    print(f"Selector run complete. Updated {updated} outliers.")


def main():
    try:
        asyncio.run(main_async())
    except Exception as e:
        print(f"Error running selector: {e}")


if __name__ == "__main__":
    main()
