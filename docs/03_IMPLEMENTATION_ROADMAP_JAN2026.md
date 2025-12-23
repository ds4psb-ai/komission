# Implementation Roadmap: 1월~3월 2026 실행 계획

**작성**: 2025-12-24  
**목표**: 4주 내 MVP 배포 → 3개월 내 완전 운영화  
**범위**: Viral Depth + Genealogy Debate + Canvas 노드 통합  
**결과**: "증거 기반 창작 루프"의 완전 자동화 플랫폼

---

## Phase 1: Week 1-2 (2026-01-06 ~ 01-19) - 기초 구축

### Week 1: 데이터베이스 & n8n 기초

#### Monday-Tuesday: PostgreSQL 마이그레이션

```
Task 1.1: 테이블 생성
├─ viral_parents
├─ viral_depth1_variants
├─ viral_depth2_variants
├─ genealogy_evidence
├─ creator_profiles
└─ video_generations

Task 1.2: 샘플 데이터 입력
├─ "마지막 클릭" parent 레코드 생성
├─ depth1 변주 3개 입력
├─ depth2 변주 2개 입력
└─ 성과 데이터 입력 (지난 30일)

Task 1.3: 인덱싱 설정
├─ parent_id, platform, category
├─ time_period, created_at
└─ 쿼리 성능 테스트

소요시간: 1인 × 2일
담당: DB 엔지니어

산출물:
✅ 초기 데이터베이스 구축
✅ 샘플 데이터 입력
✅ 성능 테스트 완료
```

#### Wednesday: n8n 환경 구축

```
Task 1.4: n8n 배포
├─ Docker로 로컬 배포
├─ PostgreSQL 연결
├─ Claude API 키 설정
├─ YouTube API 연결
└─ 테스트 실행

Task 1.5: n8n 기본 노드 생성
├─ "Load Data" 노드
├─ "Calculate Stats" 노드
├─ "Format Output" 노드
└─ 간단한 테스트 워크플로우

소요시간: 1인 × 1일
담당: Backend 엔지니어

산출물:
✅ n8n 운영 환경
✅ API 연결 확인
✅ 기본 노드 구현
```

#### Thursday-Friday: Evidence Table 노드 구현

```
Task 1.6: "Evidence_Table_Builder" 구현
├─ n8n 노드 로직 작성 (Python)
├─ 입력: parent_id, depth_levels, time_period
├─ 출력: evidence_table JSON
├─ 테스트: "마지막 클릭" 데이터로 실행
└─ 결과 검증

Task 1.7: 성능 최적화
├─ 쿼리 실행시간 < 5초 목표
├─ 메모리 사용량 최적화
├─ 캐싱 설정 (Redis, 선택)
└─ 로그 설정

소요시간: 1인 × 2일
담당: Backend 엔지니어

산출물:
✅ Evidence Table 자동 생성 확인
✅ 성능 기준 충족 (< 5초)
✅ PoC 데이터로 테스트 완료
```

#### Weekend: 검증 & 조정

```
Quality Assurance:
├─ 생성된 Evidence Table 정성평가
├─ 수치 검증 (improvement % 재계산)
├─ 오류 확인 (NaN, null 처리)
└─ 리뷰 미팅 (팀 전체)

조정사항:
├─ 필요시 스키마 변경
├─ n8n 노드 수정
└─ 다음주 계획 확정

소요시간: 1인 × 2시간
담당: Tech Lead + 팀

산출물:
✅ Week 1 검증 완료
✅ 이슈 목록 작성
```

### Week 2: Claude 토론 & Canvas 기초

#### Monday-Tuesday: Claude 토론 프롬프트 & 통합

```
Task 2.1: 토론 프롬프트 최적화
├─ 기본 프롬프트 작성 (Part 1 참고)
├─ 3명 분석가 역할 정의
├─ 톤 & 길이 조정
├─ Claude로 테스트 (10회 이상)
└─ 결과 평가 및 피드백

Task 2.2: n8n "Debate_Generator" 노드 구현
├─ 입력: evidence_table + parent_name
├─ Claude API 호출 로직
├─ 출력 파싱 (분석가별로 분리)
├─ 오류 처리
└─ 테스트 실행

Task 2.3: 토론 결과 저장
├─ PostgreSQL debate_results 테이블
├─ 전문, 요약, 메타데이터 저장
├─ 검색 가능하도록 인덱싱
└─ 히스토리 추적

소요시간: 1인 × 2.5일
담당: AI/ML 엔지니어 + Backend

산출물:
✅ 토론 프롬프트 최종 버전
✅ n8n Debate Generator 노드
✅ 토론 히스토리 저장 시스템
```

