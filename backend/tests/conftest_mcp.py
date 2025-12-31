"""
MCP 테스트 Fixtures 및 설정
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ===== 테스트용 Mock 데이터 =====

@pytest.fixture
def sample_outlier_id():
    """테스트용 아웃라이어 UUID"""
    return str(uuid4())


@pytest.fixture
def sample_cluster_id():
    """테스트용 클러스터 ID"""
    return "beauty_hook_1234"


@pytest.fixture
def mock_outlier():
    """테스트용 OutlierItem 객체"""
    outlier = MagicMock()
    outlier.id = uuid4()
    outlier.title = "테스트 바이럴 영상"
    outlier.platform = "tiktok"
    outlier.category = "beauty"
    outlier.outlier_tier = "S"
    outlier.outlier_score = 95.0
    outlier.view_count = 1000000
    outlier.like_count = 50000
    outlier.share_count = 10000
    outlier.comment_count = 5000
    outlier.growth_rate = 250.0
    outlier.engagement_rate = 6.5
    outlier.creator_avg_views = 100000
    outlier.promoted_to_node_id = None
    outlier.video_url = "https://tiktok.com/@test/video/123"
    return outlier


@pytest.fixture
def mock_remix_node():
    """테스트용 RemixNode 객체"""
    node = MagicMock()
    node.id = uuid4()
    node.gemini_analysis = {
        "hook_genome": {"hook_type": "question", "duration": 3.0},
        "scenes": [{"scene_type": "intro"}, {"scene_type": "main"}],
        "content_strategy": "교육적 콘텐츠 with 감성 훅"
    }
    return node


@pytest.fixture
def mock_db_session(mock_outlier, mock_remix_node):
    """Mock 데이터베이스 세션"""
    session = AsyncMock()
    
    # execute 결과 mock
    result = MagicMock()
    result.scalar_one_or_none.return_value = mock_outlier
    result.scalars.return_value.all.return_value = [mock_outlier]
    
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    
    return session


@pytest.fixture
def mock_context():
    """Mock MCP Context (LLM Sampling용)"""
    ctx = AsyncMock()
    ctx.sample = AsyncMock(return_value="AI가 생성한 분석 결과입니다. 이 패턴은 뛰어난 성과를 보여줍니다.")
    ctx.elicit = AsyncMock(return_value=MagicMock(data=True))  # 사용자 확인 승인
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.fixture
def mock_context_denied():
    """Mock MCP Context - 사용자 거부"""
    ctx = AsyncMock()
    ctx.elicit = AsyncMock(return_value=None)  # 사용자 거부
    return ctx


# ===== AsyncSessionLocal Mock =====

@pytest.fixture
def patch_async_session(mock_db_session):
    """AsyncSessionLocal을 mock으로 패치"""
    async def mock_session_context():
        return mock_db_session
    
    with patch('app.mcp.tools.search.AsyncSessionLocal') as mock:
        mock.return_value.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock.return_value.__aexit__ = AsyncMock(return_value=None)
        yield mock


# ===== Event Loop 설정 =====

@pytest.fixture(scope="session")
def event_loop():
    """pytest-asyncio용 이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
