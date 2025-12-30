# NotebookLM Library Strategy (최신)

**작성**: 2026-01-07  
**목표**: NotebookLM의 각 노트북/클러스터를 **최대 가치 창출**에 맞게 설계/운영

---

## 1) 역할 정의 (Positioning)
- NotebookLM은 **Pattern Engine**으로 적극 활용한다.
  - Source Pack을 받아 **불변 규칙 + 변주 포인트**를 합성
- **SoR는 DB**이며, NotebookLM 결과는 **DB로 래핑** 후 사용
- 목적은 “정답 생성”이 아니라 **패턴 합성 + 실행 가이드 보강**
- **패턴 경계 원칙 (중요)**:
  - 패턴 경계(cluster_id)는 **VDG/DB 기준선**으로 고정
  - NotebookLM이 패턴을 "결정/정의"하지 않는다.
  - 이 경계가 없으면 시간이 지나면서 패턴 일관성이 무너진다.

---

## 2) 2025 최신 업데이트 반영 (핵심 기능)
**공식 업데이트 기준(2025-12)**: Deep Research, 새로운 소스 타입, Studio 다중 출력, Video Overviews, Public Notebooks, **Ultra 600 Sources**

### 2.1 Ultra 플랜 (600 Sources)
- **노트북당 최대 600개 소스** 지원
- **전략**: Mega-Pack 모드로 다중 클러스터를 단일 노트북에 통합
- **스크립트**: `build_notebook_source_pack.py --mega-pack --cluster-ids "c1,c2,c3"`

### 2.2 Deep Research
- 외부 소스를 자동 탐색/리포트 생성
- **원칙**: 클러스터 핵심은 내부 소스, **Deep Research는 보강용**
- **가드레일**: 허용 도메인 목록 기반(브랜드/플랫폼 공식 문서만)

### 2.3 소스 타입 확장
- **Google Sheets / Drive URL / 이미지 / .docx** 지원
- **전략**: DB에서 `Notebook Source Pack`을 만들고 Sheets/Docx로 자동 출력

### 2.4 Studio 다중 출력
- 노트북당 **여러 Output 생성 가능**
- **용도 분리**: Creator용(브리프), Business용(근거/리스크), Ops용(체크리스트)
- **스크립트**: `--output-targets "creator,business,ops"`

### 2.5 Data Tables → Sheets Export
- NotebookLM이 생성한 구조화 테이블을 **Google Sheets로 Export**
- **파이프라인**: Data Tables → Sheets → PostgreSQL (PatternSynthesis)
- **용도**: NotebookLM 산출물의 DB-wrapped 자동화

### 2.6 Video/Audio Overviews
- 구조/프로세스 설명에 강함 (절차/단계/사례 요약)
- **용도**: 내부 교육/온보딩/캠페인 브리핑용

### 2.7 Public Notebooks
- 링크 공유 가능 (읽기 전용 상호작용)
- **원칙**: 기본은 비공개, **공개는 마케팅/홍보 목적에만 제한**

### 2.8 Enterprise API
- 노트북 생성/조회/공유/정리 자동화 가능
- **용도**: 라이프사이클 자동화 (create → sync → archive)
- **상세**: [18_NOTEBOOKLM_ENTERPRISE_INTEGRATION.md](18_NOTEBOOKLM_ENTERPRISE_INTEGRATION.md)

---

## 3) 라이브러리 구조 (Notebook Topology)
### 3.1 기본 단위 = cluster_id + temporal_phase
- **1 노트북 = cluster_id + temporal_phase** (예: `hook-2s-textpunch_T1`)
- 같은 cluster라도 T0(초기)와 T3(늦은 시점)의 변주 비율이 다름
- 시간축 분리로 패턴 규칙이 명확해지고 품질이 올라감 
- 클러스터는 **Parent‑Kids(Depth1/Depth2)** 변주를 포괄

### 3.2 분할 규칙
- **표준 모드**: 소스 50개 한도, **temporal_phase 분할**
- **Ultra Mega-Pack 모드**: 최대 600개 소스, 다중 클러스터 통합 가능
- 기준: **temporal_phase(T0~T4)** 우선, 필요시 **하위 변주 타입(훅/오디오)**
  - 예: `hook-2s-textpunch_T0`, `hook-2s-textpunch_T1`
- **Mega-Pack 명령어**: `--mega-pack --cluster-ids "c1,c2,c3" --limit 600`

