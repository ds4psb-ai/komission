# Notebook Library + Node Module Spec (최신)

**작성**: 2026-01-07
**목표**: 코드 기반 영상 해석 스키마를 **Notebook Library**로 축적하고, NotebookLM 요약은 보조 레이어로 사용한다. 이를 **노드 모듈/템플릿**으로 연결하여 Komission 철학(Evidence Loop)을 유지하면서 고도화한다.

---

## 1) 핵심 철학 (Notebook Library 특화)
- 기본 원칙은 `docs/00_DOCS_INDEX.md`, `docs/15_FINAL_ARCHITECTURE.md`를 따른다.
- NotebookLM은 **요약/라벨/근거 보조 레이어**이며 결과는 **DB로 래핑**한다.
- 소스는 **정적 스냅샷**이며, 노트북당 소스 제한을 고려해 클러스터를 분할한다.
- 템플릿 학습은 **창작자/PD/작가 커스텀 로그**를 축적해 개선한다.

---

## 2) Notebook Library 역할 정의
### 2.1 무엇을 저장하는가?
- **코드 기반 해석 스키마**(훅/씬/오디오/템포/텍스트 패턴)
- **Parent → Kids 변주 기록**의 요약
- **실행 가능한 숏폼 브리프**(캡슐 출력 스키마에 맞춤)
- (선택) NotebookLM 요약/라벨

### 2.2 무엇을 하지 않는가?
- 원본 영상/민감 데이터 직접 저장 금지
- 토큰/비공개 키 추출 금지
- 외부 모델의 내부 추론/비공개 데이터 사용 금지

### 2.3 2025 NotebookLM 업데이트 반영
- **Deep Research**: 외부 소스 수집은 *보강용*으로만 사용
- **새 소스 타입**: Sheets/Drive URL/이미지/.docx 지원
- **Studio 다중 출력**: 노트북당 다양한 Output(브리프/근거/체크리스트) 생성 가능
- **Video Overviews**: 내부 교육/브리핑용으로 활용

---

## 3) 노트북 기반 노드 모듈 구조

### 3.1 노드 타입
1) **Notebook Source Node**
- 입력: outlier_url, platform, category
- 출력: analysis_schema_id
- 역할: **코드 기반 영상 해석** 파이프라인 실행 (NotebookLM 요약은 선택)

2) **Notebook Library Node**
- 입력: analysis_schema_id 또는 parent_id
- 출력: library_entry_id, cluster_id
- 역할: 유사 패턴 클러스터링, 라벨 생성

3) **Evidence Node**
- 입력: parent_id + library_entry_id
- 출력: evidence_snapshot
- 역할: Pattern Lift와 연결

4) **Capsule Node**
- 입력: evidence_snapshot + library_summary
- 출력: short-form brief (hook/shotlist/audio/timing/do_not)

5) **Template Node**
- 입력: capsule_output + creator_profile
- 출력: 실행 템플릿 (촬영/편집 체크리스트)

---

## 4) 역설계 기반 단계별 흐름 (구체 디테일)

### Step 1: Outlier 수집
- 수동 링크 입력 또는 외부 구독 데이터 ingest
- `outlier_items` 저장 → `VDG_Outlier_Raw` 동기화

### Step 2: 영상 해석 스키마 생성 (코드 기반)
- **해석 목표**: 훅 구조, 전개 리듬, 오디오, 텍스트 패턴 스키마 추출
- 출력은 **분석 스키마**로 저장 (SoR)
- 권장 모델: Gemini 3.0 Pro (단일 모델 고정)
- 출력은 **JSON Schema**로 강제하여 재현성을 확보한다

### Step 2.5: Notebook Source Pack 생성 (자동)
- 분석 스키마/증거/결정 요약을 **Sheets/Docx로 자동 출력**
- NotebookLM 소스는 **이 Pack에서만** 가져오도록 제한

### Step 3: 유사도 클러스터링 + 요약(선택)
- 유사 패턴을 **클러스터**로 묶어 라벨링
- NotebookLM 요약은 **클러스터 설명 보조**로만 사용
- 예: `Cluster: Hook-2s-TextPunch` / `Scene: Kitchen-Zoom` / `Audio: Viral-120bpm`
 - (선택) Deep Research로 외부 소스 보강 (허용 도메인만)

