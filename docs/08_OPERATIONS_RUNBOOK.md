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
**권한**: Curator/Admin

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
  "https://komission-api-xxx.run.app/api/v1/outliers/items/{item_id}/comments"

# 3. VDG 분석 재시도
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/outliers/items/{item_id}/approve"
```

---

## 2.7) Admin 권한 부여 (운영)

**원칙**: 운영 확장성을 위해 DB role 기반(`role=admin`)을 기본으로 사용하고,  
`SUPER_ADMIN_EMAILS`는 부트스트랩/긴급 복구용으로만 사용한다.

**절차**:
1. 대상 직원이 Google 로그인으로 계정을 1회 생성한다.
2. DB에서 role을 admin으로 승격한다.

```sql
-- Promote to admin
UPDATE users SET role = 'admin' WHERE email = 'someone@example.com';

-- Rollback to user
UPDATE users SET role = 'user' WHERE email = 'someone@example.com';
```

**Break-glass**:
- 환경변수 `SUPER_ADMIN_EMAILS`에 콤마로 이메일을 추가하면 DB 변경 없이 관리자 권한을 부여할 수 있다.

---

## 2.8) 코칭 로그 품질 / WS 상태 점검 (운영)

**목적**: 세션 로그 품질과 WebSocket 상태를 빠르게 점검한다.
**권한**: Admin

```bash
# 전체 세션 요약
curl -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/coaching/stats/all-sessions"

# 로그 품질 리포트
curl -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/coaching/quality/report"

# 개별 세션 품질
curl -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/coaching/quality/session/{session_id}"

# WebSocket 헬스
curl -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/coaching/ws/health"

# 활성 WebSocket 세션
curl -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/coaching/ws/sessions"
```

---

## 3) 파일럿 운영 규칙
- Parent 1개당 최소 14일 추적
- Depth2는 Depth1 성공 기준 충족 시에만 진행
- 실패 Parent는 즉시 중단 및 기록

---

## 4) 장애/리스크 대응
- Sheet 쓰기 실패: 권한/폴더 공유 확인
- ~~중복 Outlier: URL hash 중복 확인~~ → **DB UNIQUE 제약으로 자동 방지됨 (2024-12-30)**
- Decision 공백: Opal 실패 시 규칙 기반 대체

---

## 4.5) 승격 워크플로우 [NEW 2024-12-30]

**일반 승격 vs 체험단 승격**

| 액션 | campaign_eligible | 용도 |
|------|-------------------|------|
| `[승격]` 버튼 | `False` | 일반 RemixNode 생성 (VDG 분석용) |
| `[체험단 선정]` 버튼 | `True` | RemixNode + O2O 캠페인 후보군 등록 |

**체험단 후보 조회**:
```bash
# campaign_eligible=true 아이템 목록
curl -H "Authorization: Bearer $TOKEN" \
  "https://komission-api-xxx.run.app/api/v1/outliers?campaign_eligible=true"
```

---

## 5) 핵심 운영 지표
- Evidence → Decision 생성 시간
- Depth 실험 회전율
- O2O 타입별 전환율
- **체험단 후보 → 실제 캠페인 전환율**
