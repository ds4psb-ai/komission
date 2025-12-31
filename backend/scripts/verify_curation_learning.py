#!/usr/bin/env python
"""
Curation Learning Verification Script (Local Development Only)

Usage:
    python scripts/verify_curation_learning.py [--allow-delete]

Safety:
    - Uses DATABASE_URL from environment (falls back to local dev only)
    - Will NOT delete rules unless --allow-delete flag is passed
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import CurationRule
from app.services.curation_service import learn_curation_rules_from_decisions, find_matching_rules

# Get DATABASE_URL from environment or use local dev default
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://kmeme_user:kmeme_password@localhost:5432/kmeme_db"
)

# Prevent accidental execution against production
if "production" in DATABASE_URL.lower() or "prod" in DATABASE_URL.lower():
    print("❌ ABORT: This script should not run against production databases!")
    sys.exit(1)


async def verify_system(allow_delete: bool = False):
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        if allow_delete:
            print("🧹 Cleaning up old rules (--allow-delete flag detected)...")
            await db.execute(text("DELETE FROM curation_rules"))
            await db.commit()
        else:
            print("ℹ️  Skipping rule deletion (use --allow-delete to enable)")
        
        # Check if we have decisions
        count = await db.execute(text("SELECT count(*) FROM curation_decisions"))
        count = count.scalar()
        print(f"📊 Found {count} decisions in database")
        
        if count < 5:
            print("⚠️ Not enough decisions for learning. Seed data first.")
            return
        
        print("\n🧠 1. Testing Rule Learning...")
        result = await learn_curation_rules_from_decisions(
            db, 
            min_samples=5,  # Lower threshold for testing
            min_support_ratio=0.5,
            dry_run=False
        )
        print(f"✅ Learning Result: {result['created']} created, {result['updated']} updated.")
        
        # Verify Rules
        rules = await db.execute(select(CurationRule))
        rules = rules.scalars().all()
        for r in rules:
            acc = r.accuracy if r.accuracy is not None else 0.0
            print(f"   Rule: {r.rule_name} | Acc: {acc:.2f} | {r.conditions}")

        print("\n🔮 2. Testing Rule Matching (P2)...")
        # Test feature matching against learned rules
        test_features = {"category": "news", "outlier_score": 200, "platform": "unknown"}
        matches = await find_matching_rules(db, test_features)
        
        if matches:
            print(f"✅ Match Success! {matches[0].rule_name} -> {matches[0].rule_type}")
        else:
            print("❌ No matching rules found for test features.")
            print(f"   Test features: {test_features}")

        print("\n✅ Verification complete.")


if __name__ == "__main__":
    allow_delete = "--allow-delete" in sys.argv
    asyncio.run(verify_system(allow_delete=allow_delete))
