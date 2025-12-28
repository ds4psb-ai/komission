"""
For You API Tests
Tests for /api/v1/for-you endpoint
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestForYouAPI:
    """For You API 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_for_you_recommendations(self):
        """기본 추천 조회 테스트"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/for-you")
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data
            assert "total_count" in data

    @pytest.mark.asyncio
    async def test_get_for_you_with_platform_filter(self):
        """플랫폼 필터링 테스트"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/for-you?platform=tiktok")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_for_you_detail_not_found(self):
        """단일 추천 상세 조회 - 404"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            fake_id = str(uuid4())
            response = await client.get(f"/api/v1/for-you/{fake_id}")
            assert response.status_code == 404