### 3.3 네이밍 규칙
```
NL_{platform}_{category}_{cluster_id}_{temporal_phase}_v{n}
예) NL_tiktok_beauty_hook-2s-textpunch_T1_v2
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

### 5.2 Comment Evidence Standard (Pack)
댓글은 **바이럴 DNA 증거**로 취급한다.  
NotebookLM이 패턴을 합성할 때 댓글 근거를 반드시 사용할 수 있도록 **정제 규칙을 고정**한다.

**comment_samples.md 구성 규칙**
- 상위 댓글 10~30개만 포함
- 언어 우선: `ko > en > others`
- 중복/노이즈 제거 (이모지/짧은 감탄사/의미 없는 반복)

**권장 포맷**
```
[likes] [lang] [tag] comment text
```
- tag 예시: `hook`, `payoff`, `product_curiosity`, `confusion`, `controversy`
- 댓글이 없으면 `NO_COMMENTS_AVAILABLE` 한 줄을 추가하여 환각 방지

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

## 8) Pattern Retrieval Standard (L1 Hybrid → L2 Reranker)
NotebookLM 출력은 **DB 래핑 이후** 검색/추천 단계에서 사용한다.  
패턴 경계는 **cluster_id 기준선**을 유지하며, 검색 단계는 경계를 절대 변경하지 않는다.

### 8.1 입력 쿼리 구조 (권장)
```json
{
  "platform": "tiktok|shorts|reels",
  "category": "beauty|food|tech|fashion|etc",
  "creator_persona": "string",
  "product_constraints": ["string"],
  "intent": "string",
  "temporal_phase": "T0|T1|T2|T3|T4"
}
```

### 8.2 L0 사전 필터 (Guardrails)
- `platform`, `category`, `temporal_phase` 우선 필터
- `Update Freshness` 7일 초과 시 기본 제외(필요 시 예외 허용)
- `failure_modes`가 명시적 제약과 충돌하면 제외

### 8.3 L1 하이브리드 검색 (Recall 우선)
- **키워드(BM25)**: `pattern_definition`, `signature`, `adaptation_rules`, `product_slot`
- **벡터**: `summary + signature + adaptation_rules` 임베딩
- **후보 풀**: 50~100개

### 8.4 L2 리랭커 (Precision 우선)
필수 피처:
1. **fit_score**: persona/category/product_slot 일치
2. **evidence_strength**: source_count + variant_lift
3. **quality_score**: VDG 품질/완결성
4. **recency_score**: 최근성
5. **risk_penalty**: failure_modes 충돌

선택 피처:
- **graph_score**: 패턴↔변주↔성과 관계 그래프 신호
- **creator_history**: 과거 성공 패턴 재현성

**Temporal Recurrence 피처** (confirmed 재등장 시에만 반영):
- **recurrence_score**: 과거 패턴과의 유사도 (0.88 이상 confirmed만)
- **historical_lift**: 과거 패턴의 성과 지표 (avg_delta, success_rate)
- **reaction_delta**: 과거 대비 댓글 반응 변화

### 8.5 Comment Signature 산출 (Recurrence 전용)
댓글 5개에서 태그 분포를 추출하여 재등장 여부를 판별한다.

**태그 집합 (고정)**
- `hook`, `payoff`, `product_curiosity`, `confusion`, `controversy`

**벡터 예시**
```
hook=0.4, payoff=0.2, product=0.2, confusion=0.1, controversy=0.1
```

**comment_signature_sim**: 두 벡터의 cosine similarity (0~1)
- 영상 구조가 유사해도 댓글 반응이 다르면 다른 패턴
- 댓글 태그가 과거 패턴과 유사하면 진짜 재등장 확정

### 8.6 자동 임계값 보정 로직
고정 임계값은 데이터가 쌓이면 깨지므로 주기적으로 재설정한다.

**보정 방법**
- `within 분포`: 같은 클러스터 내부 유사도
- `cross 분포`: 다른 클러스터 간 유사도
- **임계값 후보**:
  - `t1 = P99(cross)` (오탐 억제 기준)
  - `t2 = P50(within)` (재현율 기준)
- **최종 임계값**: `max(t1, t2)`

**보정 주기**
- 신규 데이터 300개 이상 또는 주 1회
- 급격한 요동 방지를 위해 EMA로 스무딩

### 8.7 출력 규칙
- Top‑K(기본 3~5)만 노출
- 각 결과에 **근거(citations)**와 **변주 슬롯**을 함께 표시
- `query_id`, `ranked_ids`, `feature_snapshot`을 로그로 저장
- **confirmed 재등장**: "과거 성공 패턴과 동일 구조" 근거 표시

---

## 9) 활용 지점 (최대 가치)
- **Capsule Guide**: “실행 가능한 브리프” 강화
- **Template Seeds**: Opal 시드의 컨텍스트 강화
- **Evidence Loop**: Decision 근거 요약 강화
- **Creator Persona**: 개인화 변환 가이드 생성 (Phase 3)

---

## 10) 패턴 합성 프롬프트 프로토콜 (2025-12 확정)

### 10.1 Prompt A: Invariant Extraction (불변 규칙 추출)

```
Source Pack의 Parent vs Kids를 비교하여 다음을 JSON 형식으로 추출해주세요:

