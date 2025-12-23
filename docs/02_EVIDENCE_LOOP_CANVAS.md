# Evidence Loop + Canvas Template (최신)

**작성**: 2026-01-06
**목표**: Evidence Loop를 **Canvas 템플릿**으로 운영

---

## 1) 핵심 원칙
- **Evidence Loop가 엔진**
- **Debate는 옵션** (조건부 실행)
- **DB=SoR, Sheets=버스**
- NotebookLM/Opal은 **가속 옵션**

---

## 2) Evidence Loop (운영 플로우)
```
Outlier: 외부 소스 크롤링
  ↓
Parent 후보 선정
  ↓
Depth1/Depth2 실험
  ↓
Metric Daily 수집
  ↓
Evidence Snapshot 생성
  ↓
Decision Summary 생성
  ↓
Creator 실행 + O2O know-how 연결
  ↓
성과 반영 → 다음 Parent
```

---

## 3) Sheets 버스 설계 (컬럼 계약)

**네이밍 규칙**: `VDG_*` 접두어 사용 (예: `VDG_Evidence`)

## 1. Google Sheets Infrastructure

**Generated Sheets (as of 2025-02-13):**
- **VDG_Outlier_Raw**: `1bFYFBMMgOz8a4Q8VIJJgdr7-jhfTU4iTn9rdG-GXxSs`
- **VDG_Parent_Candidates**: `1PmD_jtNWar6iyqYO9h2styRPl6LV3DF38NZVpa8lMeQ`
- **VDG_Evidence**: `1wYYOkAx4c__qkP_5q77qCEYqOkgx85w-ysIzDzjhakg`
- **VDG_Decision**: `1Po1CYEqN_Rlj78qWFqzZFRn87ESCBe8u1Vq1WQpcCtQ`
- **VDG_Experiment**: `1WIcagWwbb4AtRHHNR7hha73hale2htzUHjG03eM9nfs`
- **VDG_Progress**: `11BTl6Mhp8vaSNdGSlpwxrsJFWJtlmSFFBt5gFC6K8IM`
- **VDG_O2O_Campaigns**: `1ntnsUXW8WxYsAlUD9uH9ahhwUvb2QlYQ8Z2u0MxfYrk`
- **VDG_O2O_Applications**: `1Bjgd5mKsa-jOH6gRFqRNODWnCtEklG7NU0vZO5_cY3Q`
- **VDG_Insights**: `1NDYuTfQNuct1eBeIHwLsQyuJIbheAmwfps5Op8i0cjg`

The following sheets form the core database for the Evidence Loop.

### 3.1 Outlier Raw Sheet (옵션)
**목적**: 외부 구독 소스 크롤링 결과를 사람이 검토/선별

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| source_name | string | O | 구독 소스 이름 |
| source_url | string | O | 원본 링크 |
| collected_at | datetime | O | 수집 시각 |
| platform | enum | O | tiktok / instagram |
| category | string | O | beauty / meme / lifestyle 등 |
| title | string | O | 콘텐츠 제목 |
| views | int | O | 조회수 |
| growth_rate | float | X | 성장률(있으면) |
| author | string | X | 크리에이터 |
| posted_at | datetime | X | 업로드 시각 |
| status | enum | O | new / ignored / candidate |

### 3.2 Parent Candidates Sheet
**목적**: Parent 후보 확정용 관리표

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| parent_id | uuid | O | DB Parent ID |
| title | string | O | Parent 제목 |
| platform | enum | O | tiktok / instagram |
| category | string | O | 카테고리 |
| source_url | string | O | 원본 링크 |
| baseline_views | int | O | 기준 조회수 |
| baseline_engagement | float | X | 기준 참여율 |
| selected_by | string | X | 선택자 |
| selected_at | datetime | X | 선택 시각 |
| status | enum | O | planning / depth1 / depth2 / complete |

### 3.3 Evidence Sheet
**목적**: Depth 결과를 한 표로 정규화

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| evidence_id | uuid | O | Evidence 스냅샷 ID |
| parent_id | uuid | O | Parent ID |
| parent_title | string | O | Parent 제목 |
| depth | int | O | 1 or 2 |
| variant_id | uuid | O | Variant ID |
| variant_name | string | O | 변주 이름 |
| views | int | O | 조회수 |
| engagement_rate | float | X | 참여율 |
| retention_rate | float | X | 유지율 |
| tracking_days | int | O | 추적 일수 |
| confidence_score | float | O | 신뢰도 점수 |
| confidence_ci_low | float | X | 신뢰구간 하한 |
| confidence_ci_high | float | X | 신뢰구간 상한 |
| rank | int | O | 순위 |
| winner | boolean | O | 최종 후보 여부 |
| generated_at | datetime | O | 생성 시각 |

