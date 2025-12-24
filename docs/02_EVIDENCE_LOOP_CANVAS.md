# Evidence Loop + Canvas Template (최신)

**작성**: 2026-01-07
**목표**: Evidence Loop를 **Canvas 템플릿**으로 운영

---

## 1) 핵심 원칙
- **Evidence Loop가 엔진**
- **Debate는 옵션** (조건부 실행)
- **DB=SoR, Sheets=버스**
- NotebookLM/Opal은 **가속 레이어**이며 결과는 **DB로 래핑**
- Capsule/Template은 **실행 레이어**

---

## 2) Evidence Loop (운영 플로우)
```
Outlier: 수동 입력/외부 소스 크롤링
  ↓
NotebookLM 해석 → Notebook Library(DB)
  ↓
Parent 후보 선정
  ↓
Pattern 후보 라벨 (Notebook Library 기반)
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

### 3.0 Google Sheets Infrastructure
Sheets are created by the runner or setup scripts using the `VDG_*` names.
The pipeline looks up sheets **by name**, so IDs can live in Drive without hardcoding.
Use `KOMISSION_FOLDER_ID` to keep them in a shared folder.

### 3.1 Outlier Raw Sheet (옵션)
**목적**: 외부 구독 소스 크롤링 결과를 사람이 검토/선별
DB에서 수집한 Outlier는 `sync_outliers_to_sheet.py`로 동기화합니다.

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
| status | enum | O | new / ignored / candidate / promoted |

**상태 매핑 (DB → Sheet)**
- pending → new
- selected → candidate
- rejected → ignored
- promoted → promoted

### 3.2 Parent Candidates Sheet
**목적**: Parent 후보 확정용 관리표

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| parent_id | string | O | DB Parent ID (권장: remix_nodes.node_id) |
| title | string | O | Parent 제목 |
| platform | enum | O | tiktok / instagram |
| category | string | O | 카테고리 |
| source_url | string | O | 원본 링크 |
| baseline_views | int | O | 기준 조회수 |
| baseline_engagement | float | X | 기준 참여율 |
| selected_by | string | X | 선택자 |
| selected_at | datetime | X | 선택 시각 |
| status | enum | O | planning / depth1 / depth2 / complete |

> Sheet-only 운영 시 parent_id는 임시 ID를 사용해도 됩니다.
> DB 연동 시에는 `remix_nodes.node_id`로 정규화합니다.

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
| data_source | enum | X | simulated / progress / api / crawler |

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
| parent_id | uuid | X | Parent ID (자동 매핑용) |
| variant_name | string | X | Variant 이름 |

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
**목적**: NotebookLM 결과를 **DB에 저장한 후** 공유용으로 동기화

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| parent_id | uuid | O | Parent ID |
| summary | text | O | 요약 |
| key_patterns | text | X | 상위 패턴/클러스터 라벨 |
| risks | text | X | 리스크 |
| created_at | datetime | O | 생성 시각 |

---

## 4) NotebookLM/Opal 활용 (기본)

### NotebookLM (Data Tables)
- Outlier Raw → 해석/라벨 → **Notebook Library(DB)**
- Evidence Sheet → NotebookLM 요약 → **Notebook Library(DB)**
- NotebookLM이 Sheets로 직접 출력하는 경우, **Sheet → DB ingest**로 SoR를 유지
- 결과는 **DB에 저장 후** 필요 시 Insights Sheet로 동기화

### Opal
- Evidence/Insights Sheet 입력 → Decision Sheet 생성
- 실험 계획과 리스크 요약을 자동 생산

> 없으면 n8n/백엔드에서 동일 로직으로 대체 가능

---

## 5) Pattern Library/Trace (옵션)
패턴은 엔진이며, NotebookLM은 패턴 후보를 **요약/라벨링**하는 보조 레이어입니다.

### 5.1 Pattern Library Sheet (옵션)
| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| pattern_id | uuid | O | 패턴 ID |
| name | string | O | 패턴명 |
| pattern_type | enum | O | hook / scene / subtitle / audio / pacing |
| description | text | X | 설명 |
| created_at | datetime | O | 생성 시각 |

### 5.2 Pattern Trace Sheet (옵션)
| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| trace_id | uuid | O | Trace ID |
| variant_id | uuid | O | 변주 ID |
| pattern_id | uuid | O | 패턴 ID |
| weight | float | X | 적용 강도 |
| evidence_note | text | X | 근거 메모 |
| created_at | datetime | O | 생성 시각 |

---

## 6) Capsule Node (옵션)
Capsule은 Opal/NotebookLM/Sheets를 감싼 **보안형 실행 노드**입니다.

### 6.1 Capsule Input/Output 계약
**Input**
- parent_id, evidence_snapshot, pattern_lift_summary
- insights_summary (NotebookLM 요약)
- library_entry_id (Notebook Library 참조)
- constraints (budget/time/brand guardrails)

**Output**
- decision_json (GO/STOP/PIVOT + next_experiment)
- decision_sheet_row_id
- audit_log_id

> 내부 체인은 서버에서만 실행되며, UI에는 입력/출력만 노출합니다.

### 6.2 Guide Node 표시 규칙
- Capsule Output이 있으면 **Guide Node**가 자동 생성됨
- Guide Node는 **숏폼 브리프(훅/샷/오디오/템포)**만 노출
- 긴 설명/토론 로그는 **접힘 상태**로 유지

---

## 7) Debate 실행 조건 (옵션)
Debate는 아래 조건에서만 실행:
- Top1 vs Top2 점수 차 < 0.03
- 샘플 수 부족(Tracking < 10일)
- 리스크가 큰 카테고리(브랜드/법적 민감 영역)

---

## 8) Canvas 템플릿 (MVP)

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

### 템플릿 D: Cluster → Pattern → Decision (옵션)
```
[Outlier Cluster] → [Pattern Library] → [Evidence Table] → [Decision Summary]
```

---

## 9) 출력 형식 (UI 최소 기준)
기본 화면:
- 결론 5줄
- Evidence Table
- Progress(14일)

Pro/팀 리드:
- Debate 전문 보기(접힘)
- Evidence/Decision 히스토리 다운로드
