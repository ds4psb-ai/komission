from typing import Dict, Type
from app.crawlers.base import BaseCrawler
from app.crawlers.mock import MockCrawler

class CrawlerFactory:
    """
    Factory to create crawler instances by name.
    """
    
    _registry: Dict[str, Type[BaseCrawler]] = {
        "mock": MockCrawler,
        # "tiktok": TikTokCrawler, # Future
        # "instagram": InstagramCrawler, # Future
    }

    @classmethod
    def create(cls, source_name: str) -> BaseCrawler:
        crawler_cls = cls._registry.get(source_name.lower())
        if not crawler_cls:
            raise ValueError(f"Unknown crawler source: {source_name}. Available: {list(cls._registry.keys())}")
        return crawler_cls()