#### Wednesday-Thursday: Canvas 기초 노드 구현

```
Task 2.4: Canvas Node 시스템 아키텍처
├─ Node 메타데이터 스키마 설계
├─ Input/Output 포맷 정의
├─ 노드 연결 규칙 정의
├─ Canvas API 스펙 작성
└─ 문서화

Task 2.5: Type 1 노드 구현 (Data Input)
├─ "Parent Selector" 노드 UI
├─ "Depth Level Selector" 노드 UI
├─ "Time Period Selector" 노드 UI
├─ "Auto-load Data" 백엔드 로직
└─ 연결 테스트

Task 2.6: Type 2 노드 구현 (Analysis) - Part 1
├─ "Evidence Table Builder" 노드
├─ "Debate Generator" 노드
├─ Canvas → n8n 호출 로직
└─ 결과 표시 UI

소요시간: 2인 × 2일
담당: Frontend + Backend

산출물:
✅ Canvas 노드 기초 아키텍처
✅ Data Input 노드들 (UI + 로직)
✅ Analysis 노드들 (UI + 통합)
✅ 초기 Canvas 대시보드 프로토타입
```

#### Friday: 통합 테스트

```
Task 2.7: E2E 통합 테스트
├─ Canvas에서 Parent 선택
├─ 자동 데이터 로드 확인
├─ Evidence Table 생성 확인
├─ 토론 생성 확인
├─ 결과 표시 확인
└─ 성능 측정

Issue Resolution:
├─ 발견된 모든 버그 수정
├─ UI 개선사항 적용
├─ 성능 최적화
└─ 보안 검증

소요시간: 2인 × 1.5일
담당: 전체 팀

산출물:
✅ Week 1-2 통합 검증 완료
✅ 버그 제로
✅ 성능 기준 충족 (< 3초)
```

---

## Phase 2: Week 3-4 (2026-01-20 ~ 02-02) - MVP 완성

### Week 3: Canvas 노드 완성 & 피드백 루프

#### Monday-Tuesday: Type 3 & 4 노드 (Decision & Execution)

```
Task 3.1: Type 3 노드 구현 (Decision)
├─ "Experiment Plan Generator" 노드
├─ "Success Criteria Validator" 노드
├─ "Decision Summary" 노드
├─ 각 노드의 UI + 로직
└─ 상호 연결

Task 3.2: Type 4 노드 구현 (Execution)
├─ "Batch Assign to Creators" 노드
│  ├─ 창작자 선택 드롭다운
│  ├─ 할당 확인 모달
│  └─ 데이터베이스 저장
├─ "Notification Sender" 노드
│  ├─ Slack 알림 발송
│  ├─ Email 발송
│  └─ Canvas 업데이트
└─ "Timeline Tracker" 노드

소요시간: 2인 × 2일
담당: Frontend + Backend

산출물:
✅ Decision 노드들 완성
✅ Execution 노드들 완성
✅ 실제 창작자 할당 가능
```

#### Wednesday-Thursday: Type 5 노드 (Feedback & Heritage)

```
Task 3.3: YouTube API 통합
├─ 영상별 성과 메트릭 수집
├─ 매일 자동 수집 스케줄
├─ 신뢰도 점수 업데이트
├─ 수렴 분석
└─ 승자 결정 로직

Task 3.4: Type 5 노드 구현
├─ "Performance Data Collector" 노드
├─ "Confidence Score Updater" 노드
├─ "Winner Determination" 노드
├─ "Heritage Update" 노드
├─ 각 노드 UI + 로직
└─ 자동 루프 설정

Task 3.5: Heritage 시스템
├─ 이전 승자 데이터 저장
├─ "다음 세대 창작자"에게 추천
├─ 패턴 학습 (아직은 수동)
└─ 히스토리 탭 UI

소요시간: 2인 × 2.5일
담당: Backend + Data

산출물:
✅ 모든 Type 5 노드 완성
✅ YouTube API 연결 완료
✅ Heritage 시스템 기초 구축
```