### 3.4 Decision Sheet
**목적**: 자동/반자동 의사결정 결과 저장

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| decision_id | uuid | O | Decision ID |
| parent_id | uuid | O | Parent ID |
| winner_variant_id | uuid | O | 승자 변주 ID |
| winner_variant_name | string | O | 승자 변주 이름 |
| top_reasons | text | O | 근거 3개 요약 |
| risks | text | X | 리스크 2개 |
| next_experiment | text | O | 다음 실험 1개 |
| sample_size | int | X | 샘플 수 |
| tracking_days | int | X | 추적 일수 |
| success_criteria | text | X | 성공 기준 |
| status | enum | O | draft / approved / in_progress |
| created_at | datetime | O | 생성 시각 |

### 3.5 Experiment Sheet
**목적**: 실행 계획/배정 관리

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| experiment_id | uuid | O | 실험 ID |
| parent_id | uuid | O | Parent ID |
| variant_id | uuid | O | 변주 ID |
| assigned_creators | text | X | 담당자 목록 |
| start_date | date | O | 시작일 |
| end_date | date | O | 종료일 |
| status | enum | O | planned / running / done |
| notes | text | X | 메모 |

### 3.6 Progress Sheet
**목적**: 14일 추적 상태 요약

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| variant_id | uuid | O | 변주 ID |
| date | date | O | 날짜 |
| views | int | O | 조회수 |
| engagement_rate | float | X | 참여율 |
| retention_rate | float | X | 유지율 |
| confidence_score | float | X | 현재 점수 |
| status | enum | O | tracking / complete |

### 3.7 O2O Campaigns Sheet
**목적**: 캠페인 운영/게이팅 기준

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| campaign_id | string | O | 캠페인 ID |
| campaign_type | enum | O | instant / onsite / shipment |
| title | string | O | 캠페인명 |
| brand | string | X | 브랜드 |
| category | string | X | 카테고리 |
| reward_points | int | O | 포인트 |
| reward_product | string | X | 제공 제품 |
| location_name | string | X | 방문형 장소 |
| address | string | X | 방문형 주소 |
| status | enum | O | active / inactive |
| start_date | date | O | 시작일 |
| end_date | date | O | 종료일 |

### 3.8 O2O Applications Sheet
**목적**: 신청/배송/완료 상태 관리

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| application_id | uuid | O | 신청 ID |
| campaign_id | string | O | 캠페인 ID |
| user_id | uuid | O | 사용자 ID |
| status | enum | O | applied / selected / shipped / delivered / completed / rejected |
| applied_at | datetime | O | 신청 시각 |
| updated_at | datetime | O | 변경 시각 |
| shipment_tracking | string | X | 배송 추적 번호 |

### 3.9 Insights Sheet (NotebookLM 출력)
**목적**: NotebookLM Data Tables 결과 저장

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| parent_id | uuid | O | Parent ID |
| summary | text | O | 요약 |
| key_patterns | text | X | 상위 패턴 |
| risks | text | X | 리스크 |
| created_at | datetime | O | 생성 시각 |

---

## 4) NotebookLM/Opal 활용 (옵션)

### NotebookLM (Data Tables)
- Evidence Sheet → Data Tables → Insights Sheet
- 사람에게 설명 가능한 표/요약을 자동 생성

### Opal
- Evidence/Insights Sheet 입력 → Decision Sheet 생성
- 실험 계획과 리스크 요약을 자동 생산

> 없으면 n8n/백엔드에서 동일 로직으로 대체 가능

---

## 5) Debate 실행 조건 (옵션)
Debate는 아래 조건에서만 실행:
- Top1 vs Top2 점수 차 < 0.03
- 샘플 수 부족(Tracking < 10일)
- 리스크가 큰 카테고리(브랜드/법적 민감 영역)

---

## 6) Canvas 템플릿 (MVP)

### 템플릿 A: Evidence → Decision → Assignment
```
[Parent Selector] → [Evidence Table] → [Decision Summary] → [Creator Assignment]
```

### 템플릿 B: Evidence → Debate(옵션) → Decision
```
[Evidence Table] → [Debate Transcript] → [Decision Summary]
```

### 템플릿 C: Performance → Heritage
```
[Progress Tracker] → [Winner 결정] → [Heritage 업데이트]
```

---

## 7) 출력 형식 (UI 최소 기준)
기본 화면:
- 결론 5줄
- Evidence Table
- Progress(14일)

Pro/팀 리드:
- Debate 전문 보기(접힘)
- Evidence/Decision 히스토리 다운로드
