# Implementation Roadmap (2주 MVP + 4주 파일럿)

**작성**: 2026-01-06
**목표**: Evidence Loop MVP → 2개 Parent 파일럿

---

## Week 0 (준비)
- Outlier 소스 정보 확정 (구독 사이트 크롤링 정책 포함)
- Google Drive 폴더 구조 확정 (Evidence/Decision/Experiment/O2O)
- 카테고리 택소노미 확정 (beauty, meme, lifestyle, food, fashion)

---

## Week 1: 데이터/수집/증거 기반
- VDG 스키마 마이그레이션
- Outlier 크롤러 스크립트 + 스케줄링(일 1회)
- Parent 후보 API
- Evidence Snapshot 계산 로직
- Evidence Sheet 자동 업로드

**출력물**: Parent 1개 기준 Evidence Sheet 생성

---

## Week 2: Decision + Canvas 템플릿
- Decision Sheet 생성 (Opal or 백엔드 로직)
- Canvas 템플릿 A/B 연결 (Evidence/Decision)
- Progress Sheet(Tracking 14일) 연결
- Debate 옵션 구현 (조건부)

**출력물**: Evidence → Decision → Canvas 표시 완료

---

## Week 3: O2O 연계 + 파일럿 1차
- O2O Campaigns Sheet ↔ Earn/Shoot UI 게이팅
- 배송/방문/즉시 타입 표시
- 파일럿 Parent 1개(beauty) Depth1 시작

**출력물**: Depth1 진행 + 상태 추적

---

## Week 4: 파일럿 2차 + 평가
- Parent 2개(meme) Depth1/2 시작
- Evidence/Decision 주간 리포트 생성
- KPI 측정: Evidence→Decision 시간, 성공률 변화

**출력물**: 파일럿 2개 결과 + 개선 지표