1) invariant_rules: 모든 성공 변주에서 공통으로 유지된 규칙
2) must_keep: 반드시 유지해야 할 Hook/Pacing/Payoff 요소
3) citations: 근거가 되는 소스 참조

출력 형식:
{
  "invariant_rules": ["rule1", "rule2"],
  "must_keep": {
    "hook": "...",
    "pacing": "...",
    "payoff": "..."
  },
  "citations": ["source1", "source2"]
}
```

### 10.2 Prompt B: Mutation Strategy (변주 전략)

```
성공/실패 변주를 비교하여 다음을 JSON 형식으로 분석해주세요:

1) success_variables: 성공에 기여한 변수들
2) failure_variables: 실패를 유발한 변수들
3) next_depth_recommendations: 다음 Depth 변주 추천 3개

출력 형식:
{
  "success_variables": ["var1", "var2"],
  "failure_variables": ["var1", "var2"],
  "next_depth_recommendations": [
    {"mutation": "...", "expected_lift": "..."},
    ...
  ],
  "citations": ["source1", "source2"]
}
```

### 10.3 Prompt C: Failure Modes (실패 패턴)

```
실패 사례만 분석하여 다음을 JSON 형식으로 정리해주세요:

1) common_failure_patterns: 공통 실패 패턴
2) do_not_list: 절대 하지 말아야 할 요소

출력 형식:
{
  "common_failure_patterns": ["pattern1", "pattern2"],
  "do_not_list": ["item1", "item2"],
  "citations": ["source1", "source2"]
}
```

> **참고**: NotebookLM은 인라인 citation을 제공하므로 근거가 자동 연결됩니다.

---

## 11) Source Pack 분할 프로토콜 (대규모 운영)

### 11.1 분할 기준 (3단계)

| 단계 | 조건 | 분할 방식 |
| --- | --- | --- |
| **1차** | 기본 | `cluster_id + temporal_phase` |
| **2차** | 소스 50개 초과 | 변주 타입(hook/audio) 분리 |
| **3차** | 시간창 확장 | 월 단위 추가 분할 |

### 11.2 Pack 구성 (권장)

| 파일 | 내용 |
| --- | --- |
| `cluster_summary.docx` | 패턴 정의, 핵심 시그니처 3개, temporal_phase 명시 |
| `variants_table.xlsx` | Depth1/2 성공/실패 사례, 메트릭(view/like/share/comment + outlier_score) |
| `evidence_digest.docx` | Evidence Snapshot 요약, Failure modes |
| `comment_samples.md` | 상위 댓글 10~30개 (반응/오해/리스크) |

### 11.3 대규모 운영 원칙

- **DB에 원본 보관** + Pack은 "요약 스냅샷"만
- **노트북 간 접근 불가**이므로 Pack 자체가 완결 구조
- **Temporal Phase 분리**: T0/T1은 높은 오마주, T3/T4는 변주 비율 증가

---

## 12) 품질 지표 (효율성 측정)
- **Cluster Coverage**: 패턴 대비 노트북 생성 비율
- **Update Freshness**: 마지막 갱신일 7일 이내 비율
- **Actionability**: Guide에서 실제 적용된 변주 비율
- **Lift Delta**: 노트북 업데이트 이후 성과 개선 폭

---

## 13) 실패 방지 원칙
- NotebookLM 결과는 **직접 노출 금지**
- 항상 **DB 래핑 + 사람이 최종 검토**
- 소스가 오래되면 **즉시 폐기/재생성**

---

## 14) 다음 단계 (Phase 3 준비)
- `creator_style_fingerprint`와 결합한 **개인화 가이드**
- `synapse_rules`와 연결된 **자동 변주 추천**
- 노트북 요약을 **템플릿 시드 기본값**으로 직접 주입
