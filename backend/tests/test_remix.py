import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_remix_nodes_empty(client: AsyncClient):
    response = await client.get("/api/v1/remix/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_admin_create_node_flow(client: AsyncClient):
    # 1. Login as Admin (in dev, email creates user, need to manually patch role or assume logic)
    # Since our dev login logic auto-creates user with role='user', 
    # we can't easily test admin routes without a way to set role. 
    # For now, we'll verify the 403 Forbidden for non-admin on create endpoint.
    
    # Login
    login_data = {"username": "user@k-meme.com", "password": "pw"}
    token_res = await client.post("/api/v1/auth/token", data=login_data)
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try create node
    node_data = {
        "title": "Test Node",
        "source_video_url": "http://vid.com/1.mp4",
        "platform": "tiktok"
    }
    response = await client.post("/api/v1/remix/", json=node_data, headers=headers)
    
    # Should fail as role='user' by default
    assert response.status_code == 403
