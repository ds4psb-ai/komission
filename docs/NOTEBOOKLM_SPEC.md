# NotebookLM Specification (통합 문서)

**작성**: 2025-12-30  
**통합**: 14_NOTEBOOK_LIBRARY_NODE_SPEC + 17_NOTEBOOKLM_LIBRARY_STRATEGY + 18_ENTERPRISE_INTEGRATION

---

## 1) 역할 정의 (Positioning)

- **NotebookLM = Pattern Engine**: Source Pack 기반 **불변 규칙 + 변주 포인트** 합성
- **SoR는 DB**: NotebookLM 결과는 반드시 **DB-wrapped** 후 사용
- **패턴 경계 원칙**: `cluster_id`는 **VDG/DB 기준선**으로 고정 (NotebookLM이 결정 안 함)
- **목적**: 정답 생성 ❌ → 패턴 합성 + 실행 가이드 보강 ✅

---

## 2) 2025 NotebookLM 기능 활용

| 기능 | 활용 방식 |
|------|----------|
| **Ultra (600 Sources)** | Mega-Pack 모드로 다중 클러스터 통합 |
| **Deep Research** | 외부 소스 보강용 (허용 도메인만) |
| **Studio 다중 출력** | Creator용/Business용/Ops용 분리 |
| **Data Tables → Sheets** | 산출물 DB-wrapped 자동화 |
| **Enterprise API** | 노트북 생성/공유/정리 자동화 |

---

## 3) 라이브러리 구조 (Notebook Topology)

### 3.1 기본 단위
```
1 노트북 = cluster_id + temporal_phase
예) hook-2s-textpunch_T1
```

### 3.2 분할 규칙
| 조건 | 분할 방식 |
|------|----------|
| 기본 | `cluster_id + temporal_phase` |
| 소스 50개 초과 | 변주 타입(hook/audio) 분리 |
| 시간창 확장 | 월 단위 추가 분할 |

### 3.3 네이밍 규칙
```
NL_{platform}_{category}_{cluster_id}_{temporal_phase}_v{n}
예) NL_tiktok_beauty_hook-2s-textpunch_T1_v2
```

---

## 4) Source Pack 스펙

### 4.1 Pack 파일 구성
| 파일 | 내용 |
|------|------|
| `cluster_summary.docx` | 패턴 정의 + 핵심 시그니처 3개 |
| `variants_table.xlsx` | Depth1/2 성공/실패 + 메트릭 |
| `evidence_digest.docx` | Evidence Snapshot + Failure modes |
| `comment_samples.md` | 상위 댓글 10~30개 (태깅 완료) |

### 4.2 Comment Evidence 규칙
```
[likes] [lang] [tag] comment text
```
- 태그: `hook`, `payoff`, `product_curiosity`, `confusion`, `controversy`
- 언어 우선: `ko > en > others`
- 댓글 없으면: `NO_COMMENTS_AVAILABLE` 추가

### 4.3 생성 커맨드
```bash
python backend/scripts/build_notebook_source_pack.py \
  --cluster-id CLUSTER_ID \
  --temporal-phase T1 \
  --output-dir /path/to/packs
```

---

## 5) 노드 모듈 구조

| 노드 타입 | 입력 | 출력 |
|----------|------|------|
| **Notebook Source Node** | outlier_url, platform, category | analysis_schema_id |
| **Notebook Library Node** | analysis_schema_id or parent_id | library_entry_id, cluster_id |
| **Evidence Node** | parent_id + library_entry_id | evidence_snapshot |
| **Capsule Node** | evidence_snapshot + library_summary | short-form brief |
| **Template Node** | capsule_output + creator_profile | 실행 템플릿 |

---

## 6) 패턴 합성 프롬프트 프로토콜

### 6.1 Prompt A: Invariant Extraction
```
Source Pack의 Parent vs Kids를 비교하여:
1) invariant_rules: 모든 성공 변주에서 공통으로 유지된 규칙
2) must_keep: Hook/Pacing/Payoff 필수 요소
3) citations: 근거 소스 참조

JSON 형식으로 출력
```

