# NotebookLM Library Strategy (최신)

**작성**: 2026-01-07  
**목표**: NotebookLM의 각 노트북/클러스터를 **최대 가치 창출**에 맞게 설계/운영

---

## 1) 역할 정의 (Positioning)
- NotebookLM은 **요약/라벨/근거**를 만드는 **가속 레이어**
- **SoR는 DB**이며, NotebookLM 결과는 **DB로 래핑** 후 사용
- 목적은 “정답 생성”이 아니라 **패턴 이해 + 실행 가이드 보강**

---

## 2) 2025 최신 업데이트 반영 (핵심 기능)
**공식 업데이트 기준(2025)**: Deep Research, 새로운 소스 타입, Studio 다중 출력, Video Overviews, Public Notebooks

### 2.1 Deep Research
- 외부 소스를 자동 탐색/리포트 생성
- **원칙**: 클러스터 핵심은 내부 소스, **Deep Research는 보강용**
- **가드레일**: 허용 도메인 목록 기반(브랜드/플랫폼 공식 문서만)

### 2.2 소스 타입 확장
- **Google Sheets / Drive URL / 이미지 / .docx** 지원
- **전략**: DB에서 `Notebook Source Pack`을 만들고 Sheets/Docx로 자동 출력

### 2.3 Studio 다중 출력
- 노트북당 **여러 Output 생성 가능**
- **용도 분리**: Creator용(브리프), Business용(근거/리스크), Ops용(체크리스트)

### 2.4 Video Overviews
- 구조/프로세스 설명에 강함 (절차/단계/사례 요약)
- **용도**: 내부 교육/온보딩/캠페인 브리핑용

### 2.5 Public Notebooks
- 링크 공유 가능 (읽기 전용 상호작용)
- **원칙**: 기본은 비공개, **공개는 마케팅/홍보 목적에만 제한**

---

## 3) 라이브러리 구조 (Notebook Topology)
### 3.1 기본 단위 = Pattern Cluster Notebook
- **1 클러스터 = 1 노트북**
- 클러스터는 **Parent‑Kids(Depth1/Depth2)** 변주를 포괄
- 노트북 수는 1차적으로 **패턴 수(목표 600)**와 동일

### 3.2 분할 규칙
- **소스 50개 한도** 초과 시 **분할**
- 기준: **기간(월 단위)** or **하위 변주 타입(훅/오디오)**
  - 예: `Hook-v1` / `Hook-v2`, `Audio-v1` / `Audio-v2`

### 3.3 네이밍 규칙
```
NL_{platform}_{category}_{pattern}_{version}
예) NL_tiktok_beauty_hush-voice_v2
```

---

## 4) 노트북 구성 템플릿 (구성지게 만드는 뼈대)
### 4.1 요약 헤더 (Always‑on)
- **Pattern Definition** (한 줄 정의)
- **Signature** (Hook/Shot/Audio/Timing 핵심 3개)
- **Do / Don’t** (금지 요소 2개)

### 4.2 Evidence Digest
- **Top Variants** (Depth1/Depth2 상위 3개)
- **Pattern Lift** (상승률/유지율 요약)
- **Failure Modes** (실패 2~3개)

### 4.3 Adaptation Guide
- **Creator Persona 적용 가이드** (Phase 3)
- **제품/브랜드 제약** 반영 예시
- **다음 변주 추천** (Depth3 후보)

---

## 5) 입력 소스 규칙 (최대 가치 기준)
### 필수 소스
- Parent 영상 (원본)
- Depth1 상위 3개
- Depth2 상위 3개
- Evidence Snapshot 요약
- Decision Summary 요약

### 선택 소스
- 동일 패턴의 경쟁 플랫폼 사례
- 오디오/훅 변형 실험 로그

> **중요**: “많이 넣는 것”보다 **승자 변주+실패 변주 조합**이 가치가 큼

### 5.1 Notebook Source Pack 구성 (권장)
**목표**: NotebookLM 입력을 표준화하고 일관성을 보장한다.

**Pack 파일**
- `cluster_summary.docx` (Pattern Definition + Signature + Do/Don't)
- `evidence_digest.docx` (Top Variants + Lift + Failure Modes)
- `decision_summary.docx` (Next Experiment + Risks)
- `variants_table.xlsx` (Depth1/Depth2 핵심 지표)

**규칙**
- Pack은 **DB에서 자동 생성**되며, NotebookLM에는 Pack만 입력
- Deep Research는 **Pack에 없는 외부 근거 보강용**으로만 사용

---

## 6) 업데이트 정책 (운영 규칙)
- **주 1회 갱신** (신규 승자 변주 반영)
- **핵심 이벤트 발생 시 즉시 갱신**
  - Pattern Lift 급상승
  - 새로운 Depth2 승자 등장
  - 제품/브랜드 제약 변경

---

## 7) 출력 계약 (DB 래핑)
NotebookLM 출력은 항상 아래 구조로 변환되어 DB에 적재:
```json
{
  "cluster_id": "pattern_xxx",
  "summary": "...",
  "signature": {
    "hook": "...",
    "timing": "...",
    "audio": "..."
  },
  "top_variants": ["v1", "v2", "v3"],
  "failure_modes": ["...", "..."],
  "adaptation_rules": ["...", "..."],
  "recommended_next_variants": ["..."]
}
```

---

## 8) 활용 지점 (최대 가치)
- **Capsule Guide**: “실행 가능한 브리프” 강화
- **Template Seeds**: Opal 시드의 컨텍스트 강화
- **Evidence Loop**: Decision 근거 요약 강화
- **Creator Persona**: 개인화 변환 가이드 생성 (Phase 3)

---

## 9) 품질 지표 (효율성 측정)
- **Cluster Coverage**: 패턴 대비 노트북 생성 비율
- **Update Freshness**: 마지막 갱신일 7일 이내 비율
- **Actionability**: Guide에서 실제 적용된 변주 비율
- **Lift Delta**: 노트북 업데이트 이후 성과 개선 폭

---

## 10) 실패 방지 원칙
- NotebookLM 결과는 **직접 노출 금지**
- 항상 **DB 래핑 + 사람이 최종 검토**
- 소스가 오래되면 **즉시 폐기/재생성**

---

## 11) 다음 단계 (Phase 3 준비)
- `creator_style_fingerprint`와 결합한 **개인화 가이드**
- `synapse_rules`와 연결된 **자동 변주 추천**
- 노트북 요약을 **템플릿 시드 기본값**으로 직접 주입
