# Komission 출시 체크리스트

> **마지막 업데이트**: 2025-12-31  
> **목표**: MVP 출시 준비 완료

---

## Phase 0: 인프라 검증 (P0 - 당장)

### 데이터베이스
- [ ] PostgreSQL 운영 DB 연결 확인
- [ ] `alembic upgrade head` 실행 (coaching 테이블 생성)
  ```bash
  cd backend && alembic upgrade head
  ```
- [ ] Neo4j 연결 확인 (그래프 DB)

### 환경변수 (.env)
- [ ] `GEMINI_API_KEY` 설정 확인
- [ ] `DATABASE_URL` 운영 DB로 설정
- [ ] `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 확인
- [ ] `FIREBASE_PROJECT_ID` 확인
- [ ] `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (S3용)

### 서버
- [ ] 백엔드 서버 기동 테스트
  ```bash
  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
- [ ] 헬스체크 엔드포인트 확인: `GET /health`

---

## Phase 1: 백엔드 검증 (P0)

### API 엔드포인트 테스트
- [ ] `POST /api/v1/agent/chat` - Chat Agent 응답 확인
- [ ] `GET /api/v1/agent/suggestions` - 추천 프롬프트
- [ ] `POST /api/v1/agent/action` - 액션 실행
- [ ] `GET /coaching/sessions` - 세션 목록

### 핵심 서비스
- [ ] Gemini API 호출 성공 확인
- [ ] CoachingRepository CRUD 동작 확인
- [ ] IntentClassifier 7가지 인텐트 분류 테스트

### 에러 핸들링
- [ ] 인증 없이 API 호출 → 401 반환 확인
- [ ] 잘못된 입력 → 적절한 에러 메시지

---

## Phase 2: 프론트엔드 검증 (P0)

### 빌드
- [ ] 프로덕션 빌드 성공
  ```bash
  cd frontend && npm run build
  ```
- [ ] 빌드 에러 0개

### 페이지 접근
- [ ] `/` - 메인 페이지 로딩
- [ ] `/login` - 로그인 페이지
- [ ] `/agent` - Chat Agent UI
- [ ] `/outliers` - Outlier 관리자

### 기능 테스트
- [ ] Firebase 로그인 성공
- [ ] Chat Agent 메시지 전송/수신
- [ ] localStorage 메시지 저장 확인
- [ ] 새로고침 후 대화 복원

---

## Phase 3: 데이터 준비 (P1 - 1주 내)

### 클러스터 10개 적재
| # | 패턴 | 니치 | Parent | Kids | 상태 |
|---|------|------|--------|------|------|
| 1 | hook_subversion | beauty | | | ⬜ |
| 2 | visual_punch | beauty | | | ⬜ |
| 3 | question_hook | food | | | ⬜ |
| 4 | reaction_loop | food | | | ⬜ |
| 5 | transformation | daily | | | ⬜ |
| 6 | before_after | beauty | | | ⬜ |
| 7 | tutorial_hook | food | | | ⬜ |
| 8 | surprise_reveal | daily | | | ⬜ |
| 9 | pov_narrative | fashion | | | ⬜ |
| 10 | challenge_format | daily | | | ⬜ |

### 클러스터 생성 기준
- Parent: Tier S/A, merger_quality=gold
- Kids: 6개 이상, unique_creators >= 3
- success + failure 대비 포함

---

## Phase 4: 베타 테스트 (P1)

### 테스터 모집
- [ ] 크리에이터 3-5명 선정
- [ ] 비공개 베타 초대 발송
- [ ] 피드백 수집 채널 준비 (Discord/Slack)

### 테스트 시나리오
- [ ] 시나리오 1: 첫 방문 → 로그인 → Chat Agent 질문
- [ ] 시나리오 2: 촬영 가이드 요청 → Pack 생성
- [ ] 시나리오 3: 트렌드 분석 질문

### 수집 지표
- [ ] 첫 메시지까지 걸린 시간
- [ ] 세션 당 메시지 수
- [ ] 이탈 지점

---

## Phase 5: 출시 당일 (D-Day)

### 최종 점검
- [ ] 모든 Phase 0-1 체크 완료
- [ ] 백업 확인 (DB)
- [ ] 모니터링 대시보드 준비

### 배포
- [ ] 프론트엔드 배포 (Vercel/etc)
- [ ] 백엔드 배포 (Cloud Run/EC2)
- [ ] DNS 확인

### 롤백 플랜
- [ ] 이전 버전 태그 확인
- [ ] 롤백 명령어 문서화
- [ ] 긴급 연락처 공유

---

## 지금 바로 실행 (Quick Start)

```bash
# 1. DB 마이그레이션
cd backend && alembic upgrade head

# 2. 백엔드 테스트
python -c "from app.services.coaching_repository import CoachingRepository; print('OK')"

# 3. 프론트엔드 빌드
cd ../frontend && npm run build

# 4. API 테스트
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "안녕하세요"}'
```

---

## 출시 후 모니터링

### 1주차 KPI
- DAU: 10명 이상
- 세션 완료율: 50% 이상
- 첫 메시지 응답시간: 3초 이내

### 알림 설정
- [ ] 에러 로그 > 10/min → Slack 알림
- [ ] API 응답시간 > 5s → 알림
- [ ] DB 연결 실패 → 즉시 알림

---

## 연락처

| 역할 | 담당 | 연락처 |
|------|------|--------|
| 인프라 | | |
| 백엔드 | | |
| 프론트엔드 | | |
| PM | | |
