"""
Virlo Meme Outliers Seed Data

P2 Roadmap: 실제 클러스터 데이터 입력
Virlo.ai에서 크롤링한 밈 아웃라이어 영상들

Usage:
    python -m app.scripts.seed_meme_outliers
    
Or via API:
    POST /api/v1/outliers/items/bulk
"""
import asyncio
import httpx
from typing import List, Dict, Any


# Virlo에서 수집한 밈 아웃라이어 데이터 (2024-12-30)
VIRLO_MEME_OUTLIERS = [
    {
        "creator": "racinronny",
        "title": "Relatable 'bad days' observation - Gas station POV",
        "view_count": 766800,
        "outlier_score": 5181,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@racinronny",  # Creator page
        "insight": "Uses CapCut editing to trigger immediate identification",
        "hook_pattern": "relatable_pov",
        "success": True
    },
    {
        "creator": "kinggen25",
        "title": "IShowSpeed-style personality clipping",
        "view_count": 918300,
        "outlier_score": 1870,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@kinggen25",
        "insight": "Viral reactions and parasocial connection",
        "hook_pattern": "reaction_clip",
        "success": True
    },
    {
        "creator": "kupahlamar",
        "title": "Dark humor about 'nature of things' + scorpion emoji",
        "view_count": 1400000,
        "outlier_score": 1063,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@kupahlamar",
        "insight": "Relatable meme format featuring dark humor",
        "hook_pattern": "dark_humor",
        "success": True
    },
    {
        "creator": "kadijaconteh_",
        "title": "Corporate/Office life humor - Salary & Interns weaponization",
        "view_count": 839900,
        "outlier_score": 1026,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@kadijaconteh_",
        "insight": "Weaponizing workplace frustrations into viral comedy",
        "hook_pattern": "office_life",
        "success": True
    },
    {
        "creator": "slamaholiccentral",
        "title": "Joey Diaz x Joe Rogan x Absurdist food commentary",
        "view_count": 416600,
        "outlier_score": 272,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@slamaholiccentral",
        "insight": "Combining podcast culture with absurdist humor",
        "hook_pattern": "popup_reference",
        "success": True
    },
    {
        "creator": "jermoza",
        "title": "Skibidi Toilet x Gumball crossover",
        "view_count": 758700,
        "outlier_score": 260,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@jermoza",
        "insight": "Niche internet culture invading mainstream entertainment",
        "hook_pattern": "cultural_crossover",
        "success": True
    },
    # Failed examples for contrast (synthetic based on patterns)
    {
        "creator": "meme_fail_01",
        "title": "Generic meme repost without personalization",
        "view_count": 500,
        "outlier_score": 0.1,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@meme_fail_example",
        "insight": "No original content, pure repost",
        "hook_pattern": "none",
        "success": False
    },
    {
        "creator": "meme_fail_02",
        "title": "Overused meme template with bad timing",
        "view_count": 200,
        "outlier_score": 0.05,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@meme_fail_example2",
        "insight": "Template is stale (T4), execution poor",
        "hook_pattern": "stale_template",
        "success": False
    }
]


async def seed_outliers_via_api(base_url: str = "http://localhost:8000", token: str = None):
    """Seed outliers via API (requires curator auth)."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        results = []
        for outlier in VIRLO_MEME_OUTLIERS:
            try:
                payload = {
                    "video_url": outlier["video_url"],
                    "title": outlier["title"],
                    "platform": outlier["platform"],
                    "category": outlier["category"],
                    "view_count": outlier["view_count"],
                    "source_name": "virlo_meme_crawl"
                }
                
                response = await client.post(
                    f"{base_url}/api/v1/outliers/items/manual",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    results.append({
                        "creator": outlier["creator"],
                        "status": "created",
                        "id": response.json().get("id")
                    })
                else:
                    results.append({
                        "creator": outlier["creator"],
                        "status": "error",
                        "error": response.text
                    })
            except Exception as e:
                results.append({
                    "creator": outlier["creator"],
                    "status": "error",
                    "error": str(e)
                })
        
        return results


def get_cluster_seed_data() -> List[Dict[str, Any]]:
    """
    Get seed data structured for cluster creation.
    
    Returns list ready for ClusterService.create_from_template()
    """
    # Parent: highest outlier score
    parent = max(VIRLO_MEME_OUTLIERS, key=lambda x: x["outlier_score"])
    
    # Kids: all others
    kids = [o for o in VIRLO_MEME_OUTLIERS if o["creator"] != parent["creator"]]
    
    return {
        "cluster_template": "comment_mise",  # Most fitting for meme content
        "parent": {
            "creator": parent["creator"],
            "vdg_id": f"vdg_virlo_{parent['creator']}",
            "content_id": f"tiktok_{parent['creator']}",
            "tier": "S",
            "outlier_score": parent["outlier_score"]
        },
        "kids": [
            {
                "creator": kid["creator"],
                "vdg_id": f"vdg_virlo_{kid['creator']}",
                "content_id": f"tiktok_{kid['creator']}",
                "success": kid["success"],
                "hook_pattern": kid["hook_pattern"]
            }
            for kid in kids
        ]
    }


if __name__ == "__main__":
    print("Virlo Meme Outliers Seed Data")
    print("=" * 50)
    print(f"Total outliers: {len(VIRLO_MEME_OUTLIERS)}")
    print(f"Successful: {sum(1 for o in VIRLO_MEME_OUTLIERS if o['success'])}")
    print(f"Failed: {sum(1 for o in VIRLO_MEME_OUTLIERS if not o['success'])}")
    
    print("\nCluster seed data:")
    data = get_cluster_seed_data()
    print(f"Parent: {data['parent']['creator']} (Score: {data['parent']['outlier_score']}x)")
    print(f"Kids: {len(data['kids'])}")
    for kid in data['kids']:
        status = "✅" if kid['success'] else "❌"
        print(f"  {status} {kid['creator']} ({kid['hook_pattern']})")
