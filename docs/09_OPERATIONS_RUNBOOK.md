# Operations Runbook (최신)

**작성**: 2026-01-07
**목표**: 일/주간 운영 체크리스트 표준화

---

## 1) 일간 체크리스트
- Outlier 링크 수집(수동 입력 or CSV)
- `sync_outliers_to_sheet.py` 실행
- 후보 상태 확인 (new → candidate)
- Parent 승격 1건 이상 처리

---

## 2) 주간 체크리스트
- Evidence Runner 실행 (1회 이상)
- Decision Sheet 생성 확인
- 상위 패턴/리스크 요약 업데이트
- O2O 캠페인 타입 게이팅 점검

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
