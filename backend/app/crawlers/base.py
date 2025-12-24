from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.evidence import OutlierCrawlItem

class BaseCrawler(ABC):
    """
    Abstract base class for Outlier Crawlers.
    Responsibilities:
    - Fetch content from external source
    - Normalize data into OutlierCrawlItem objects
    """

    @abstractmethod
    def crawl(self, limit: int = 10, **kwargs) -> List[OutlierCrawlItem]:
        """
        Crawl sources and return a list of normalized outlier items.
        """
        pass
