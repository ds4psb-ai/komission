import pytest
from datetime import datetime, timedelta
from app.models import O2OLocation, User
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_list_locations(client, db_session: AsyncSession):
    # Setup
    loc = O2OLocation(
        location_id="loc_1",
        place_name="Test Place",
        address="123 Test St",
        lat=37.5,
        lng=127.0,
        campaign_type="visit",
        campaign_title="Visit Test",
        reward_points=100,
        verification_method="gps",
        active_start=datetime.utcnow() - timedelta(days=1),
        active_end=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(loc)
    await db_session.commit()

    response = await client.get("/api/v1/o2o/locations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["place_name"] == "Test Place"

@pytest.mark.asyncio
async def test_verify_location_success(client, db_session: AsyncSession):
    # Setup User & Location
    user = User(email="o2o_user@test.com", firebase_uid="o2o_uid", k_points=0)
    db_session.add(user)
    
    loc = O2OLocation(
        location_id="loc_success",
        place_name="Success Place",
        address="Seoul",
        lat=37.5665,
        lng=126.9780,
        campaign_type="visit",
        campaign_title="Success Campaign",
        reward_points=50,
        verification_method="gps",
        active_start=datetime.utcnow() - timedelta(days=1),
        active_end=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(loc)
    await db_session.commit()
    
    # Login
    login_data = {"username": "o2o_user@test.com", "password": "pw"}
    token_res = await client.post("/api/v1/auth/token", data=login_data)
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verify (Exact location)
    verify_data = {
        "lat": 37.5665,
        "lng": 126.9780,
        "location_id": "loc_success"
    }
    
    res = await client.post("/api/v1/o2o/verify", json=verify_data, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "verified"
    assert res.json()["points_awarded"] == 50
    assert res.json()["total_points"] == 50

@pytest.mark.asyncio
async def test_verify_location_too_far(client, db_session: AsyncSession):
    # Setup User & Location
    user = User(email="far_user@test.com", firebase_uid="far_uid", k_points=0)
    db_session.add(user)
    
    loc = O2OLocation(
        location_id="loc_far",
        place_name="Far Place",
        address="Seoul",
        lat=37.5665,
        lng=126.9780,
        campaign_type="visit",
        campaign_title="Far Campaign",
        reward_points=50,
        verification_method="gps",
        active_start=datetime.utcnow() - timedelta(days=1),
        active_end=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(loc)
    await db_session.commit()
    
    # Login
    login_data = {"username": "far_user@test.com", "password": "pw"}
    token_res = await client.post("/api/v1/auth/token", data=login_data)
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verify (Coordinate far away, e.g. Busan)
    verify_data = {
        "lat": 35.1796,
        "lng": 129.0756,
        "location_id": "loc_far"
    }
    
    res = await client.post("/api/v1/o2o/verify", json=verify_data, headers=headers)
    assert res.status_code == 400
    assert "Too far" in res.json()["detail"]