### Step 4: Evidence Loop 결합
- 클러스터 결과를 Evidence 요약에 연결
- Pattern Lift 계산 시 Notebook 라벨을 보조 피처로 사용

### Step 5: Capsule Output 생성
- Evidence + Notebook Library 요약을 합쳐 **실행 브리프** 생성
 - 필요 시 Opal 템플릿 시드를 함께 반영
- UI에서는 **Guide Node**로 표시

### Step 6: Template 커스터마이징 학습
- 창작자/PD/작가가 수정한 템플릿 로그를 축적
- 성과 반영(views/retention/engagement)
- 강화학습(정책 개선) 기반으로 **템플릿 기본값 업데이트**

---

## 5) 데이터 모델 (권장)

### 5.1 Notebook Library
```sql
CREATE TABLE notebook_library (
  id UUID PRIMARY KEY,
  source_url TEXT,
  platform VARCHAR(50),
  category VARCHAR(50),
  analysis_schema JSONB,     -- code-based hook/scene/audio/text schema
  summary JSONB,             -- optional NotebookLM summary
  cluster_id VARCHAR(100),
  parent_node_id UUID,       -- optional link to Parent
  created_at TIMESTAMP
);
```

### 5.2 Template Version + Feedback
```sql
CREATE TABLE template_versions (
  id UUID PRIMARY KEY,
  template_id UUID,
  version INT,
  base_params JSONB,
  created_at TIMESTAMP
);

CREATE TABLE template_feedback (
  id UUID PRIMARY KEY,
  template_version_id UUID,
  creator_id UUID,
  edits JSONB,
  metrics JSONB,
  created_at TIMESTAMP
);
```

### 5.3 Policy/Optimization (RL-lite)
```sql
CREATE TABLE template_policy (
  id UUID PRIMARY KEY,
  template_id UUID,
  policy_json JSONB,
  updated_at TIMESTAMP
);
```

### 5.4 Notebook Source Pack (NotebookLM 입력)
```sql
CREATE TABLE notebook_source_packs (
  id UUID PRIMARY KEY,
  cluster_id VARCHAR(100),
  pack_type VARCHAR(50), -- docx | sheet
  drive_file_id TEXT,
  source_version VARCHAR(50),
  created_at TIMESTAMP
);
```

---

## 6) 강화학습/최적화 방식 (현실적 적용)
**목표**: 복잡한 RL보다 **성과 기반 개선(RL-lite)** 적용

- **Bandit/Ranking 기반**
  - 템플릿 A/B 성과 비교 → 승자 확률 업데이트
- **Pairwise Feedback**
  - 사용자 편집 로그를 “선호 데이터”로 변환
- **정책 업데이트 주기**
  - 주간 배치 업데이트 (Evidence Snapshot과 동기화)

> LLM은 **생성 보조**, 핵심은 **템플릿 파라미터의 지속 개선**이다.

---

## 7) UI/UX 적용 원칙
- Notebook Library는 **백그라운드 도서관**으로 노출
- 사용자는 **Guide Node 결과**만 본다
- 템플릿 수정은 **간단 슬롯(5%)만 노출**
- Studio 다중 출력은 **내부 운영용**으로만 사용

---

## 8) 리스크/정책
- 외부 플랫폼 데이터는 **약관 준수**
- NotebookLM 결과는 **참고/요약 레이어**로만 사용
- 토큰/비공개 키 추출 금지

---

## 9) 적용 우선순위
1. Notebook Library 테이블 생성
2. Outlier → 분석 스키마 연결
3. 클러스터링 + (선택) NotebookLM 요약 연결
4. Capsule Output에 Notebook Library 요약 반영
4. 템플릿 커스터마이징 로그 축적
5. RL-lite 정책 업데이트

---

## 10) 결론
Notebook Library는 **Komission 철학(Evidence Loop)**을 유지하면서, 실행 브리프와 템플릿을 고도화하는 **가속 레이어**다. 우리는 토론이나 장문 가이드가 아니라 **숏폼 실행 브리프 + 증거 기반 템플릿 학습**으로 차별화한다.