#### Friday: MVP 최종 검증

```
Task 3.6: 전체 워크플로우 E2E 테스트
├─ Parent 선택 → 할당 → 생성 → 추적 → 승자 → Heritage
├─ 모든 노드 정상 작동 확인
├─ 데이터 흐름 검증
├─ UI/UX 검증
└─ 성능 최종 측정

Task 3.7: MVP 문서화
├─ 사용자 가이드 (팀용)
├─ API 문서 (개발자용)
├─ n8n 워크플로우 설정 가이드
├─ 트러블슈팅 가이드
└─ 자주 묻는 질문

소요시간: 2인 × 1.5일
담당: 전체 + 기술 문서 담당자

산출물:
✅ MVP 완전 검증 완료
✅ 버그 제로
✅ 문서 완성
✅ 팀 교육 준비
```

### Week 4: PoC 실행 & 최종 배포

#### Monday: 팀 교육 & PoC 킥오프

```
Task 4.1: 팀 온보딩
├─ 기술 리더들 대상 2시간 교육
├─ Canvas 대시보드 사용법
├─ n8n 모니터링 방법
├─ 에러 대응 프로토콜
└─ Q&A

Task 4.2: PoC 환경 준비
├─ 운영 데이터베이스 최종 설정
├─ n8n 자동 스케줄 설정
├─ YouTube API 키 설정
├─ Slack 봇 연결
├─ 모니터링 도구 설정 (Sentry, DataDog)
└─ 백업 정책 확인

Task 4.3: PoC 시작
├─ Parent: "마지막 클릭" 선택
├─ Canvas에서 실행
├─ 첫 Evidence Table 생성
├─ 첫 토론 스크립트 생성
├─ 창작자 할당 실행
└─ 14일 추적 시작

소요시간: 3인 × 1.5일
담당: 전체 팀

산출물:
✅ 팀이 시스템 완벽히 이해
✅ PoC 정식 시작
✅ 모니터링 활성화
```

#### Tuesday-Wednesday: 모니터링 & 최적화

```
Task 4.4: PoC 초기 모니터링
├─ 첫 영상 생성 확인
├─ 성과 데이터 수집 확인
├─ 신뢰도 점수 증가 추적
├─ 에러 로그 확인
└─ 팀과 일일 싱크

Task 4.5: 실시간 최적화
├─ 발견된 모든 버그 즉시 수정
├─ UI 개선사항 적용
├─ 성능 튜닝
├─ 창작자 피드백 수집
└─ 프롬프트 조정 (필요시)

소요시간: 2인 × 2일
담당: 개발팀 풀타임

산출물:
✅ 버그 매일 해결
✅ PoC 순조로운 진행
✅ 팀 신뢰도 증대
```

#### Thursday-Friday: 최종 배포 & 문서화

```
Task 4.6: 운영 환경 배포
├─ 개발 → 운영 환경 마이그레이션
├─ 데이터 검증
├─ 성능 재측정
├─ 보안 감사
└─ 롤백 계획 수립

Task 4.7: 최종 문서화
├─ 전체 아키텍처 문서 (for CEO)
├─ 기술 문서 (for developers)
├─ 운영 매뉴얼 (for team)
├─ FAQ 및 트러블슈팅
└─ 성공 메트릭 정의

Task 4.8: MVP 공식 릴리스
├─ 팀에 공식 발표
├─ Slack에 "MVP 출시" 알림
├─ 기본 사용법 문서 배포
├─ 피드백 채널 오픈
└─ 첫주 일정 정리

소요시간: 3인 × 2일
담당: 전체 팀

산출물:
✅ MVP 운영 환경 완전 배포
✅ 모든 문서 완성
✅ 팀이 독립적으로 운영 가능
✅ 공식 릴리스 완료
```

---

## Phase 3: Week 5-8 (2026-02-03 ~ 02-27) - PoC 실행 & 패턴 학습

### Week 5-6: PoC 진행 + 2번째 Parent 시작

