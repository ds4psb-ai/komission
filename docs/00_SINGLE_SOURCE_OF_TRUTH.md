# Single Source of Truth (SoR) Rules

**작성**: 2026-01-07  
**목표**: Komission의 “단일 진실(SoR)”과 계약/라인리지/운영 경계를 문서로 고정한다.  
**적용 범위**: 모든 수집/분석/클러스터/NotebookLM/Opal/캔버스/증거/의사결정 파이프라인

---

## 1) 핵심 원칙 (불변)
1. **DB가 SoR**: 의사결정/증거/클러스터/가이드의 진실은 DB에만 기록된다.
2. **Sheets는 ops/share bus**: 승인/공유/협업용 버스이며 SoR가 아니다.
3. **NotebookLM/Opal 출력은 DB‑wrapped**: 결과는 반드시 구조화/버전/리비전 후 DB에 저장된다.
4. **Canvas는 I/O만 노출**: 내부 체인/프롬프트/로직은 노출하지 않는다.

---

## 2) 진실 소유(Truth Ownership) 맵

| 도메인 오브젝트 | SoR | 쓰기 경로 | 읽기 경로 | 비고 |
| --- | --- | --- | --- | --- |
| Outlier Raw | DB | 크롤러/수동 ingest | 운영 UI/Sheet | raw payload는 DB 보관 |
| Outlier Canonical | DB | 정규화 파이프라인 | UI/분석 | `(platform, external_id)` upsert |
| Metrics Snapshot | DB | 수집/업로드 | Evidence/RL | 시간축 스냅샷 분리 |
| VDG Edge (candidate/confirmed) | DB | VDG 파이프라인 | Graph/Decision | `confidence + evidence_json` 필수 |
| Pattern Cluster Boundary | DB | 클러스터링 서비스 | NotebookLM Pack | 경계는 코드/DB가 고정 |
| Source Pack (metadata) | DB | Pack builder | NotebookLM | 실제 파일은 Drive, 메타는 DB |
| NotebookLM/Opal Output | DB | ingest/auto wrap | UI/Decision | 요약/라벨/가이드 구조체 |
| Evidence Snapshot | DB | Evidence Runner | Decision/UI | Sheets는 ops 공유만 |
| Decision Object | DB | Decision Runner | UX/RL | Debate는 부록 artifact |
| Template/Capsule | DB | Template Seed/Version | Canvas | 실행 이력/피드백 포함 |
| Run/Artifact/Lineage | DB | 모든 파이프라인 | Ops Console | run_id/inputs_hash 필수 |
| NotebookLM Notebook | 외부 | NotebookLM API | 관리 UI | DB에 registry 매핑만 저장 |

---

## 3) 쓰기 규칙 (SoR Write Rules)
- **DB 외부 출력은 SoR가 아니다.** Sheets/NotebookLM/Opal 결과는 반드시 DB에 래핑한다.
- 모든 쓰기는 **run_id + inputs_hash + schema_version + idempotency_key**를 포함한다.
- 동일 입력 재실행 시 **중복 데이터가 아닌 revision**으로 기록한다.

---

## 4) NotebookLM 패턴 엔진 정책
- **NotebookLM은 패턴 엔진**으로 적극 활용한다.
- **패턴 경계(cluster_id)는 VDG/DB 기준선**으로 고정한다.
- Source Pack은 `cluster_id + temporal_phase + 성공/실패 샘플`로 구성한다.
- NotebookLM 출력은 **Pattern Library/Notebook Library 구조체로 DB‑wrapped**한다.

---

## 5) 품질/검증 게이트
- 모든 핵심 IO는 **JSON Schema 기반 계약**을 따른다.
- ingest 단계에서 **검증 실패 시 fail‑closed** (조용히 진행 금지).
- 결과가 Evidence/Decision/RL로 흐르려면 **검증 통과**가 선행 조건이다.

---

## 6) 라인리지/재현성 규칙
- 모든 파이프라인은 **입력 → 출력 → 결정** 흐름을 추적 가능해야 한다.
- 최소 기준: `run_id`, `artifact_id`, `inputs_hash`, `schema_version`, `model_version`.
- Evidence/Decision은 **어떤 입력팩과 근거**에서 나왔는지 역추적 가능해야 한다.

---

## 7) 변경 규칙
- SoR 규칙 변경 시 **반드시** 아래 문서를 함께 갱신한다:
  - `docs/15_FINAL_ARCHITECTURE.md`
  - `docs/00_DOCS_INDEX.md`
  - `docs/07_PIPELINE_PLAYBOOK.md`
- 스키마 버전 변경 시 **migration/validator/ingest**를 동시에 업데이트한다.

---

## 8) 체크리스트 (SoR 판단)
다음 중 하나라도 “아니오”라면 SoR가 아니다.
1. DB에 기록되었는가?
2. run_id/inputs_hash가 있는가?
3. schema_version이 있는가?
4. 재실행 시 중복이 아닌가?
5. Evidence/Decision에서 역추적 가능한가?
