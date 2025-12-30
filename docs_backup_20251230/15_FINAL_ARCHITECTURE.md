# Komission 최종 아키텍처 (PEGL v1.0)

**작성**: 2026-01-07  
**기준**: consulting-20251226 / commit 55acf17  
**목표**: 최신 아키텍처 후퇴 없이, 프로덕션 완성 기준을 “코드/정책/운영”으로 잠근다.

---

## 1) 최종 결론 (한 줄)
**Fact는 Gemini, Pattern은 NotebookLM, 진실은 DB, 운영은 Evidence Loop**가 최선이다.

---

## 2) 불변 가드레일 (Architecture Non-Regression)
1. **DB = System of Record (SoR)**
2. **Sheets = ops/share bus** (승인/공유용, SoR 금지)
3. **NotebookLM/Opal 출력 = DB-wrapped + versioned**
4. **Canvas = I/O only** (내부 체인/로직 노출 금지)

---

## 3) 핵심 역할 정의 (최종)
- **Gemini 3.0 Pro**: 영상 1건을 해체하는 **Fact Interpreter**
- **VDG/클러스터링(코드)**: 패턴 경계/정합성/재현성 **기준선**
- **NotebookLM**: **Pattern Engine**  
  - Source Pack을 받아 **불변 규칙 + 변주 포인트**를 합성
  - 결과는 반드시 DB에 구조화 저장
- **Opal**: 템플릿/캡슐 설계 시드 + 운영 보조 UI
- **DB**: Fact/Pattern/Evidence/Decision/Lineage의 SoR

> NotebookLM은 “패턴 엔진”으로 적극 활용하되, **패턴 경계(cluster_id)는 VDG/DB 기준선으로 고정**한다.

---

## 4) Fact-to-Pattern 파이프라인 (최종 흐름)
```
Outlier 수집(구독/수동/API)
  → 댓글 증거 추출(best_comments, HITL)
  → Gemini 해석(VDG + audience_reaction)
  → VDG 유사도 클러스터링(패턴 경계 확정)
  → Source Pack 생성(cluster_id + temporal_phase)
  → NotebookLM 패턴 합성(Pattern Engine)
  → Pattern Library(DB-wrapped, revisioned)
  → L1/L2 Retrieval(Answer-First (For You) + EvidenceBar)
  → Evidence Loop(Decision Object)
  → Capsule/Template 실행(캔버스 I/O)
  → 성과/로그 → Bandit/RL-lite
```

---

## 5) 프로덕션 완성 정의 (Definition of Done)
1. **재현성**: 동일 입력이면 동일 결과 또는 revision으로 추적 가능
2. **복구 가능성**: 실패/재시도에도 데이터 오염 없음
3. **운영 가능성**: UI에서 루프 완주 + 실패/원인/재시도 가시화

---

## 6) Phase 0 — 가드레일을 “코드로” 강제
**목표**: 데모가 아닌 운영 가능한 시스템으로 잠금

**필수 고정**
- **Data Contract**: 모든 핵심 IO에 `schema_version` 강제
- **Validation Gate**: ingest 단계에서 품질 검증 자동화
- **Run/Artifact/Idempotency**: `run_id`, `artifact_id`, `idempotency_key`, `inputs_hash` 전 파이프라인 공통
- **Lineage 최소 표준**: job/run/dataset 관계를 DB 이벤트로 기록

**DoD**
- 같은 입력 재실행 시 중복/오염 없음
- 스키마가 깨지면 조용히 진행하지 않고 “명시적으로 실패”

---

## 7) Phase 1 — Outlier 수집을 “운영 가능한 수집 시스템”으로 고정
- Raw payload + normalized 분리
- canonical URL/ID 정규화
- metrics snapshot 분리(시간축)
- `(platform, external_id)` upsert 강제
- run log + 실패/재시도 기록
- source_mode(official/api/scrape) 고정

---

