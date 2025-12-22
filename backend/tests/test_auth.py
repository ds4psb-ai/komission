import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_login_and_get_me(client: AsyncClient):
    # 1. Login (Auto-create dev user)
    login_data = {
        "username": "testuser@example.com",
        "password": "password"
    }
    response = await client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

    # 2. Get Me
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == "testuser@example.com"
    assert user_data["role"] == "user"
