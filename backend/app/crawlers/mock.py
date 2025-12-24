import random
import uuid
from datetime import datetime
from typing import List
from app.crawlers.base import BaseCrawler
from app.schemas.evidence import OutlierCrawlItem

class MockCrawler(BaseCrawler):
    """
    Generates fake viral content for testing the pipeline.
    """

    CATEGORIES = ["beauty", "skincare", "makeup", "haircare", "asmr"]
    PLATFORMS = ["tiktok", "instagram", "youtube_shorts"]
    
    TEMPLATES = [
        "Viral Skincare Hack #{n}",
        "POV: You tried the glass skin routine",
        "Stop doing this to your face 🛑",
        "Unbelievable transformation in 7 days",
        "Best drugstore dupe for high-end serum",
        "My dermatologist hates this trick",
        "ASMR Skincare Routine 💦",
        "Get valid results with this one change",
        "Why your makeup looks cakey",
        "Hidden gem found at Sephora"
    ]

    def crawl(self, limit: int = 10, **kwargs) -> List[OutlierCrawlItem]:
        results = []
        for _ in range(limit):
            platform = random.choice(self.PLATFORMS)
            category = random.choice(self.CATEGORIES)
            title = random.choice(self.TEMPLATES).format(n=random.randint(1, 999))
            
            # Generate random viral metrics
            views = random.randint(100_000, 5_000_000)
            growth_rate = f"{random.uniform(1.1, 5.0):.1f}x"
            
            item = OutlierCrawlItem(
                source_name="mock_provider",
                external_id=str(uuid.uuid4()),
                video_url=f"https://www.{platform}.com/video/{uuid.uuid4()}",
                platform=platform,
                category=category,
                title=title,
                thumbnail_url=f"https://via.placeholder.com/150?text={category}",
                view_count=views,
                like_count=int(views * random.uniform(0.05, 0.15)),
                share_count=int(views * random.uniform(0.01, 0.05)),
                growth_rate=growth_rate
            )
            results.append(item)
            
        return results
