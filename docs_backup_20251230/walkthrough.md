# TikTok 추출 시스템 - 인수인계 문서

작성일: 2025-12-28
상태: 로컬 테스트 성공, Cloud Run 배포 대기

## 요약
| 항목 | 상태 |
| --- | --- |
| 메타데이터 추출 | ✅ 로컬 완벽 동작 (405M views 등) |
| 댓글 추출 | ⚠️ 로컬 IP 차단, 서버 IP로 테스트 필요 |
| 로컬 Docker | ✅ 빌드 성공, Playwright launch() 성공 |
| Cloud Run 배포 | ❌ 배포 명령 실행됐으나 Revision 미생성 |

## 주요 파일
| 파일 | 설명 |
| --- | --- |
| `Dockerfile` | Playwright + Chromium 포함 |
| `tiktok_standalone.py` | 경량 FastAPI 서비스 + 디버그 엔드포인트 |
| `tiktok_extractor.py` | 통합 추출 로직 |
| `tiktok_metadata.py` | 메타데이터 파싱 |

## 현재 상태

### GCP 정보
- Project: algebraic-envoy-456610-h8
- Region: asia-northeast3
- Service: tiktok-extractor
- Account: ted.taeeun.kim@gmail.com

### 문제점
- 빌드는 성공하지만 배포(Revision 생성)가 안 됨
- 현재 서비스는 15:46 UTC에 배포된 구 버전 실행 중
- 구 버전은 Playwright 경로 문제로 `source: unknown` 반환

## 배포 전 로컬 검증 (완료됨)

```bash
cd /Users/ted/komission/backend
docker build -t tiktok-test .

docker run --rm tiktok-test python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    print('Browser launched successfully!')
    browser.close()
"
```

결과: `PLAYWRIGHT_BROWSERS_PATH: /ms-playwright`, Browser launched successfully

## 배포 명령 (실행 필요)

```bash
cd /Users/ted/komission/backend
gcloud run deploy tiktok-extractor \
  --source . \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --project=algebraic-envoy-456610-h8 \
  --quiet
```

## 배포 후 검증 (중요!)

1. Revision 생성 확인

```bash
gcloud run revisions list --service=tiktok-extractor \
  --project=algebraic-envoy-456610-h8 --region=asia-northeast3 --limit=3
```

기대값: 새 Revision이 ACTIVE로 표시

2. 환경 확인

```bash
curl https://tiktok-extractor-297976838198.asia-northeast3.run.app/debug/env
```

기대값: `playwright_browsers_path: /ms-playwright`, `browsers_dir_exists: true`

3. Playwright 동작 확인

```bash
curl -X POST "https://tiktok-extractor-297976838198.asia-northeast3.run.app/debug/playwright-html?url=https://www.tiktok.com/@haircutsalon27/video/7585084792698342686"
```

기대값: `success: true`, `contains_video_data: true`

4. 실제 추출 테스트

```bash
curl -X POST "https://tiktok-extractor-297976838198.asia-northeast3.run.app/extract?url=https://www.tiktok.com/@haircutsalon27/video/7585084792698342686"
```

기대값: `view_count: 405200000` 등 메타데이터 반환

## 문제 발생 시 디버깅

### Playwright 경로 에러
```
Executable doesn't exist at /home/appuser/.cache/ms-playwright/...
```

해결: Dockerfile의 symlink 확인

```bash
RUN mkdir -p /home/appuser/.cache && \
    ln -s /ms-playwright /home/appuser/.cache/ms-playwright
```

### `source: unknown` 반환
확인 순서:

1. `/debug/env` → `browsers_dir_exists` 확인
2. `/debug/playwright-html` → Playwright 동작 확인
3. `gcloud logging read` → 전체 에러 로그 확인

### 로그 확인

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=tiktok-extractor" \
  --project=algebraic-envoy-456610-h8 --limit=50 \
  --format="table(timestamp,severity,textPayload)"
```

## 검증 체크리스트
- 배포 후 새 Revision 생성 확인 (BUILD SUCCESS ≠ DEPLOY)
- `/debug/env` 정상 응답
- `/debug/playwright-html` 성공
- `/extract` 메타데이터 반환
- 댓글 추출 테스트 (TikTok 차단 여부에 따라 실패 가능)

## 알려진 제한사항
- 쿠키 미포함: Cloud Run 컨테이너에 쿠키 파일 없음. Secret Manager로 주입 필요
- 프록시 미설정: TikTok IP 차단 시 프록시 필요
- 댓글 추출: 메타데이터는 성공해도 댓글은 TikTok 차단으로 실패 가능
