# User Flow (최신)

**작성**: 2026-01-07
**목표**: 관리자/크리에이터/캠페인 흐름을 한 문서에서 정렬

---

## 1) 역할 정의
- **Curator/Admin**: 아웃라이어 수집/선별, Parent 승격, Evidence/Decision 생성
- **Creator**: Outlier 선택 → 촬영 → 제출 → 성과 추적
- **Brand/O2O**: 캠페인 타입(즉시/방문/배송) 설정 및 게이팅

---

## 2) Curator/Admin 흐름 (수동 수집 중심)
1. **Outlier 수집**
   - 수동 링크 입력 (`POST /api/v1/outliers/items/manual`)
   - DB 저장(`outlier_items`)
2. **Sheet 동기화**
   - `sync_outliers_to_sheet.py`로 `VDG_Outlier_Raw` 반영
3. **NotebookLM 해석**
   - 요약/클러스터 생성 → `notebook_library` 저장
4. **Parent 후보 선정**
   - 후보 기준(조회수/성장률/카테고리)
   - `VDG_Parent_Candidates` 상태 업데이트
5. **Parent 승격**
   - `POST /api/v1/outliers/items/{item_id}/promote`
   - `remix_nodes` 생성 (layer=MASTER)
6. **분석/요약(옵션)**
   - `POST /api/v1/remix/{node_id}/analyze`
   - NotebookLM/Opal 요약 반영
7. **Evidence/Decision**
   - Evidence Sheet → Decision Sheet 생성
8. **Capsule/Template 배포**
   - Canvas 템플릿에 적용

---

## 3) Creator 흐름
1. **Outlier 탐색**
   - Parent/Outlier 목록에서 선택
2. **Shoot 실행**
   - Capsule 요약 + 변수 슬롯(5%)만 노출
3. **제출/검수**
   - 제출 후 상태 추적(Tracking)
4. **성과 확인**
   - My 페이지에서 성과/로열티 확인

---

## 4) O2O 타입별 흐름
- **즉시형**: 신청 → 촬영 → 제출 → 승인
- **방문형**: 신청 → 위치 인증 → 촬영 → 제출
- **배송형**: 신청 → 선정 → 배송 → 촬영 → 제출

> O2O 타입에 따라 Shoot CTA와 안내 문구가 달라집니다.

---

## 5) Role Switch 규칙 (Creator ↔ Business)
- 상단 스위치로 역할 전환 (페이지 분리 없음)
- **세션 컨텍스트 유지**: node_id/parent_id/phase는 유지
- Creator: Shoot 중심 CTA만 강조
- Business: Evidence/Decision/O2O 관리가 전면

---

## 6) 데이터 산출물 (핵심)
- OutlierItem → 후보
- RemixNode(MASTER) → Parent
- EvidenceSnapshot → 증거 요약
- Decision Sheet → 다음 실험 제안
