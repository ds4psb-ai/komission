import pytest
from datetime import datetime, timedelta
from app.models import RemixNode, EvidenceSnapshot, User, NodeLayer
from app.services.depth_experiments import depth_experiment_service

@pytest.mark.asyncio
async def test_depth2_eligibility(db_session):
    # Setup User
    user = User(email="test_curator@komission.xyz", firebase_uid="test_curator_uid", name="Test Curator", role="curator")
    db_session.add(user)
    await db_session.flush()

    # Setup Parent Node (Old enough - 20 days ago)
    parent = RemixNode(
        node_id="parent_001",
        title="Parent Test Node",
        layer=NodeLayer.MASTER,
        created_by=user.id,
        created_at=datetime.utcnow() - timedelta(days=20),
        # Required fields based on models.py
        is_published=True
    )
    db_session.add(parent)
    await db_session.flush()

    # Add 4 variants (children)
    for i in range(4):
        child = RemixNode(
            node_id=f"var_00{i}",
            title=f"Variant {i}",
            layer=NodeLayer.FORK,
            parent_node_id=parent.id,
            created_by=user.id,
            is_published=True
        )
        db_session.add(child)
    
    # Add Evidence (High confidence, recent)
    snap = EvidenceSnapshot(
        parent_node_id=parent.id,
        confidence=0.85,
        top_mutation_pattern="visual_cut_fast",
        top_mutation_type="visual",
        top_mutation_rate="+15%",
        sample_count=100,
        depth1_summary={"visual": {"visual_cut_fast": {"success_rate": 0.8}}},
        snapshot_date=datetime.utcnow(),
        period="4w"
    )
    db_session.add(snap)
    await db_session.commit()

    # Test Status Check
    status = await depth_experiment_service.get_experiment_status(db_session, "parent_001")
    
    # Debug print if fails
    if not status["ready_for_depth2"]:
        print(f"DEBUG Status: {status}")

    assert status["ready_for_depth2"] is True
    assert status["variants_count"] == 4
    assert status["decision"]["top_mutation_pattern"] == "visual_cut_fast"
    assert status["recommendation"].startswith("Depth2 권장")

    # Test Start Depth2
    plan = await depth_experiment_service.start_depth2_experiment(db_session, "parent_001")
    
    assert "experiment_id" in plan
    assert plan["parent_id"] == "parent_001"
    assert plan["base_pattern"] == "visual_cut_fast"
    assert plan["variants_to_create"] == 3
    # Check refinement axes logic
    assert "refinement_axes" in plan
    assert "transition_style" in plan["refinement_axes"]  # Visual type axes

@pytest.mark.asyncio
async def test_depth2_not_eligible(db_session):
    # Setup User
    user = User(email="test_user@komission.xyz", firebase_uid="test_user_uid", name="Test User")
    db_session.add(user)
    await db_session.flush()

    # Setup Parent Node (Too new - 5 days ago)
    parent = RemixNode(
        node_id="parent_002",
        title="New Parent",
        layer=NodeLayer.MASTER,
        created_by=user.id,
        created_at=datetime.utcnow() - timedelta(days=5),
        is_published=True
    )
    db_session.add(parent)
    await db_session.commit()

    # Test Status Check
    status = await depth_experiment_service.get_experiment_status(db_session, "parent_002")
    
    assert status["ready_for_depth2"] is False
    assert status["days_tracked"] < 14
    assert "계속 추적 중" in status["recommendation"]
