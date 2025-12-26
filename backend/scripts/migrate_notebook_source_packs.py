"""
Migration: Add notebook_source_packs table
Run: python backend/scripts/migrate_notebook_source_packs.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import AsyncSessionLocal

# Split into separate statements for asyncpg compatibility
MIGRATION_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS notebook_source_packs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        cluster_id VARCHAR(100) NOT NULL,
        pack_type VARCHAR(50) NOT NULL,
        drive_file_id VARCHAR(100) NOT NULL,
        drive_url TEXT,
        source_version VARCHAR(50) DEFAULT 'v1.0',
        entry_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_notebook_source_packs_cluster_id 
        ON notebook_source_packs(cluster_id)
    """,
]


async def run_migration():
    print("🔄 Running migration: notebook_source_packs table...")
    
    async with AsyncSessionLocal() as db:
        try:
            for i, stmt in enumerate(MIGRATION_STATEMENTS, 1):
                print(f"   Executing statement {i}/{len(MIGRATION_STATEMENTS)}...")
                await db.execute(text(stmt))
            await db.commit()
            print("✅ Migration completed: notebook_source_packs table created")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())
