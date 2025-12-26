import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from sqlalchemy import select
from app.services.bandit_policy import batch_updater
from app.models import TemplateSeed, TemplateVersion, RemixNode, EvidenceSnapshot

# Mock data
MOCK_CUSTOMIZATION_PATTERNS = {
    "duration": {
        "change_count": 10,
        "sample_changes": [
            {"old": 1.5, "new": 0.5},
            {"old": 1.5, "new": 0.5},
            {"old": 1.5, "new": 0.5},
            {"old": 1.5, "new": 0.5},
            {"old": 1.5, "new": 0.5}
        ]
    }
}

@pytest.mark.asyncio
async def test_update_template_defaults_with_customization(db_session):
    """
    Test that update_template_defaults:
    1. Detects strong customization signals
    2. Updates TemplateSeed default values
    3. Creates TemplateVersion history
    """
    # 1. Setup: Create a TemplateSeed that uses 'duration'
    seed = TemplateSeed(
        seed_id="seed_test_001",
        template_type="capsule",
        prompt_version="1.0",
        seed_json={
            "duration": 1.5,
            "style": "cinematic"
        }
    )
    db_session.add(seed)
    await db_session.commit()
    await db_session.refresh(seed)
    
    # 2. Mock 'get_customization_patterns' to return strong signal
    with patch("app.routers.template_customization.get_customization_patterns", return_value=MOCK_CUSTOMIZATION_PATTERNS):
        
        # 3. Run Batch Update
        result = await batch_updater.update_template_defaults(db_session)
        
        # 4. Verify Results
        assert "rl_updates" in result
        updates = result["rl_updates"]
        assert len(updates) > 0
        
        update = updates[0]
        assert update["field"] == "duration"
        assert update["old"] == 1.5
        assert update["new"] == 0.5
        
        # 5. Verify DB updates
        await db_session.flush()
        # Reload seed
        await db_session.refresh(seed)
        assert seed.seed_json["duration"] == 0.5  # Should be updated
        
        # Verify Version History
        versions = await db_session.execute(
            select(TemplateVersion).where(TemplateVersion.seed_id == seed.id)
        )
        version_history = versions.scalars().all()
        assert len(version_history) == 1
        assert version_history[0].change_type == "rl_update"
        assert "duration" in version_history[0].change_reason
        assert version_history[0].template_json["duration"] == 0.5

@pytest.mark.asyncio
async def test_update_template_defaults_no_signal(db_session):
    """Test that low-frequency signals do NOT trigger updates"""
    # Setup
    seed = TemplateSeed(
        seed_id="seed_test_002",
        template_type="capsule",
        seed_json={"duration": 1.5}
    )
    db_session.add(seed)
    await db_session.commit()
    
    # Mock WEAK signal (count=2 < 5)
    weak_signal = {
        "duration": {
            "change_count": 2,
            "sample_changes": [{"old": 1.5, "new": 0.5}]
        }
    }
    
    with patch("app.routers.template_customization.get_customization_patterns", return_value=weak_signal):
        result = await batch_updater.update_template_defaults(db_session)
        
        assert len(result["rl_updates"]) == 0
        
        # Verify no DB changes
        await db_session.refresh(seed)
        assert seed.seed_json["duration"] == 1.5
