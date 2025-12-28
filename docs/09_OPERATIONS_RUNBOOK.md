# Operations Runbook (최신)

**작성**: 2025-12-28
**목표**: 일/주간 운영 체크리스트 표준화

---

## 1) 일간 체크리스트
- Outlier 링크 수집(수동 입력 or CSV)
- `sync_outliers_to_sheet.py` 실행
- 영상 해석(코드) 파이프라인 실행 확인
- 후보 상태 확인 (new → candidate)
- Parent 승격 1건 이상 처리
- TikTok 댓글 수집 실패 시 쿠키 갱신 필요 (아래 절차)

---

## 2) 주간 체크리스트
- Evidence Runner 실행 (1회 이상)
- Decision Sheet 생성 확인
- Opal 템플릿 시드 생성 여부 확인(선택)
- 상위 패턴/리스크 요약 업데이트
- O2O 캠페인 타입 게이팅 점검
- TikTok 세션 갱신 (다음 섹션 참고)

---

## 2.5) TikTok 쿠키 갱신 절차 (신규)

**원인**: TikTok sessionid는 2-4시간마다 만료됨

**절차**:
```bash
# 1. Chrome 완전 종료
# 2. Playwright로 쿠키 추출 (로그인 필요 시 브라우저에서 로그인)
PYTHONPATH=backend ./venv/bin/python backend/scripts/export_tiktok_cookies.py

# 3. Secret Manager 업데이트
gcloud secrets versions add tiktok-cookies \
  --data-file=backend/tiktok_cookies_auto.json \
  --project=algebraic-envoy-456610-h8

# 4. Cloud Run 재배포 (secret 버전 latest 사용 시 자동 적용)
gcloud run services update tiktok-extractor --region=asia-northeast3 \
  --update-secrets="/secrets/tiktok_cookies.json=tiktok-cookies:latest"
```

**검증**:
```bash
curl -X POST "https://tiktok-extractor-ubwbuq6kaa-du.a.run.app/extract?url=...&include_comments=true"
# Comments: 5 이상이면 성공
```

---

## 2.6) 수동 댓글 검토 (신규)

**대상**: S/A 티어 아이템 중 댓글 추출 실패

**프로세스**:
1. 댓글 실패 시 자동으로 `comments_pending_review` 상태
2. 큐레이터가 수동으로 댓글 입력
3. VDG 분석 재시도

```bash
# 1. 대기 목록 확인
curl -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/outliers/items/pending-comments"

# 2. 수동 댓글 입력
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comments": [{"text": "완전 대박", "likes": 1500}]}' \
  "https://komission-api-xxx.run.app/api/v1/outliers/items/{id}/comments"

# 3. VDG 분석 재시도
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/outliers/items/{id}/approve"
```

---

## 3) 파일럿 운영 규칙
- Parent 1개당 최소 14일 추적
- Depth2는 Depth1 성공 기준 충족 시에만 진행
- 실패 Parent는 즉시 중단 및 기록

---

## 4) 장애/리스크 대응
- Sheet 쓰기 실패: 권한/폴더 공유 확인
- 중복 Outlier: URL hash 중복 확인
- Decision 공백: Opal 실패 시 규칙 기반 대체

---

## 5) 핵심 운영 지표
- Evidence → Decision 생성 시간
- Depth 실험 회전율
- O2O 타입별 전환율
