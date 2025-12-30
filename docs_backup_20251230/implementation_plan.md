# Cloud Run + Playwright 배포 검증 플랜

## 문제 요약
- Build SUCCESS ≠ Deploy: 빌드 성공해도 서비스에 새 이미지가 미적용될 수 있음
- 로그 확인 불완전: textPayload만 보면 실제 에러를 놓칠 수 있음
- 경로 문제 미검증: symlink 타겟에 브라우저가 설치됐는지 확인 필요
- 원인 단정 금지: `source: unknown`은 Playwright 외에도 TikTok 차단 가능

## 7단계 검증 체크리스트

1. 빌드 상태 확인

```bash
gcloud builds list --project=PROJECT --region=REGION --limit=1
```

2. Revision 생성/적용 확인 (Build ≠ Deploy)

```bash
gcloud run services describe SERVICE --project=PROJECT --region=REGION \
  --format="value(status.latestReadyRevisionName,status.latestCreatedRevisionName)"

gcloud run revisions list --service=SERVICE --project=PROJECT --region=REGION --limit=3
```

3. 이미지 digest 일치 확인 (빌드 결과가 Revision에 반영됐는지)

```bash
gcloud run revisions describe REVISION --project=PROJECT --region=REGION \
  --format="value(spec.containers[0].image)"
```

4. 전체 로그 확인 (text/json/proto 포함)

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE" \
  --project=PROJECT --limit=50 \
  --format="table(timestamp,severity,textPayload,jsonPayload.message,protoPayload.status.message)"

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE AND severity>=ERROR" \
  --project=PROJECT --limit=20
```

5. 로컬 Docker 사전 검증

```bash
docker build -t tiktok-extractor-test .

docker run --rm -it tiktok-extractor-test /bin/sh
# 컨테이너 내부:
ls -la /ms-playwright/
ls -la $HOME/.cache/ms-playwright/
echo $PLAYWRIGHT_BROWSERS_PATH
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); print('OK'); b.close(); p.stop()"
```

6. 런타임 환경변수 확인

```bash
gcloud run services describe SERVICE --project=PROJECT --region=REGION \
  --format="yaml(spec.template.spec.containers[0].env)"

curl https://SERVICE_URL/debug/env
```

7. Playwright/추출 동작 확인

```bash
curl -X POST "https://SERVICE_URL/debug/playwright-html?url=https://www.tiktok.com/@user/video/123"
curl -X POST "https://SERVICE_URL/extract?url=https://www.tiktok.com/@user/video/123"
```

기대값: `success: true`, `contains_video_data: true`, 메타데이터 정상 반환

## Dockerfile 검증된 패턴

```dockerfile
FROM python:3.13-slim
WORKDIR /app

# 1. 환경변수 먼저 설정 (설치 전!)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONPATH=/app

# 2. 시스템 deps 설치 (root)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libfreetype6 \
    libfontconfig1 libdbus-1-3 libx11-xcb1 libxcursor1 \
    fonts-liberation fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 3. Python deps 설치
RUN pip install --no-cache-dir playwright httpx fastapi uvicorn

# 4. 브라우저 설치 (ENV 적용된 상태에서)
RUN mkdir -p /ms-playwright && playwright install chromium

# 5. 사용자 생성 및 권한 부여
RUN useradd -m appuser && chown -R appuser:appuser /ms-playwright /app

# 6. (선택) Symlink 생성 - 안전장치
RUN mkdir -p /home/appuser/.cache && \
    ln -s /ms-playwright /home/appuser/.cache/ms-playwright && \
    chown -R appuser:appuser /home/appuser

USER appuser
COPY --chown=appuser:appuser . .
CMD ["python", "tiktok_standalone.py"]
```

## 재발 방지 규칙

| 상황 | 잘못된 행동 | 올바른 행동 |
| --- | --- | --- |
| Build SUCCESS 후 | 바로 curl 테스트 | Revision 배포 여부 먼저 확인 |
| 추출 실패 시 | "경로 문제" 단정 | 로그 전체 + HTML 내용 확인 |
| Dockerfile 수정 | 바로 Cloud Run 배포 | 로컬 Docker 테스트 먼저 |
| 배포 반복 실패 | 수정 후 즉시 재배포 | 실패 원인 로그 분석 후 진행 |
| 로그 비어있음 | 무시하고 진행 | jsonPayload/protoPayload 확인 |

## 다음 액션
- 최신 Revision이 실제로 서비스에 적용되었는지 확인
- 전체 로그 (jsonPayload 포함) 확인
- 로컬 Docker 빌드로 `/ms-playwright` 내용 검증
- TikTok HTML이 차단 페이지인지 확인
- 검증 완료 후에만 재배포