```
"마지막 클릭" PoC:
├─ Week 1-2 (Jan 6-19): 데이터 수집 중
├─ Week 3 (Jan 20-26): 최종 분석 중
├─ Week 4 (Jan 27-Feb 2): 승자 결정 (예상)

"사랑의 후유증":
├─ Week 5 (Feb 3-9): Evidence Table + 토론 생성
├─ Week 6 (Feb 10-16): 실험 실행 시작
└─ Week 7-8: 계속 진행

병렬 진행:
├─ Canvas 노드 개선사항 수집
├─ n8n 성능 최적화
├─ Claude 프롬프트 A/B 테스트
└─ Creator 피드백 수집
```

### Week 7-8: 패턴 학습 & 문서화

```
학습할 것:
1. "마지막 클릭"에서 어떤 변주가 성공했나?
2. "사랑의 후유증"도 같은 패턴을 따르나?
3. 성공 패턴의 공통점은?
4. 실패한 변주의 특징은?

산출물:
├─ "성공 패턴 분석" 보고서
├─ "Depth1 vs Depth2 비교" 분석
├─ "창작자별 성공률" 분석
└─ 다음 단계 권장사항
```

---

## Phase 4: Week 9-12 (2026-03-02 ~ 03-27) - Scaling & Automation

### Week 9: 5개 Parent 동시 진행

```
Week 8 결과:
├─ "마지막 클릭": 승자 확정 (Depth1 최적화 시작)
├─ "사랑의 후유증": Depth2 진행 중 (신뢰도 0.82)
├─ "꽃길": 방금 시작 (Week 5)

Week 9: 2개 추가
├─ "노을빛 편지": 시작
├─ "마지막 인사": 시작
└─ 총 5개 Parent 동시 추적

자동화 레벨:
├─ 데이터 수집: 100% 자동
├─ 토론 생성: 100% 자동
├─ 의사결정: 100% 자동
├─ 창작자 할당: 95% 자동 (마지막 승인만)
└─ 모니터링: 100% 자동
```

### Week 10: 운영 안정화

```
주요 업무:
├─ 일일 에러 처리
├─ 주간 성과 보고
├─ 창작자 피드백 반영
├─ n8n 성능 모니터링
├─ Canvas UI 개선
└─ 팀 지원

예상 이슈:
- YouTube API 할당량 모니터링
- Claude API 비용 최적화
- 데이터베이스 크기 증가 관리
- 새로운 Parent 온보딩 프로세스 자동화
```

### Week 11-12: 다음 단계 계획

```
Week 11 상황:
├─ 5개 Parent 동시 진행
├─ 2개는 완료, 3개는 진행 중
├─ 누적 데이터: 50개 변주, 200+ 창작 영상
├─ 성공 패턴: 점점 명확해짐

Week 12 계획:
├─ "통 데이터셋" 시스템으로 전환 준비
├─ "Creator Persona Matching" 개발 시작
├─ "Heritage 자동 학습" 개발 시작
├─ 다음 3개월 로드맵 수립

목표: "증거 기반 의사결정" 자동화 완성
```

---

## 리소스 할당

### 핵심 팀 구성

```
**개발팀 (6인)**
├─ Backend Lead (1인) - n8n, PostgreSQL, API
├─ Frontend Lead (1인) - Canvas UI/UX
├─ AI/ML Engineer (1인) - Claude 프롬프트 최적화
├─ DevOps (1인) - 배포, 모니터링, 보안
├─ QA/Test (1인) - 테스트, 버그 추적
└─ 인턴/주니어 (1인) - 문서화, 데이터 입력

**운영팀 (2인)**
├─ Product Manager (1인) - 요구사항, 우선순위, 리포팅
└─ Operations Manager (1인) - 창작자 조율, 데이터 검증

**CEO (의사결정)**
└─ 전략 방향, 대외 발표, 펀딩

합계: 8인 + CEO
```

### 스프린트 구조

```
각 2주 스프린트:

Sprint Planning (월요일 10:00, 1시간):
├─ 지난주 회고
├─ 이번주 목표 확정
├─ 작업 분배
└─ 리스크 논의

Daily Standup (매일 10:30, 15분):
├─ 어제: 뭐 했나?
├─ 오늘: 뭐 할건가?
├─ 블로킹: 뭐가 막혔나?
└─ 다음: 도와줄게 있나?

Sprint Review (금요일 16:00, 30분):
├─ 완성된 작업 데모
├─ 품질 검증
├─ 메트릭 보고
└─ 이슈 논의

Sprint Retro (금요일 16:30, 30분):
├─ "잘했던 것" 공유
├─ "아쉬웠던 것" 논의
├─ "개선할 것" 결정
└─ 행동 계획
```

