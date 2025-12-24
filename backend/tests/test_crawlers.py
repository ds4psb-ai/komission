
import pytest
from app.crawlers.factory import CrawlerFactory
from app.crawlers.mock import MockCrawler
from app.schemas.evidence import OutlierCrawlItem

def test_crawler_factory_mock():
    crawler = CrawlerFactory.create("mock")
    assert isinstance(crawler, MockCrawler)

def test_crawler_factory_invalid():
    with pytest.raises(ValueError):
        CrawlerFactory.create("unknown_source")

def test_mock_crawler_crawl():
    crawler = MockCrawler()
    items = crawler.crawl(limit=5)
    assert len(items) == 5
    for item in items:
        assert isinstance(item, OutlierCrawlItem)
        assert item.source_name == "mock_provider"
        assert item.platform in MockCrawler.PLATFORMS
        assert item.view_count >= 100_000
        assert item.growth_rate.endswith("x")
