# Platform Extraction Pipeline Guide

> 마지막 업데이트: 2026-01-04

TikTok, YouTube, Instagram에서 메타데이터와 댓글을 추출하는 파이프라인 가이드.

---

## 현재 상태 (2026-01-04 검증)

| Platform | Metadata | upload_date | Comments | Status |
|----------|----------|-------------|----------|--------|
| **YouTube** | ✅ API | ✅ 99.8% | ✅ API | 🟢 Ready |
| **TikTok** | ✅ yt-dlp | ✅ 100% | ✅ API (쿠키) | 🟢 Ready |
| **Instagram** | ⚠️ yt-dlp | ❌ 0% | ⚠️ Limited | 🟡 Partial |

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      Outlier Ingestion                          │
│                                                                 │
│  Virlo Crawler → outlier_items → Promote → VDG Pipeline        │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
    ┌────────────┐     ┌────────────┐     ┌────────────┐
    │  YouTube   │     │  TikTok    │     │ Instagram  │
    └────────────┘     └────────────┘     └────────────┘
           │                  │                  │
    ┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐
    │ Metadata:   │    │ Metadata:   │    │ Metadata:   │
    │ Data API v3 │    │ yt-dlp      │    │ yt-dlp      │
    ├─────────────┤    ├─────────────┤    ├─────────────┤
    │ Comments:   │    │ Comments:   │    │ Comments:   │
    │ Data API v3 │    │ API+Cookie  │    │ Limited     │
    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## YouTube

### 메타데이터 추출

**파일**: `backend/app/services/video_downloader.py`

| Method | Source | Fields |
|--------|--------|--------|
| Primary | YouTube Data API v3 | id, title, duration, view_count, like_count, upload_date, thumbnail |
| Fallback | yt-dlp | 동일 (API 키 없을 때) |

```python
# API 호출 (line 409-480)
async def _fetch_youtube_metadata_api(self, video_id: str, api_key: str):
    # GET https://www.googleapis.com/youtube/v3/videos
    # ?part=snippet,contentDetails,statistics&id={video_id}
```

**환경변수**: `YOUTUBE_API_KEY`

### 댓글 추출

**파일**: `backend/app/services/comment_extractor.py`

```python
async def _extract_youtube_api(self, video_url: str, limit: int):
    # GET https://www.googleapis.com/youtube/v3/commentThreads
    # ?part=snippet&videoId={video_id}&order=relevance
```

**테스트** (2026-01-04):
```
✅ Extracted: 3 comments
  1. [en] Gonna flag this for nudity... (539,624 likes)
```

---

## TikTok

### 메타데이터 추출

**파일**: `backend/app/services/video_downloader.py`, `tiktok_extractor.py`

| Method | Source | Success Rate |
|--------|--------|--------------|
| Primary | yt-dlp + Chrome cookies | ~95% |
| Fallback | Playwright DOM | ~80% |

**환경변수**:
- `TIKTOK_COOKIE_FILE`: 쿠키 파일 경로
- `YTDLP_COOKIES_FROM_BROWSER`: `chrome` (자동 쿠키)

### 댓글 추출

**파일**: `backend/app/services/comment_extractor.py`

3-tier 폴백 시스템:
1. ✅ **API** (`/api/comment/list/`) - 가장 안정적, 쿠키 필요
2. Playwright DOM 스크래핑
3. yt-dlp `--write-comments`

```python
# Auto mode priority (line 94-110)
comments = await self._extract_tiktok_comment_list(url, limit)  # API first
if not comments:
    comments = await self._extract_tiktok_playwright(url, limit)
if not comments:
    comments = await self._extract_via_ytdlp(url, 'tiktok', limit)
```

### 쿠키 관리

**저장 위치**: `/backend/tiktok_cookies_auto.json`

```bash
# 쿠키 상태 확인
python -c "
from app.services.comment_extractor import comment_extractor
print(comment_extractor.get_cookie_status())
"

# 자동 갱신
python -c "
import asyncio
from app.services.comment_extractor import comment_extractor
asyncio.run(comment_extractor._try_export_chrome_cookies())
"
```

**테스트** (2026-01-04):
```
✅ Loaded 11 TikTok cookies
✅ TikTok comment list API: 5 comments
  1. the floor is lava ?... (185,805 likes)
```

---

## Instagram

### 메타데이터 추출

**파일**: `backend/app/services/video_downloader.py`, `crawlers/instagram.py`

| Method | Source | Limitation |
|--------|--------|------------|
| yt-dlp | yt-dlp | 로그인 필요, 불안정 |
| Playwright | DOM | 봇 탐지 |

> [!WARNING]
> Instagram upload_date 추출률 0% (20/20 items). 개선 필요.

### 댓글 추출

yt-dlp `--write-comments` 사용, 성공률 낮음.

---

## DB 스키마

### outlier_items

| Column | Type | Source |
|--------|------|--------|
| `video_url` | VARCHAR | 원본 URL |
| `platform` | VARCHAR | tiktok/youtube/instagram |
| `upload_date` | TIMESTAMP | 플랫폼에서 추출 |
| `best_comments` | JSONB | 댓글 배열 |
| `view_count` | INTEGER | 메타데이터 |
| `creator_username` | VARCHAR | 크리에이터 핸들 |

### 댓글 스키마 (JSONB)

```json
{
  "text": "댓글 내용",
  "likes": 12345,
  "lang": "ko",
  "author": "username"
}
```

---

## 트러블슈팅

### TikTok 댓글 0개

| 원인 | 해결 |
|------|------|
| 쿠키 만료 (>1h) | Chrome에서 TikTok 로그인 후 갱신 |
| IP 차단 | VPN 또는 프록시 (`TIKTOK_PROXY`) |
| 봇 탐지 | API 메서드 우선 사용 |

### YouTube API 할당량 초과

```bash
# 할당량 확인: Google Cloud Console > APIs > YouTube Data API v3
# 기본 10,000 units/day
```

### Instagram 실패

현재 안정적 솔루션 없음. yt-dlp + 로그인 쿠키 필요.

---

## 히스토리

| 날짜 | 변경 |
|------|------|
| 2026-01-04 | YouTube API upload_date 버그 수정 |
| 2026-01-04 | TikTok 쿠키 갱신, 댓글 추출 검증 |
| 2026-01-04 | 3플랫폼 통합 문서 생성 |
| 2026-01-01 | TikTok Auto mode: API first |

---

## 관련 파일

- [video_downloader.py](file:///Users/ted/komission/backend/app/services/video_downloader.py) - 메타데이터 추출
- [comment_extractor.py](file:///Users/ted/komission/backend/app/services/comment_extractor.py) - 댓글 추출
- [tiktok_extractor.py](file:///Users/ted/komission/backend/app/services/tiktok_extractor.py) - TikTok 통합
- [crawlers/youtube.py](file:///Users/ted/komission/backend/app/crawlers/youtube.py) - YouTube 크롤러
