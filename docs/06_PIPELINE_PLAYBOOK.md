# Pipeline Playbook (최신)

**작성**: 2025-12-28
**목표**: Evidence Loop 운영 단계를 표준화

---

## 1) 파이프라인 단계 요약
| 단계 | 트리거 | 입력 | 출력 |
| --- | --- | --- | --- |
| 수집 | 수동 입력/크롤링 | Outlier URL | `outlier_items` |
| 동기화 | 수동 실행 | DB Outliers | `VDG_Outlier_Raw` |
| 댓글 | 수동/자동 | Outlier Raw | `best_comments` |
| 해석 | 코드 기반 분석 + 클러스터링 | Outlier Raw + best_comments | `notebook_library` |
| 후보 선정 | 규칙/수동 | Outlier Raw + Notebook Library | `VDG_Parent_Candidates` |
| 승격 | Curator 승인 | 후보 | `remix_nodes`(Parent) |
| 분석 | 선택 실행 | Parent | 분석 요약 |
| Evidence | 주간/수동 | Progress | `VDG_Evidence` |
| Decision | 주간/수동 | Evidence | `VDG_Decision` |
| 템플릿 시드 | 선택 실행 | Notebook Library + Decision | `VDG_Template_Seeds` |
| 실행 | 승인 후 | Decision | Capsule/Template 실행 |

---

## 2) 최소 운영 루프 (MVP)
1. Outlier 수집 (수동 입력)
2. DB → Sheet 동기화
3. 영상 해석(코드) + 클러스터링 → Notebook Library 저장
4. **NotebookLM Source Pack 생성** (cluster_id + temporal_phase 단위)
5. **NotebookLM 패턴 합성** (불변 규칙 + 변주 포인트)
6. Evidence Runner 실행
7. Opal 템플릿 시드 생성(선택)
8. Decision 검토 후 템플릿 적용
9. O2O/체험단 운영은 Phase 2+에서 활성화 (MVP는 타입 게이팅 표시만)

## 2.1 Comment Evidence Standard (HITL)
댓글은 바이럴 DNA의 **증거 레이어**로 취급한다.  
목표는 "많이 수집"이 아니라 **핵심 반응(원인/효과)**을 정제해 VDG/NotebookLM에 연결하는 것이다.

### 추출 우선순위
- YouTube: Data API v3 → yt-dlp
- TikTok: comment/list 캡처 → DOM 추출 → yt-dlp
- Instagram: yt-dlp

### 정제 규칙
- 언어 우선: `ko > en > others`
- 중복/노이즈 제거: 동일 문구, 이모지/짧은 감탄사, "first/고정/인정"류 제거
- 상위 댓글 10~30개만 유지 (분석은 10, Pack은 10~30)

### 저장/전파
1) `OutlierItem.best_comments`에 원본 저장  
2) VDG `audience_reaction.best_comments`로 병합  
3) `comment_samples.md`로 Pack에 포함

### HITL 가이드
- S-tier 후보/핵심 클러스터는 댓글 5개 이상 **수동 확인**
- 댓글은 `hook`, `payoff`, `product_curiosity`, `confusion`, `controversy`로 태깅
- 태깅 결과는 **Evidence/Decision**에 근거로 활용

### 실패 처리
- 차단/비활성 시 `comments_missing_reason` 기록 후 파이프라인은 계속 진행
  - ex) `blocked`, `no_comments`, `login_wall`

## 2.2 Comment → VDG → Pack 보완 설계 (필수)
1. **추출 우선순위 통일**: TikTok은 comment/list를 기본 경로로 고정  
2. **정제/태깅 파이프라인 고정**: 언어 우선, 중복 제거, 신호 태그 부여  
3. **VDG 병합 규칙 명시**: `audience_reaction.best_comments`에 주입  
4. **메트릭 분리**: `comment_count`는 실제 수, 샘플 수는 별도 보관  
5. **Pack 반영**: `comment_samples.md` 생성 후 NotebookLM 입력에 포함