### 6.2 Prompt B: Mutation Strategy
```
성공/실패 변주를 비교하여:
1) success_variables: 성공에 기여한 변수
2) failure_variables: 실패를 유발한 변수
3) next_depth_recommendations: 다음 Depth 변주 추천 3개

JSON 형식으로 출력
```

### 6.3 Prompt C: Failure Modes
```
실패 사례만 분석하여:
1) common_failure_patterns: 공통 실패 패턴
2) do_not_list: 절대 하지 말아야 할 요소

JSON 형식으로 출력
```

---

## 7) Pattern Retrieval Standard (L1/L2)

### 7.1 검색 단계
| 단계 | 역할 |
|------|------|
| **L0 Guardrails** | platform/category/temporal_phase 필터 |
| **L1 Hybrid** | BM25 + 벡터 → 후보 50-100개 |
| **L2 Reranker** | fit/evidence/quality/recency/risk 피처 |

### 7.2 리랭커 피처
- `fit_score`: persona/category/product_slot 일치
- `evidence_strength`: source_count + variant_lift
- `recurrence_score`: 과거 패턴 유사도 (confirmed만)

---

## 8) Enterprise API 연동

### 8.1 Notebook Registry (DB)
```sql
CREATE TABLE notebooklm_registry (
  id UUID PRIMARY KEY,
  cluster_id TEXT,
  temporal_phase TEXT,
  source_pack_id UUID,
  notebook_id TEXT,           -- NotebookLM ID
  status TEXT,                -- planned/created/shared/archived/deleted
  created_at TIMESTAMP,
  run_id TEXT
);
```

### 8.2 라이프사이클 상태
1. `planned` → 2. `created` → 3. `shared` → 4. `archived` → 5. `deleted`

### 8.3 자동화 플로우
```bash
# 생성
python backend/scripts/notebooklm_create.py --cluster-id CLUSTER_ID

# 정합성 점검
python backend/scripts/notebooklm_reconcile.py

# 정리
python backend/scripts/notebooklm_cleanup.py --older-than 90d
```

---

## 9) DB 스키마 (권장)

### 9.1 notebook_library
```sql
CREATE TABLE notebook_library (
  id UUID PRIMARY KEY,
  source_url TEXT,
  platform VARCHAR(50),
  category VARCHAR(50),
  analysis_schema JSONB,
  summary JSONB,              -- NotebookLM pattern output
  cluster_id VARCHAR(100),
  temporal_phase VARCHAR(10),
  source_pack_id UUID,
  created_at TIMESTAMP
);
```

### 9.2 notebook_source_packs
```sql
CREATE TABLE notebook_source_packs (
  id UUID PRIMARY KEY,
  cluster_id VARCHAR(100),
  temporal_phase VARCHAR(10),
  pack_type VARCHAR(50),
  drive_file_id TEXT,
  source_version VARCHAR(50),
  created_at TIMESTAMP
);
```

---

## 10) 운영 규칙

### 10.1 업데이트 정책
- **주 1회 갱신** (신규 승자 변주 반영)
- Pattern Lift 급상승 시 즉시 갱신

### 10.2 품질 지표
| 지표 | 설명 |
|------|------|
| Cluster Coverage | 패턴 대비 노트북 생성 비율 |
| Update Freshness | 마지막 갱신일 7일 이내 비율 |
| Actionability | Guide에서 실제 적용된 변주 비율 |

### 10.3 실패 방지 원칙
- NotebookLM 결과는 **직접 노출 금지**
- 항상 **DB 래핑 + 사람이 최종 검토**
- 소스가 오래되면 **즉시 폐기/재생성**

---

## 11) Reference

- [01_VDG_SYSTEM.md](01_VDG_SYSTEM.md) - VDG 시스템
- [06_PIPELINE_PLAYBOOK.md](06_PIPELINE_PLAYBOOK.md) - 파이프라인 운영
- [15_TEMPORAL_VARIATION_THEORY.md](15_TEMPORAL_VARIATION_THEORY.md) - 시간축 이론
