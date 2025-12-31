"""
MCP Smart Analysis 도구 테스트
실제 DB 데이터 연동 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSmartPatternAnalysis:
    """smart_pattern_analysis 도구 테스트"""
    
    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_error(self):
        """잘못된 UUID 형식"""
        from app.mcp.tools.smart_analysis import smart_pattern_analysis
        
        tool = smart_pattern_analysis
        result = await tool.fn(outlier_id="not-a-uuid")
        
        assert "Error" in result or "Invalid" in result
    
    @pytest.mark.asyncio
    async def test_not_found_returns_error(self):
        """존재하지 않는 아웃라이어"""
        from app.mcp.tools.smart_analysis import smart_pattern_analysis
        
        with patch('app.mcp.tools.smart_analysis.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=result_mock)
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            tool = smart_pattern_analysis
            result = await tool.fn(
                outlier_id="00000000-0000-0000-0000-000000000000"
            )
            
            assert "not found" in result.lower() or "Error" in result
    
    @pytest.mark.asyncio
    async def test_returns_structured_data(self):
        """구조화된 데이터 반환"""
        from app.mcp.tools.smart_analysis import smart_pattern_analysis
        
        mock_outlier = MagicMock()
        mock_outlier.id = "test-uuid"
        mock_outlier.title = "테스트 패턴"
        mock_outlier.platform = "tiktok"
        mock_outlier.category = "beauty"
        mock_outlier.outlier_tier = "S"
        mock_outlier.outlier_score = 95.0
        mock_outlier.view_count = 100000
        mock_outlier.like_count = 5000
        mock_outlier.share_count = 1000
        mock_outlier.growth_rate = "150%"
        mock_outlier.engagement_rate = 5.0
        mock_outlier.creator_avg_views = 10000
        mock_outlier.video_url = "https://example.com"
        mock_outlier.promoted_to_node_id = None
        
        with patch('app.mcp.tools.smart_analysis.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_outlier
            mock_db.execute = AsyncMock(return_value=result_mock)
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            tool = smart_pattern_analysis
            result = await tool.fn(
                outlier_id="aef4a444-cc8f-4e96-b555-38f7ef3bc3db"
            )
            
            # 구조화된 데이터 확인
            assert "패턴 분석 데이터" in result
            assert "테스트 패턴" in result
            assert "tiktok" in result
            assert "S" in result


class TestAIBatchAnalysis:
    """ai_batch_analysis 도구 테스트"""
    
    @pytest.mark.asyncio
    async def test_minimum_two_outliers(self):
        """최소 2개 아웃라이어 필요"""
        from app.mcp.tools.smart_analysis import ai_batch_analysis
        
        tool = ai_batch_analysis
        result = await tool.fn(
            outlier_ids=["00000000-0000-0000-0000-000000000001"],
            focus="trends"
        )
        
        assert "2" in result or "Error" in result
    
    @pytest.mark.asyncio
    async def test_maximum_ten_outliers(self):
        """최대 10개 제한"""
        from app.mcp.tools.smart_analysis import ai_batch_analysis
        
        tool = ai_batch_analysis
        result = await tool.fn(
            outlier_ids=[f"00000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(11)],
            focus="trends"
        )
        
        assert "10" in result or "Error" in result


class TestGetPatternPerformance:
    """get_pattern_performance 도구 테스트"""
    
    @pytest.mark.asyncio
    async def test_invalid_uuid(self):
        """잘못된 UUID"""
        from app.mcp.tools.smart_analysis import get_pattern_performance
        
        tool = get_pattern_performance
        result = await tool.fn(outlier_id="invalid")
        
        assert "Invalid" in result or "Error" in result
    
    @pytest.mark.asyncio
    async def test_returns_performance_table(self):
        """성과 테이블 반환"""
        from app.mcp.tools.smart_analysis import get_pattern_performance
        
        mock_outlier = MagicMock()
        mock_outlier.title = "테스트"
        mock_outlier.view_count = 50000
        mock_outlier.growth_rate = "200%"
        mock_outlier.engagement_rate = 3.5
        mock_outlier.creator_avg_views = 5000
        mock_outlier.outlier_tier = "A"
        mock_outlier.outlier_score = 80.0
        
        with patch('app.mcp.tools.smart_analysis.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_outlier
            mock_db.execute = AsyncMock(return_value=result_mock)
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            tool = get_pattern_performance
            result = await tool.fn(
                outlier_id="aef4a444-cc8f-4e96-b555-38f7ef3bc3db"
            )
            
            assert "성과 데이터" in result
            assert "지표" in result
            assert "평가" in result


class TestSafeFloatHandling:
    """타입 안전 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_handles_string_growth_rate(self):
        """문자열 growth_rate 처리"""
        from app.mcp.tools.smart_analysis import get_pattern_performance
        
        mock_outlier = MagicMock()
        mock_outlier.title = "테스트"
        mock_outlier.view_count = 50000
        mock_outlier.growth_rate = "1302x outlier"  # 문자열
        mock_outlier.engagement_rate = None
        mock_outlier.creator_avg_views = 5000
        mock_outlier.outlier_tier = "S"
        mock_outlier.outlier_score = 95.0
        
        with patch('app.mcp.tools.smart_analysis.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_outlier
            mock_db.execute = AsyncMock(return_value=result_mock)
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            tool = get_pattern_performance
            result = await tool.fn(
                outlier_id="aef4a444-cc8f-4e96-b555-38f7ef3bc3db"
            )
            
            # 에러 없이 결과 반환 (문자열에서 숫자 추출)
            assert "Error" not in result
            assert "1302" in result
