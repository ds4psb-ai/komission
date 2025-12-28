"""
verify_batch_results.py

Verifies that OutlierItems have been analyzed.
"""
import asyncio
import os
import sys
import json
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

from app.config import settings
from app.models import OutlierItem

async def verify():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check counts
        stmt = select(func.count(OutlierItem.id)).where(OutlierItem.analysis_status == 'completed')
        result = await db.execute(stmt)
        count = result.scalar()
        
        print(f"✅ Items with status 'completed': {count}")
        
        # Check content of one item
        stmt = select(OutlierItem).where(OutlierItem.analysis_status == 'completed').limit(1)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        
        if item:
            print(f"\n🔍 Sample Item: {item.title}")
            print(f"   ID: {item.id}")
            print(f"   Analysis Status: {item.analysis_status}")
            print(f"   Outlier Score: {item.outlier_score}")
            
            if item.raw_payload and 'vdg_analysis' in item.raw_payload:
                print("   ✅ VDG Analysis Data Present")
                vdg = item.raw_payload['vdg_analysis']
                print(f"   VDG Pattern: {vdg.get('hook_genome', {}).get('pattern')}")
            else:
                print("   ❌ Missing VDG Analysis Data")
        else:
            print("   ⚠️ No completed items found.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify())
