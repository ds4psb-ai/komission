import pytest
from unittest.mock import AsyncMock, patch
from app.services.cache import RedisCache

@pytest.fixture
def mock_redis():
    with patch("redis.asyncio.Redis", new_callable=AsyncMock) as mock:
        yield mock

@pytest.mark.asyncio
async def test_redis_cache_operations(mock_redis):
    # Setup
    cache_service = RedisCache()
    cache_service._client = mock_redis
    
    # Test set/get
    mock_redis.get.return_value = "test_value"
    val = await cache_service.get("key")
    assert val == "test_value"
    mock_redis.get.assert_called_with("key")
    
    await cache_service.set("key", "value")
    mock_redis.setex.assert_called_with("key", 3600, "value")

@pytest.mark.asyncio
async def test_quota_check(mock_redis):
    cache_service = RedisCache()
    cache_service._client = mock_redis
    
    # Case 1: Under limit
    mock_redis.get.return_value = "5" # Current usage
    mock_redis.incr.return_value = 6
    
    result = await cache_service.check_user_quota("user1", daily_limit=10)
    assert result["allowed"] is True
    assert result["remaining"] == 4
    
    # Case 2: Over limit
    mock_redis.get.return_value = "10"
    result = await cache_service.check_user_quota("user1", daily_limit=10)
    assert result["allowed"] is False
    assert result["remaining"] == 0

@pytest.mark.asyncio
async def test_gemini_cache(mock_redis):
    cache_service = RedisCache()
    cache_service._client = mock_redis
    
    analysis_data = {"bpm": 120}
    # Test caching (json serialization)
    await cache_service.cache_gemini_analysis("http://vid", analysis_data)
    # Verify setex called with json string
    args = mock_redis.setex.call_args[0]
    assert args[0] == "gemini:http://vid"
    assert '"bpm": 120' in args[2]
