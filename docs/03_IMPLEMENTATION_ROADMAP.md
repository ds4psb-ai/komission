# Implementation Roadmap (Phases + Micro Steps)

**작성**: 2026-01-07
**목표**: Evidence Loop MVP → 2개 Parent 파일럿

---

## Phase 0: Alignment & Setup (Day 0-2)
**목표**: 운영/데이터 기준 고정

- 소스 확정: 외부 구독 사이트 목록 + 크롤링 정책
- Drive 폴더 구조 확정: Evidence/Decision/Experiment/O2O
- 카테고리/패턴 택소노미 고정 (beauty/meme/etc + hook/scene/audio/subtitle/pacing)
- NotebookLM/Opal 사용 범위 확정 (옵션)
- Capsule IO 계약 정의 (입력/출력/로그)

**완료 기준**
- `.env`에 Drive/Sheet 설정 완료
- 템플릿 IO 계약 문서화

---

## Phase 1: Ingestion + SoR (Week 1)
**목표**: Outlier → Parent 승격까지 안정화

**마이크로 단계**
1. Outlier 수동 입력 API 정리 (링크 기반)
2. 중복 제거 규칙 확정 (URL hash)
3. DB → Sheet 동기화 스크립트 연결
4. 후보 리스트(Parent Candidates) 자동 생성 로직
5. Parent 승격 → RemixNode 생성
6. 분석 호출(`/remix/{node_id}/analyze`) 경로 확정

**완료 기준**
- Outlier 20개 이상 적재
- Parent 1개 승격 + 분석 결과 확보
- `VDG_Outlier_Raw`와 `VDG_Parent_Candidates` 생성 확인

---

## Phase 2: Evidence Loop MVP (Week 2)
**목표**: Evidence → Decision 생성 자동화

**마이크로 단계**
1. Progress CSV 입력 연결(선택)
2. Evidence 스냅샷 생성 로직 정리
3. Evidence Sheet 업로드 확인
4. Opal Decision 생성 (또는 규칙 기반 대체)
5. NotebookLM Insights Sheet(옵션)

**완료 기준**
- Evidence/Decision Sheet 1건 이상 생성
- Evidence → Decision 데이터 흐름 검증

---

## Phase 3: Capsule + Canvas (Week 3)
**목표**: Canvas 템플릿에 Evidence/Decision 연결

**마이크로 단계**
1. Capsule Node 계약 적용 (입력/출력/로그)
2. Canvas 템플릿 A/B 연결
3. 핵심 CTA(촬영/신청) 위치 고정
4. O2O 타입 게이팅(즉시/방문/배송)

**완료 기준**
- Canvas에서 Evidence/Decision 표시
- O2O 타입에 따라 UI가 분기

---

## Phase 4: Pilot + O2O (Week 4)
**목표**: 2개 Parent 파일럿 가동

**마이크로 단계**
1. Parent 2개 선정 (beauty/meme)
2. Depth1 실험 실행 + 14일 추적
3. Decision 반영 후 Depth2 시작
4. KPI 리포트 생성

**완료 기준**
- 주간 리포트 자동 생성
- 성공 구조 1개 이상 도출

---

## 정의된 산출물 (요약)
- Evidence Sheet / Decision Sheet / Progress Sheet
- Capsule 실행 로그
- 2개 Parent 파일럿 결과