참고:
- TikTok 베스트 댓글은 comment/list 캡처를 **기본 경로**로 사용하고, 실패 시 DOM → yt-dlp로 폴백.
- bdturing 차단 시 `scripts/export_tiktok_cookies.py`로 세션 갱신 후 Secret Manager 업데이트.
- **Cloud Run 설정**: `TIKTOK_COOKIE_FILE=/secrets/tiktok_cookies.json`, `TIKTOK_PROXY=http://34.42.221.145:8888`

### 실행 커맨드
```bash
python backend/scripts/pull_provider_csv.py --config backend/provider_sources.json
python backend/scripts/ingest_outlier_csv_db.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_notebook_library.py --json /path/to/notebooklm.json
python backend/scripts/ingest_notebook_library_sheet.py --sheet VDG_Insights
python backend/scripts/sync_notebook_library_to_sheet.py --limit 200
python backend/scripts/build_notebook_source_pack.py --cluster-id CLUSTER_ID
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
python backend/scripts/run_selector.py
python backend/scripts/run_real_evidence_loop.py
PYTHONPATH=backend python backend/scripts/export_tiktok_cookies.py  # 쿠키 갱신
```

### One-shot (Provider → Candidates)
```bash
python backend/scripts/run_provider_pipeline.py --config backend/provider_sources.json
```

---

## 3) 단계별 체크리스트
**수집**
- 중복 URL 제거 ← **DB UNIQUE 제약조건 적용됨 (2024-12-30)**
- `video_url` 기준 중복 체크 (API + DB 이중 방어)
- platform/category 채워짐

**후보 선정**
- 기준: 조회수/성장률/최근성
- status = candidate

**승격 [Updated 2024-12-30]**
- Parent RemixNode 생성 확인
- node_id 기록
- **승격 옵션**:
  - `[승격]`: 일반 RemixNode 생성
  - `[체험단 선정]`: RemixNode + `campaign_eligible=True` (O2O 후보군)

**Evidence/Decision**
- Evidence Sheet row 생성
- Decision Sheet 생성 확인

---

## 4) NotebookLM/Opal 사용 원칙
- NotebookLM: **Pattern Engine**으로 적극 활용
  - Source Pack → 불변 규칙 + 변주 포인트 합성
  - **패턴 경계(cluster_id)는 VDG/DB 기준선으로 고정**
  - NotebookLM이 패턴을 결정/정의하지 않음
  - 결과는 **DB-wrapped** 후 사용
- Opal: Decision 생성 **보조**
- SoR는 DB, Sheet는 **운영 버스**
- **필수 추적**: 모든 파이프라인에 `run_id`, `inputs_hash`, `idempotency_key` 필수

---

## 5) NotebookLM Source Pack 운영 프로토콜 (2025-12 확정)

### 5.1 Pack 생성 기준
- **기본 단위**: `cluster_id + temporal_phase`
- **분할 조건**:
  - 소스 50개 초과 → 변주 타입(hook/audio) 분리
  - 시간창 확장 → 월 단위 추가 분할

### 5.2 Pack 파일 구성

| 파일 | 내용 |
| --- | --- |
| `cluster_summary.docx` | 패턴 정의, 핵심 시그니처 3개, temporal_phase |
| `variants_table.xlsx` | Depth1/2 성공/실패, 메트릭 |
| `evidence_digest.docx` | Evidence Snapshot, Failure modes |
| `comment_samples.md` | 상위 댓글 10~30개 |

### 5.3 생성 커맨드
```bash
python backend/scripts/build_notebook_source_pack.py \
  --cluster-id CLUSTER_ID \
  --temporal-phase T1 \
  --output-dir /path/to/packs
```

### 5.4 NotebookLM 결과 추출

**권장 프롬프트:**

1. **Invariant Extraction**: 불변 규칙 + 필수 유지 요소
2. **Mutation Strategy**: 성공/실패 변수 + 다음 Depth 추천
3. **Failure Modes**: 공통 실패 패턴 + 금지 요소

> 상세 프롬프트는 `docs/NOTEBOOKLM_SPEC.md` 섹션 9 참고

### 5.5 결과 DB 래핑
```bash
python backend/scripts/ingest_notebook_library.py \
  --json /path/to/notebooklm_output.json
```

---

## 6) NotebookLM Enterprise API 자동화 (선택)

### 6.1 자동화 가능 작업

