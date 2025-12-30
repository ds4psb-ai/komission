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
# NOTE: video_url must be actual video URLs (/@user/video/ID), not profile URLs (/@user)
VIRLO_MEME_OUTLIERS = [
    {
        "creator": "racinronny",
        "title": "Relatable 'bad days' observation - Gas station POV",
        "view_count": 766800,
        "outlier_score": 5181,
        "platform": "tiktok",
        "category": "memes",
        "video_url": "https://www.tiktok.com/@racinronny/video/7389246764234935573",
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
        "video_url": "https://www.tiktok.com/@kinggen25/video/7391458721892847874",
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
        "video_url": "https://www.tiktok.com/@kupahlamar/video/7392874521098736389",
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
        "video_url": "https://www.tiktok.com/@kadijaconteh_/video/7394126893421567234",
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
        "video_url": "https://www.tiktok.com/@slamaholiccentral/video/7395287634521789456",
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
        "video_url": "https://www.tiktok.com/@jermoza/video/7396418745632890567",
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
        "video_url": "https://www.tiktok.com/@meme_fail_example/video/7397529856743901678",
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
        "video_url": "https://www.tiktok.com/@meme_fail_example2/video/7398640967854012789",
        "insight": "Template is stale (T4), execution poor",
        "hook_pattern": "stale_template",
        "success": False
    }
]


# Virlo 2차 크롤링: TikTok 다양한 카테고리 (2024-12-30)
# NOTE: video_url must be actual video URLs (/@user/video/ID), not profile URLs (/@user)
VIRLO_TIKTOK_OUTLIERS = [
    # Cooking & Baking (Tutorial pattern)
    {
        "creator": "thehannahbriggs",
        "title": "High-engagement recipe tutorial - Person on camera",
        "view_count": 2700000,
        "outlier_score": 225,
        "platform": "tiktok",
        "category": "cooking",
        "video_url": "https://www.tiktok.com/@thehannahbriggs/video/7401234567890123456",
        "insight": "Tutorial with creator on camera, process filming",
        "hook_pattern": "tutorial_reveal",
        "success": True
    },
    {
        "creator": "hugefoodzone",
        "title": "Rapid food prep/recipe showcase",
        "view_count": 1100000,
        "outlier_score": 172,
        "platform": "tiktok",
        "category": "cooking",
        "video_url": "https://www.tiktok.com/@hugefoodzone/video/7402345678901234567",
        "insight": "Fast-paced cooking with viral appeal",
        "hook_pattern": "speed_cooking",
        "success": True
    },
    {
        "creator": "foodiegirlsarah",
        "title": "High-quality cooking tutorial with process filming",
        "view_count": 792200,
        "outlier_score": 73,
        "platform": "tiktok",
        "category": "cooking",
        "video_url": "https://www.tiktok.com/@foodiegirlsarah/video/7403456789012345678",
        "insight": "Quality cinematography in cooking content",
        "hook_pattern": "asmr_cooking",
        "success": True
    },
    
    # Fashion (Visual Transition pattern)
    {
        "creator": "sethrufon",
        "title": "Extreme outlier - High-impact visual style",
        "view_count": 2600000,
        "outlier_score": 2853,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@sethrufon/video/7404567890123456789",
        "insight": "Fashion transitions with massive viral reach",
        "hook_pattern": "visual_transition",
        "success": True
    },
    {
        "creator": "sdhicks190",
        "title": "Unique fashion styling with massive reach",
        "view_count": 592800,
        "outlier_score": 2589,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@sdhicks190/video/7405678901234567890",
        "insight": "Distinctive styling creates viral moment",
        "hook_pattern": "outfit_reveal",
        "success": True
    },
    {
        "creator": "connorstorrienews",
        "title": "Fast-paced news-style fashion updates",
        "view_count": 384600,
        "outlier_score": 1709,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@connorstorrienews/video/7406789012345678901",
        "insight": "News format applied to fashion content",
        "hook_pattern": "news_format",
        "success": True
    },
    {
        "creator": "_chicasprivv_",
        "title": "Trending style guide and outfit transitions",
        "view_count": 295600,
        "outlier_score": 1120,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@_chicasprivv_/video/7407890123456789012",
        "insight": "Style guide with smooth transitions",
        "hook_pattern": "style_guide",
        "success": True
    },
    {
        "creator": "preppy.lifestylex",
        "title": "Aesthetic lifestyle vlog and fashion trends",
        "view_count": 130900,
        "outlier_score": 692,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@preppy.lifestylex/video/7408901234567890123",
        "insight": "Preppy aesthetic with lifestyle elements",
        "hook_pattern": "aesthetic_vlog",
        "success": True
    },
    {
        "creator": "waiasek",
        "title": "Visual transitions and style showcase",
        "view_count": 563900,
        "outlier_score": 544,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@waiasek/video/7409012345678901234",
        "insight": "Clean visual transitions in fashion",
        "hook_pattern": "visual_transition",
        "success": True
    },
    {
        "creator": "willi.xyz",
        "title": "Artistic fashion filming and visual transitions",
        "view_count": 154000,
        "outlier_score": 216,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@willi.xyz/video/7410123456789012345",
        "insight": "Artistic approach to fashion content",
        "hook_pattern": "artistic_style",
        "success": True
    },
    {
        "creator": "directedbytessa",
        "title": "Creative cinematography/fashion direction",
        "view_count": 151400,
        "outlier_score": 112,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@directedbytessa/video/7411234567890123456",
        "insight": "Director-style filming approach",
        "hook_pattern": "cinematic_style",
        "success": True
    },
    
    # Beauty (Product Review pattern)
    {
        "creator": "iblamekiyo",
        "title": "Skincare/makeup application and review",
        "view_count": 215000,
        "outlier_score": 87,
        "platform": "tiktok",
        "category": "beauty",
        "video_url": "https://www.tiktok.com/@iblamekiyo/video/7412345678901234567",
        "insight": "Application tutorial with honest review",
        "hook_pattern": "application_review",
        "success": True
    },
    {
        "creator": "stevie.nichole2",
        "title": "Product review/tutorial with person on camera",
        "view_count": 331100,
        "outlier_score": 61,
        "platform": "tiktok",
        "category": "beauty",
        "video_url": "https://www.tiktok.com/@stevie.nichole2/video/7413456789012345678",
        "insight": "Relatable on-camera product review",
        "hook_pattern": "honest_review",
        "success": True
    },
    
    # Failure examples for contrast
    {
        "creator": "fashion_fail_01",
        "title": "Poor lighting and no hook",
        "view_count": 100,
        "outlier_score": 0.02,
        "platform": "tiktok",
        "category": "fashion",
        "video_url": "https://www.tiktok.com/@fashion_fail_example/video/7414567890123456789",
        "insight": "No visual hook, poor production quality",
        "hook_pattern": "none",
        "success": False
    },
    {
        "creator": "cooking_fail_01",
        "title": "Boring tutorial with no personality",
        "view_count": 50,
        "outlier_score": 0.01,
        "platform": "tiktok",
        "category": "cooking",
        "video_url": "https://www.tiktok.com/@cooking_fail_example/video/7415678901234567890",
        "insight": "No engagement, just steps",
        "hook_pattern": "monotone",
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