## 8) Phase 2 — Parent-Kids VDG 그래프를 증거 기반으로 확정
- Edge 테이블: `relation_type`, `confidence`, `evidence_json` 필수
- `candidate` → `confirmed/rejected` 분리
- depth/materialized path 캐시는 조회용
- 확정은 Evidence Loop에서만

---

## 9) Phase 3 — NotebookLM Pattern Engine 고정
### 9.1 Source Pack 스펙
- `source_pack_id`, `spec_version`, `inputs_hash`, `cluster_id`, `temporal_phase`
- 성공/실패 샘플을 함께 포함 (변주 포인트 추출 목적)

### 9.2 Pattern Library 스키마(최소)
- `pattern_id`, `source_pack_id`, `invariant_rules`, `mutation_strategy`, `citations`, `revision`

### 9.3 DB-wrapped 원칙
- NotebookLM 결과는 **직접 노출 금지**
- 반드시 구조화 → DB 적재 → UI/Decision에서만 사용

### 9.4 Comment Evidence Layer (HITL)
- 댓글은 **증거 레이어**로 취급한다 (많이 수집보다 핵심 반응 정제)
- `best_comments`는 Outlier에 저장되고, VDG `audience_reaction`에 병합
- Pack에는 `comment_samples.md`로 포함, Evidence/Decision 근거로 사용
- `comment_count`는 실제 수치만 기록 (샘플 수와 분리)

### 9.5 Pattern Retrieval Standard (L1 Hybrid → L2 Reranker)
- L0 Guardrails: 플랫폼/카테고리/temporal_phase 사전 필터
- L1: 키워드(BM25) + 벡터 하이브리드로 후보 풀 생성
- L2: fit/evidence/quality/recency/risk 피처로 리랭크
- 출력은 **근거(citations)** + **변주 슬롯**을 함께 제공

### 9.6 Temporal Recurrence / Pattern Lineage
- 재등장은 **배치 파이프라인**에서만 계산 (실시간 매칭 금지)
- `candidate → confirmed` 승격 구조 + recurrence_score 기록
- 댓글 반응 유사도(`comment_signature_sim`)를 재등장 확정에 반영

---

## 10) Phase 4 — Evidence Loop 상태머신 + Decision Object
**상태**: `queued → running → evidence_ready → decided → executed → measured`

**Debate 처리**
- Transcript는 부록 artifact
- **Decision Object(JSON)**만 1급 시민 (UX/RL 입력)

---

## 11) Phase 5 — RL-lite (Bandit-first)
- reward window: 1h / 24h / 7d
- 정책 적용은 “추천 우선순위”부터
- 자동 실행은 마지막

---

## 12) Phase 6 — UX 실적재 (루프 완주 UX)
- 운영자가 `Outlier → Graph → Guide → Experiment → Evidence`를 끊김 없이 완주
- **Answer-First (For You) + EvidenceBar(best comments + recurrence)**로 신뢰 확보
- **Session HUD + 단일 CTA + 실패 재시도/원인 보기** 중심
- Canvas는 I/O만 노출

---

## 13) 핵심 데이터 모델 (최소 집합)
- `Run`, `Artifact`, `OutlierRaw`, `Outlier`
- `VDG_Edge`(candidate/confirmed)
- `SourcePack`, `PatternLibrary`, `NotebookLibraryEntry`
- `PatternRecurrenceLink` (temporal lineage + recurrence_score)
- `CommentEvidence` (Outlier.best_comments + VDG.audience_reaction)
- `EvidenceEvent`, `DecisionObject`

---

## 14) P0 우선순위 (순서 고정)
1. Run/Artifact/Idempotency 공통 레이어
2. Outlier 정규화 + raw 보관 + upsert
3. VDG Edge(confidence/evidence) 스키마 고정
4. Source Pack spec + Pattern Library schema + revision 저장
5. Evidence Loop 상태머신 + Decision Object
6. Bandit(운영 우선순위 추천)
7. Ops Console + Session HUD 최소 적용

---

## 15) 한 문장 운영 원칙
**DB에 버전과 증거가 남지 않으면, 그건 기능이 아니라 데모다.**