---

## 비용 추정

### 개발 비용

```
인건비:
├─ Backend Lead: $6,000/월 × 3 = $18,000
├─ Frontend Lead: $6,000/월 × 3 = $18,000
├─ AI/ML Engineer: $5,000/월 × 3 = $15,000
├─ DevOps: $5,000/월 × 3 = $15,000
├─ QA: $4,000/월 × 3 = $12,000
├─ 인턴: $2,000/월 × 3 = $6,000
├─ PM: $5,000/월 × 3 = $15,000
└─ Ops: $3,000/월 × 3 = $9,000

합계: $108,000 (3개월)

외주비:
├─ 디자인 (UI/UX): $3,000
├─ 법무 (약관): $2,000
└─ 기타: $2,000

합계: $7,000

인프라 비용:
├─ AWS/GCP: $500/월 × 3 = $1,500
├─ PostgreSQL: $30/월 × 3 = $90
├─ n8n 호스팅: $15/월 × 3 = $45
├─ 모니터링: $100/월 × 3 = $300
└─ API 비용: $50/월 × 3 = $150

합계: $2,085

**총 비용: $117,085 (3개월)**
```

### ROI 분석

```
비용: $117,085

기대 효과:
1. "증거 기반 창작" 플랫폼 완성
2. 창작자 10명이 월 50개 영상 생성
3. 성공률 20-30% (지금 10%)
4. 월 30-50개 바이럴 영상 산출

수익화:
├─ 광고수익: 월 $5,000-10,000 (확정)
├─ 창작자 구독료: 월 $2,000-5,000 (미정)
└─ B2B (다른 회사): 월 $3,000-10,000 (가능성)

합계: 월 $10,000-25,000

ROI:
- 6개월 후: 손익분기점 도달
- 12개월 후: 200%+ 수익률
```

---

## Success Metrics

### 개발 완료도

```
주요 마일스톤:

Week 2:
├─ [ ] Evidence Table 자동 생성 ✅ 필수
├─ [ ] Claude 토론 통합 ✅ 필수
└─ [ ] Canvas 기초 노드 ✅ 필수

Week 4:
├─ [ ] 모든 Canvas 노드 완성 ✅ 필수
├─ [ ] MVP 배포 ✅ 필수
└─ [ ] PoC 시작 ✅ 필수

Week 8:
├─ [ ] 2개 Parent 완료 ✅ 필수
├─ [ ] 성공 패턴 분석 ✅ 필수
└─ [ ] 팀 신뢰도 높음 ✅ 필수

Week 12:
├─ [ ] 5개 Parent 동시 진행 ✅ 필수
├─ [ ] 운영 자동화 ✅ 필수
└─ [ ] 통 데이터셋 V1 ✅ 목표
```

### 운영 성과

```
Week 4 (PoC 시작):
├─ 영상 생성률: 25개/주 × 2주 = 50개
├─ 신뢰도 도달: 0.85+
├─ 버그 수: 0
└─ 팀 피드백: 긍정적

Week 8 (2개 완료):
├─ 누적 영상: 200+개
├─ 성공 패턴: 2-3개 식별
├─ 창작자 만족도: 80%+
└─ 시스템 안정성: 99%+

Week 12 (5개 동시):
├─ 월 생성 영상: 200+개
├─ 바이럴율: 25-30%
├─ 팀 효율성: 2배 향상
└─ 준비도: Phase 2로 준비 완료
```

---

## 리스크 관리

### 주요 리스크

