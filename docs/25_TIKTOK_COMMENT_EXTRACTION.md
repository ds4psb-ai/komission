# TikTok 댓글 추출 아키텍처

> 마지막 업데이트: 2026-01-01

## 개요

TikTok 동영상에서 베스트 댓글을 추출하기 위한 3-tier 폴백 시스템.

```
┌─────────────────────────────────────────────────────────────┐
│                    VDG 분석 파이프라인                        │
│   outliers.py / remix.py → extract_best_comments(limit=10)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              TikTokUnifiedExtractor (tiktok_extractor.py)    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1. UNIVERSAL_DATA JSON 파싱 (댓글 미포함 - 2026년 기준) │ │
│  │ 2. DOM 스크래핑 (Playwright)                           │ │
│  │ 3. → comment_extractor 폴백                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CommentExtractor (comment_extractor.py)         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Auto Mode 우선순위 (2026-01-01 수정):                   │ │
│  │ 1. ✅ /api/comment/list/ API (쿠키 사용) ← 가장 안정적  │ │
│  │ 2. Playwright DOM 스크래핑                             │ │
│  │ 3. yt-dlp --write-comments                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 핵심 컴포넌트

### 1. TikTokUnifiedExtractor
**파일**: `backend/app/services/tiktok_extractor.py`

| 항목 | 값 |
|------|-----|
| 역할 | 메타데이터 + 댓글 통합 추출 |
| 기본 댓글 수 | 10개 (`TIKTOK_MAX_COMMENTS`) |
| 메타데이터 소스 | UNIVERSAL_DATA JSON |
| 댓글 소스 | DOM → comment_extractor 폴백 |

### 2. CommentExtractor
**파일**: `backend/app/services/comment_extractor.py`

```python
# Auto Mode (line 94-110)
# 1. API (comment_list) → 2. Playwright → 3. yt-dlp

comments = await self._extract_tiktok_comment_list(video_url, limit)  # 가장 안정적
if comments:
    return comments

comments = await self._extract_tiktok_playwright(video_url, limit)
if comments:
    return comments
    
return await self._extract_via_ytdlp(video_url, platform, limit)
```

### 3. 프로덕션 독립 서비스
**파일**: `backend/tiktok_standalone.py`

```bash
# Docker 배포
docker build -f Dockerfile.tiktok -t komission-tiktok .
docker run -p 8080:8080 komission-tiktok

# 엔드포인트
POST /extract?url=<tiktok_url>  # 메타데이터 + 댓글
POST /metadata?url=<tiktok_url> # 메타데이터만
```

---

## API 메서드 상세 (`_extract_tiktok_comment_list`)

**엔드포인트**: `https://www.tiktok.com/api/comment/list/`

| 파라미터 | 설명 |
|---------|------|
| `aweme_id` | 비디오 ID (URL에서 추출) |
| `cursor` | 페이지네이션 |
| `count` | 요청 댓글 수 (최대 20) |
| `aid` | 앱 ID (1988 고정) |
| `msToken` | 쿠키에서 추출 |

**응답 구조**:
```json
{
  "status_code": 0,
  "has_more": true,
  "cursor": 20,
  "comments": [
    {
      "text": "댓글 내용",
      "digg_count": 123,
      "user": {"unique_id": "username", "nickname": "닉네임"}
    }
  ]
}
```

---

## 쿠키 관리

**자동 쿠키 갱신** (`_try_export_chrome_cookies`):
```python
# 저장 위치
backend/tiktok_cookies_auto.json

# 갱신 주기
1시간마다 자동 갱신 (Chrome 브라우저에서 추출)

# 필수 쿠키
- msToken: API 요청 서명
- tt_chain_token: 세션 유지
```

**수동 쿠키 설정**:
```bash
export TIKTOK_COOKIE_FILE=/path/to/cookies.json
```

---

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `TIKTOK_MAX_COMMENTS` | 10 | 추출할 최대 댓글 수 |
| `TIKTOK_TIMEOUT_MS` | 30000 | Playwright 타임아웃 |
| `TIKTOK_MAX_RETRIES` | 2 | 재시도 횟수 |
| `TIKTOK_PROXY` | - | 프록시 서버 URL |
| `TIKTOK_COOKIE_FILE` | - | 쿠키 파일 경로 |
| `TIKTOK_COMMENTS_PROVIDER` | auto | 추출 방법 강제 지정 |

---

## 테스트

```bash
# 자동 모드 테스트 (권장)
python scripts/test_tiktok_comment_extractors.py \
  --url "https://www.tiktok.com/@user/video/123" \
  --method auto

# 특정 방법 테스트
python scripts/test_tiktok_comment_extractors.py \
  --url "..." --method comment_list  # API
python scripts/test_tiktok_comment_extractors.py \
  --url "..." --method playwright    # DOM
python scripts/test_tiktok_comment_extractors.py \
  --url "..." --method ytdlp         # yt-dlp
```

---

## 트러블슈팅

### "0개 댓글" 문제

| 증상 | 원인 | 해결책 |
|------|------|--------|
| API 200이지만 0개 | 쿠키 만료 | Chrome에서 TikTok 로그인 후 재시도 |
| Playwright 0개 | 봇 탐지 | API 메서드 우선 사용 |
| yt-dlp 실패 | TikTok 차단 | API 메서드 사용 |

### 쿠키 상태 확인
```python
from app.services.comment_extractor import CommentExtractor
e = CommentExtractor()
print(e.get_cookie_status())
# {'status': 'fresh', 'age_hours': 0.5, 'count': 11, ...}
```

---

## 히스토리

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-01 | Auto mode 우선순위 변경: API first |
| 2026-01-01 | 기본 댓글 수 5개 → 10개 |
| 2025-12-27 | API 응답 수집 방식 개선 |
| 2025-12-xx | 프로덕션 Docker 배포 |
