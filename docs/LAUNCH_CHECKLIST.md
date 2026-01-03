# Komission 출시 체크리스트

> **마지막 업데이트**: 2026-01-02 (모바일 앱 추가)  
> **목표**: MVP 출시 준비 완료 (웹 + 모바일)

---

## Phase 0: 인프라 검증 (P0 - 완료)

### 데이터베이스
- [x] PostgreSQL 운영 DB 연결 확인
- [x] `alembic upgrade head` 실행 (coaching 테이블 생성)
- [ ] Neo4j 연결 확인 (그래프 DB)

### 환경변수 (.env)
- [x] `GEMINI_API_KEY` 설정 확인
- [x] `DATABASE_URL` 운영 DB로 설정
- [x] `FIREBASE_PROJECT_ID` 확인
- [ ] `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 확인
- [ ] `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (S3용)

### 서버
- [x] 백엔드 서버 기동 테스트
- [x] 헬스체크 엔드포인트 확인: `GET /health`

---

## Phase 1: 백엔드 검증 (P0 - 완료)

### API 엔드포인트 테스트
- [x] `POST /api/v1/agent/chat` - Chat Agent 응답 확인
- [x] `GET /api/v1/coaching/sessions` - 세션 목록 (Admin)
- [x] `POST /api/v1/coaching/sessions/{session_id}/events/intervention` - 개입 로깅
- [x] `scripts/smoke_coaching_ws.sh` - 코칭 WS 핸드셰이크 + recording 상태 확인

### 핵심 서비스
- [x] Gemini API 호출 성공 확인
- [x] CoachingRepository CRUD 동작 확인
- [x] IntentClassifier 7가지 인텐트 분류 테스트
- [x] `backend/venv/bin/pytest` - 백엔드 테스트 통과

---

## Phase 2: 웹 프론트엔드 검증 (P0 - 완료)

### 빌드
- [x] 프로덕션 빌드 성공 (`bun run build`)
- [x] 빌드 에러 0개

### 페이지 접근
- [x] `/` - 메인 페이지 로딩
- [x] `/login` - 로그인 페이지
- [x] `/ops/outliers` - Outlier 관리자 (Ops)

### 기능 테스트
- [x] Google OAuth 로그인 성공 (JWT 발급)
- [x] 코칭 세션 시작/중단
- [x] 음성 코칭 ON/OFF 토글

---

## Phase 2.5: 모바일 앱 검증 (⭐ NEW - Week 1 완료)

### 프로젝트 설정
- [x] Expo 프로젝트 초기화 (`/mobile`)
- [x] react-native-vision-camera 설정
- [x] expo-battery, expo-network 설정

### 촬영 기능
- [x] 4K 촬영 동작 확인
- [x] H.265/H.264 코덱 자동 선택
- [x] 프레임 레이트 안정화
- [x] 배터리/네트워크/저장공간 모니터링

### 코칭 연동
- [x] WebSocket 연결 (useCoachingWebSocket)
- [x] 음성 코칭 토글
- [x] 텍스트 코칭 토글
- [x] 피드백 오버레이 UI

### Phase 2 스트리밍

- [x] H.264 스트리밍 최적화
- [x] FrameThrottler (2fps)
- [x] AdaptiveBitrateController
- [x] frame_ack RTT 측정

### DB 연동
- [x] useSessionPersistence 훅
- [x] 세션 생성 API 연동
- [ ] 개입/결과 로깅 스키마 정합성 업데이트 필요

### 앱스토어 준비
- [ ] npm install 완료
- [ ] `npx expo prebuild --platform ios`
- [ ] TestFlight 등록
- [ ] 앱스토어 심사 제출

---

## Phase 3: 데이터 준비 (P1 - 진행 중)

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

---

## Phase 4: 베타 테스트 (P1)

### 테스터 모집
- [ ] 크리에이터 3-5명 선정
- [ ] 비공개 베타 초대 발송
- [ ] 피드백 수집 채널 준비 (Discord/Slack)

### 테스트 시나리오
- [ ] 시나리오 1: 웹앱으로 VDG 분석
- [ ] 시나리오 2: 모바일 앱으로 4K 촬영 + 코칭
- [ ] 시나리오 3: 웹앱에서 영상 업로드/성과 확인

---

## Phase 5: 출시 당일 (D-Day)

### 최종 점검
- [ ] 모든 Phase 0-2.5 체크 완료
- [ ] 백업 확인 (DB)
- [ ] 모니터링 대시보드 준비

### 배포
- [ ] 프론트엔드 배포 (Vercel)
- [ ] 백엔드 배포 (Cloud Run/EC2)
- [ ] 모바일 앱 배포 (TestFlight → App Store)
- [ ] DNS 확인

---

## 지금 바로 실행 (Quick Start)

### 모바일 앱 (⭐ 우선)
```bash
# 1. 의존성 설치
cd mobile && npm install

# 2. iOS 프리빌드
npx expo prebuild --platform ios

# 3. 실제 기기 빌드
npx expo run:ios --device
```

### 백엔드
```bash
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 웹 프론트엔드
```bash
cd frontend && bun run dev
```

---

## 출시 후 모니터링

### 1주차 KPI
- DAU: 웹 10명 + 모바일 5명 이상
- 4K 촬영 완료율: 50% 이상
- 코칭 피드백 유용성: 4.0/5.0 이상

---

## 연락처

| 역할 | 담당 | 연락처 |
|------|------|--------|
| 모바일 앱 | Claude (AI) | - |
| 웹앱 고도화 | 새 개발자 | - |
| PM | | |