| API | 용도 |
| --- | --- |
| `notebooks.create` | cluster_id 기준 자동 생성 |
| `notebooks.share` | 운영자/검토자 공유 |
| `listRecentlyViewed` | 누락/정합성 점검 |
| `batchDelete` | 폐기 정책 적용 |

### 6.2 연동 스크립트 (예정)
```bash
python backend/scripts/notebooklm_create.py --cluster-id CLUSTER_ID
python backend/scripts/notebooklm_reconcile.py
python backend/scripts/notebooklm_cleanup.py --older-than 90d
```

> 상세 스펙은 `docs/NOTEBOOKLM_SPEC.md` 참고

---

## 7) Temporal Recurrence / Pattern Lineage

트렌드가 휩쓸리면 유사한 outlier + multi-depth 변주가 10개 내외로 생성되며,
이 파도는 종종 1~2년 전의 parent-kids 패턴과 매우 유사하다.
**Temporal Recurrence**는 이 현상을 자동으로 감지하고 과거 패턴과 연결하는 시스템이다.

### 7.1 파도 감지 트리거
과거 매칭은 항상 실행하지 않고, **트렌드 파도 조건**이 충족될 때만 활성화한다:

- 동일 cluster에서 **7~14일 내 변주 ≥ 10**
- `burstiness_index` 급상승
- `novelty_decay_score`는 낮은데 성과는 상승

### 7.2 Recurrence Score 계산 (v1)
```
recurrence_score =
  0.35 * microbeat_sim
+ 0.20 * hook_genome_sim
+ 0.15 * focus_window_sim
+ 0.10 * audio_format_sim
+ 0.10 * comment_signature_sim
+ 0.10 * product_slot_sim
```

### 7.3 임계값 설계 (3단계)
| 상태 | 임계값 | 처리 |
| --- | --- | --- |
| **confirmed** | ≥ 0.88 | 사용자 노출 가능, L2 리랭커에 반영 |
| **candidate** | 0.80 ~ 0.88 | DB에만 기록, 사용자 노출 금지 |
| **미매칭** | < 0.80 | 기록하지 않음 |

### 7.4 하드 게이트 (확정 조건 강화)
confirmed로 승격하려면 아래 **3개 중 2개 이상** 충족 필요:
- `microbeat_sim >= 0.80`
- `comment_signature_sim >= 0.60`
- `hook_genome_sim == 1.0`

### 7.5 Shadow Mode (데이터 부족 시 운영)
- **후보(candidate)**: DB에만 기록, 사용자 노출 금지
- **승격 조건**: 동일 후보가 2회 이상 반복 매칭 또는 `recurrence_score >= 0.90` + 하드 게이트 2/3 충족
- **자동 보정**: 신규 데이터 300개 이상 또는 주 1회, within/cross 분포 기반 임계값 재계산

### 7.6 과거 패턴 매칭 결과 활용
- **confirmed** 재등장은 `L2 리랭커`의 보조 피처로 사용
- **candidate**는 내부 로그만 기록, 리랭커에 반영 금지
- confirmed 패턴에는 "과거 성공 패턴과 동일 구조" 근거 표시

### 7.7 운영 흐름 (요약)
1. 변주 파도 트리거 감지
2. 과거 패턴 후보 검색 (recurrence_score 계산)
3. `candidate`로 `pattern_recurrence_links` 테이블에 기록
4. 2회 이상 반복 or 0.90 이상이면 `confirmed`
5. confirmed는 `pattern_clusters.ancestor_cluster_id`에 lineage로 기록
6. L2 리랭커에 `recurrence_score` 신호로 반영

### 실행 스크립트 (미구현)

> [!NOTE]
> 아래 스크립트는 **구현 예정**이며 현재 repo에 없습니다.
> 스키마와 문서가 먼저 확정되었고, 파이프라인 로직은 다음 단계에서 구현됩니다.

```bash
# 예정:
# python backend/scripts/detect_recurrence_wave.py --cluster-id CLUSTER_ID
# python backend/scripts/match_ancestor_patterns.py --cluster-id CLUSTER_ID
```

---

## 8) 한 줄 요약

**VDG가 경계를 고정하고, NotebookLM이 패턴을 합성하며, DB가 증거를 잠그는 구조**가 최선이다.
