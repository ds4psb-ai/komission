import pytest
from unittest.mock import AsyncMock, patch
from app.models import RemixNode, User, NodeLayer
from app.schemas.vdg_v4 import VDGv4

@pytest.mark.asyncio
async def test_analyze_node_pipeline(client, db_session):
    # Setup Admin User
    admin = User(email="AI_admin@test.com", firebase_uid="ai_admin_uid", role="admin")
    db_session.add(admin)
    await db_session.commit() # Commit to generate ID
    
    # Setup Node with Video URL
    node = RemixNode(
        node_id="ai_test_node",
        title="AI Test",
        source_video_url="http://test.com/video.mp4",
        layer=NodeLayer.MASTER,
        created_by=admin.id,
        owner_type="user"
    )
    db_session.add(node)
    await db_session.commit()
    
    # Mock Gemini & Claude
    mock_gemini_res = VDGv4(
        content_id="ai_test_node",
        duration_sec=15.0
    )
    
    mock_claude_res = {
        "title_kr": "점프 챌린지",
        "hook_description": "Jump!",
        "action_steps": ["1", "2"],
        "caption": "Do it",
        "hashtags": ["#Jump"]
    }

    with patch("app.services.gemini_pipeline.gemini_pipeline.analyze_video_v4", new_callable=AsyncMock) as mock_gemini:
        with patch("app.services.claude_korean.claude_planner.generate_scenario", new_callable=AsyncMock) as mock_claude:
            mock_gemini.return_value = mock_gemini_res
            mock_claude.return_value = mock_claude_res
            
            # Login as Admin
            login_data = {"username": "AI_admin@test.com", "password": "pw"}
            token_res = await client.post("/api/v1/auth/token", data=login_data)
            token = token_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Call API
            response = await client.post(f"/api/v1/remix/ai_test_node/analyze", headers=headers)
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["gemini"]["content_id"] == "ai_test_node"
            assert data["claude"]["title_kr"] == "점프 챌린지"
            
            # Check DB persistence
            await db_session.refresh(node)
            assert node.gemini_analysis is not None
            assert node.claude_brief is not None
            assert node.claude_brief["title_kr"] == "점프 챌린지"
            assert node.gemini_analysis["content_id"] == "ai_test_node"
