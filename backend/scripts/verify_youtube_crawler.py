
import logging
from unittest.mock import MagicMock, patch
from app.crawlers.youtube import YouTubeCrawler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_outlier_scoring():
    logger.info("Testing Outlier Scoring Logic...")
    
    crawler = YouTubeCrawler(api_key="mock_key")
    
    # Test Case 1: High views, High engagement -> S Tier
    # Views: 1,000,000
    # Baseline: 10,000
    # Multiplier: 100x
    # Engagement: 10% (0.10)
    # Modifier: 1 + (0.10 - 0.05) = 1.05
    # Score: 100 * 1.05 = 105
    # Expected Tier: B (since 105 >= 100)
    
    score_data = crawler._calculate_outlier_score(
        view_count=1_000_000,
        engagement_rate=0.10,
        baseline_views=10_000
    )
    logger.info(f"Case 1 (1M views, 10k baseline, 10% eng): {score_data}")
    assert score_data["score"] == 105.0
    assert score_data["tier"] == "B"

    # Test Case 2: Mega Viral -> S Tier
    # Views: 5,000,000
    # Baseline: 10,000
    # Multiplier: 500x
    # Engagement: 5%
    # Modifier: 1.0
    # Score: 500
    score_data = crawler._calculate_outlier_score(
        view_count=5_000_000,
        engagement_rate=0.05,
        baseline_views=10_000
    )
    logger.info(f"Case 2 (5M views, 10k baseline, 5% eng): {score_data}")
    assert score_data["score"] == 500.0
    assert score_data["tier"] == "S"

    # Test Case 3: Low Engagement Penalty
    # Views: 1,000,000
    # Baseline: 10,000
    # Multiplier: 100x
    # Engagement: 1% (0.01)
    # Modifier: 1 + (0.01 - 0.05) = 0.96
    # Score: 96
    score_data = crawler._calculate_outlier_score(
        view_count=1_000_000,
        engagement_rate=0.01,
        baseline_views=10_000
    )
    logger.info(f"Case 3 (1M views, 10k baseline, 1% eng): {score_data}")
    assert score_data["score"] == 96.0
    # 96 < 100 so Tier C (>= 50)
    assert score_data["tier"] == "C"

    logger.info("All scoring tests passed!")

def test_crawl_flow():
    logger.info("Testing Crawl Flow with Mocks...")
    
    with patch("app.crawlers.youtube.httpx.Client") as MockClient:
        # Mock client instance
        client_instance = MockClient.return_value
        
        # Mock trending response
        mock_trending_response = MagicMock()
        mock_trending_response.json.return_value = {
            "items": [{"id": "video1"}, {"id": "video2"}]
        }
        mock_trending_response.raise_for_status = MagicMock()
        
        # Mock details response
        mock_details_response = MagicMock()
        mock_details_response.json.return_value = {
            "items": [
                {
                    "id": "video1",
                    "snippet": {
                        "title": "Viral Short #shorts",
                        "channelId": "channel1",
                        "description": "#shorts",
                        "thumbnails": {"high": {"url": "http://thumb"}}
                    },
                    "statistics": {
                        "viewCount": "200000",
                        "likeCount": "20000",
                        "commentCount": "1000"
                    },
                    "contentDetails": {"duration": "PT30S"}
                }
            ]
        }
        
        # Mock baseline response
        mock_baseline_response = MagicMock()
        mock_baseline_response.json.return_value = {
            "items": [{"id": {"videoId": "v1"}}, {"id": {"videoId": "v2"}}]
        }
        
        # Mock baseline video stats response
        mock_baseline_stats_response = MagicMock()
        mock_baseline_stats_response.json.return_value = {
            "items": [
                {"statistics": {"viewCount": "2000"}},
                {"statistics": {"viewCount": "2000"}}
            ]
        }
        
        # Setup side_effects for client.get
        # 1. Trending
        # 2. Details
        # 3. Baseline Search (for channel1)
        # 4. Baseline Stats (for v1, v2)
        client_instance.get.side_effect = [
            mock_trending_response, 
            mock_details_response,
            mock_baseline_response,
            mock_baseline_stats_response
        ]
        
        crawler = YouTubeCrawler(api_key="mock_key")
        items = crawler.crawl(limit=1, category="entertainment")
        
        assert len(items) == 1
        item = items[0]
        logger.info(f"Crawled Item: {item.model_dump()}")
        
        # Verify Baseline was called (views 200k > 100k)
        # Baseline = (2000+2000)/2 = 2000
        # Views = 200,000
        # Multiplier = 100
        # Engagement = 21,000 / 200,000 = 10.5%
        # Modifier = 1 + (0.105 - 0.05) = 1.055
        # Score = 100 * 1.055 = 105.5
        assert item.creator_avg_views == 2000
        assert item.outlier_score == 105.5
        assert item.outlier_tier == "B"
        
        logger.info("Crawl flow test passed!")

if __name__ == "__main__":
    test_outlier_scoring()
    test_crawl_flow()
