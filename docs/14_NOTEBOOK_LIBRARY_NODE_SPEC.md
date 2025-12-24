# Notebook Library + Node Module Spec (최신)

**작성**: 2026-01-07
**목표**: 인기 숏폼 해석을 **NotebookLM 기반 노트북 라이브러리**로 축적하고, 이를 **노드 모듈/템플릿**으로 사용하여 Komission 철학(Evidence Loop)을 유지하면서 고도화한다.

---

## 1) 핵심 철학 (유지해야 할 원칙)
- **Evidence Loop 우선**: 데이터/증거가 먼저, LLM은 보조
- **DB가 SoR, NotebookLM은 도서관**: 노트북은 참고/요약/클러스터링 레이어
- **캡슐화**: 내부 체인은 숨기고 **입출력만 노출**
- **템플릿 학습**: 창작자/PD/작가의 커스텀 파이프라인 데이터를 축적해 개선

---

## 2) Notebook Library 역할 정의
### 2.1 무엇을 저장하는가?
- **인기 영상 해석 결과**(훅/씬/오디오/템포/텍스트 패턴)
- **Parent → Kids 변주 기록**의 요약
- **실행 가능한 숏폼 브리프**(캡슐 출력 스키마에 맞춤)

### 2.2 무엇을 하지 않는가?
- 원본 영상/민감 데이터 직접 저장 금지
- 토큰/비공개 키 추출 금지
- 외부 모델의 내부 추론/비공개 데이터 사용 금지

---

## 3) 노트북 기반 노드 모듈 구조

### 3.1 노드 타입
1) **Notebook Source Node**
- 입력: outlier_url, platform, category
- 출력: raw_notes_id
- 역할: NotebookLM에 요약/해석 요청 (기본)

2) **Notebook Library Node**
- 입력: raw_notes_id 또는 parent_id
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

### Step 2: NotebookLM 요약 생성
- **요약 목표**: 훅 구조, 전개 리듬, 오디오, 텍스트 패턴 추출
- 출력은 **노트북 엔트리**로 저장 (참고용)

### Step 3: Notebook Library 정규화
- 유사 패턴을 **클러스터**로 묶어 라벨링
- 예: `Cluster: Hook-2s-TextPunch` / `Scene: Kitchen-Zoom` / `Audio: Viral-120bpm`

### Step 4: Evidence Loop 결합
- 클러스터 결과를 Evidence 요약에 연결
- Pattern Lift 계산 시 Notebook 라벨을 보조 피처로 사용

### Step 5: Capsule Output 생성
- Evidence + Notebook 요약을 합쳐 **실행 브리프** 생성
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
  summary JSONB,             -- hook/scene/audio/text patterns
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

---

## 8) 리스크/정책
- 외부 플랫폼 데이터는 **약관 준수**
- NotebookLM 결과는 **참고/요약 레이어**로만 사용
- 토큰/비공개 키 추출 금지

---

## 9) 적용 우선순위
1. Notebook Library 테이블 생성
2. Outlier → Notebook 요약 연결
3. Capsule Output에 Notebook 요약 반영
4. 템플릿 커스터마이징 로그 축적
5. RL-lite 정책 업데이트

---

## 10) 결론
NotebookLM 기반 노트북 라이브러리는 **Komission 철학(Evidence Loop)**을 유지하면서, 실행 브리프와 템플릿을 고도화하는 **가속 레이어**다. 우리는 토론이나 장문 가이드가 아니라 **숏폼 실행 브리프 + 증거 기반 템플릿 학습**으로 차별화한다.