```
Risk 1: 기술 통합 지연
├─ 영향: 배포 지연
├─ 확률: 중간 (30%)
├─ 대응: 병렬 개발, 버퍼 2주
└─ 모니터링: 주간 스프린트 체크

Risk 2: Claude API 비용 초과
├─ 영향: 운영 비용 증가
├─ 확률: 낮음 (10%)
├─ 대응: 캐싱, 배치 처리
└─ 모니터링: 일일 API 비용 추적

Risk 3: YouTube API 할당량 초과
├─ 영향: 성과 데이터 수집 불가
├─ 확률: 낮음 (5%)
├─ 대응: API 할당량 증설, 대안 API
└─ 모니터링: 주간 할당량 사용률 체크

Risk 4: 창작자 피드백 부정적
├─ 영향: PoC 실패
├─ 확률: 중간 (25%)
├─ 대응: 주간 피드백 수집, 빠른 개선
└─ 모니터링: 일일 슬랙 피드백

Risk 5: 데이터 정합성 오류
├─ 영향: 토론 신뢰성 저하
├─ 확률: 중간 (20%)
├─ 대응: 자동 검증 로직, QA 강화
└─ 모니터링: 매일 샘플 검증
```

### 완화 전략

```
기술 리스크:
├─ 개발 병렬화 (3개 스트림)
├─ 버퍼 2주 확보
├─ 자동화 테스트 100%
└─ 롤백 계획 상비

운영 리스크:
├─ 주간 팀 미팅
├─ 일일 에러 로그 검토
├─ 월간 보고서 작성
└─ 피드백 채널 24/7 오픈

데이터 리스크:
├─ 자동 검증 로직
├─ 수동 QA 샘플링
├─ 일일 데이터 백업
└─ 주간 정합성 검사
```

---

## 체크리스트

### 1월 (Week 1-4)

```
Week 1:
[ ] PostgreSQL 테이블 생성
[ ] 샘플 데이터 입력
[ ] n8n 배포
[ ] Evidence Table 노드 구현
[ ] Week 1 검증 통과

Week 2:
[ ] Claude 토론 프롬프트 최적화
[ ] n8n Debate Generator 구현
[ ] Canvas 기초 노드 구현
[ ] Type 1, 2 노드 완성
[ ] E2E 통합 테스트 통과

Week 3:
[ ] Type 3, 4 노드 완성
[ ] Type 5 노드 완성
[ ] YouTube API 통합
[ ] MVP 최종 검증 통과
[ ] 모든 문서 작성 완료

Week 4:
[ ] 팀 교육 완료
[ ] PoC 환경 준비
[ ] PoC "마지막 클릭" 시작
[ ] 모니터링 활성화
[ ] MVP 공식 릴리스
[ ] 운영 환경 배포 완료
```

### 2월 (Week 5-8)

```
Week 5-6:
[ ] 2번째 Parent "사랑의 후유증" 시작
[ ] PoC 데이터 수집 계속
[ ] n8n 성능 최적화

Week 7-8:
[ ] "마지막 클릭" 승자 확정
[ ] 성공 패턴 분석 완료
[ ] PoC 결과 보고서 작성
[ ] Phase 2 계획 수립
```

### 3월 (Week 9-12)

```
Week 9:
[ ] 5개 Parent 동시 진행
[ ] 자동화 레벨 95%+

Week 10:
[ ] 운영 안정화
[ ] 월간 보고서 작성

Week 11-12:
[ ] 통 데이터셋 V1 개발 시작
[ ] Creator Persona Matching 개발 시작
[ ] 연간 계획 수립
```

---

## 최종 메시지

### 3개월 후 (2026-03-31)

당신은 가지게 될 것:

```
✅ "증거 기반 창작" 플랫폼 (완전 자동화)
✅ Canvas 노드 시스템 (10개 노드)
✅ n8n 백엔드 (5개 워크플로우)
✅ 성공 데이터 (200+개 영상)
✅ 성공 패턴 (5-10개 확인)
✅ 팀 역량 (자립적 운영)
✅ 관계사 신뢰 (검증된 성과)

그리고 시작할 수 있을 것:
✅ "통 데이터셋" 시스템 (거장 분석)
✅ "Creator Persona Matching" (개인화)
✅ "Heritage 자동 학습" (진화)
✅ B2B 판매 (다른 회사에 제공)
✅ 시리즈 A 펀딩 (검증된 비즈니스)
```

---

## 다음 액션

1. **이 로드맵 검토 & 승인** (CEO)
2. **팀 구성 확정** (12월 말)
3. **개발 환경 준비** (1월 3일)
4. **1월 6일: 개발 정식 시작**

**"2026년 3월 31일까지 완성."**