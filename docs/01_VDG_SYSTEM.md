# VDG System: Viral Depth Genealogy 데이터 모델 (최신)

**작성**: 2026-01-07
**목표**: Parent → Depth1/Depth2 → Evidence 계산을 표준화

---

## 1) 핵심 개념
VDG는 **Parent(원본) → Depth1(1차 변주) → Depth2(최적화 변주)**의 구조를 기록합니다.
이 계보를 통해 **성공 구조를 데이터로 증명**하고 다음 실험을 자동 제안합니다.

**핵심 통찰**
- 바이럴은 “모자이크 패턴(훅/씬/자막/오디오 반복)”이 계보에서 재등장합니다.
- 따라서 **Pattern Library/Trace**를 기록해야 진짜 공식이 증명됩니다.


**시간축 기반 변주 원리** → [17_TEMPORAL_VARIATION_THEORY.md](17_TEMPORAL_VARIATION_THEORY.md)
- 시간 경과에 따라 오마쥬 비율 감소 (100% → 95% → 90%...)
- **불변**: 핵심 바이럴 로직(Hook, Pacing, Payoff) 100% 유지
- **가변**: 소재, 인물, 반전, 중간 킥 등 창의성 추가

**입력 흐름(전제)**
- 관리자 수동/크롤링 아웃라이어 → 영상 해석(코드) → 유사도 클러스터링 → **NotebookLM(Pattern Engine)** → Parent 후보 → Depth 실험
- NotebookLM은 **Pattern Engine**으로 적극 활용한다.
  - Source Pack을 받아 **불변 규칙 + 변주 포인트**를 합성한다.
- **패턴 경계 원칙 (중요)**:
  - 패턴 경계(cluster_id)는 **VDG/DB 기준선**으로 고정한다.
  - NotebookLM이 패턴을 "결정/정의"하지 않는다.
  - 패턴 경계/정합성/재현성은 코드/DB가 담당한다.
- 결과는 반드시 **DB에 구조화 저장**하며 SoR은 DB이다.

---

## 2) 정규 스키마 (SoR = DB)

### 2.1 Parents
```sql
CREATE TABLE vdg_parents (
  id UUID PRIMARY KEY,
  title VARCHAR(255),
  platform VARCHAR(50), -- tiktok, instagram, youtube
  category VARCHAR(50),
  source_url TEXT,
  baseline_views INT,
  baseline_engagement FLOAT,
  baseline_retention FLOAT,
  status VARCHAR(50), -- planning, depth1, depth2, complete
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### 2.2 Variants
```sql
CREATE TABLE vdg_variants (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES vdg_parents(id),
  depth INT, -- 1 or 2
  variant_name VARCHAR(255),
  structure_elements JSONB,
  created_by VARCHAR(255),
  status VARCHAR(50), -- tracking, complete
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### 2.3 Metrics (일별)
```sql
CREATE TABLE vdg_metric_daily (
  id UUID PRIMARY KEY,
  variant_id UUID REFERENCES vdg_variants(id),
  date DATE,
  views INT,
  likes INT,
  comments INT,
  retention FLOAT,
  engagement_rate FLOAT
);
```

### 2.4 Evidence Snapshot
```sql
CREATE TABLE vdg_evidence (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES vdg_parents(id),
  generated_at TIMESTAMP,
  confidence_level FLOAT,
  winner_variant_id UUID,
  evidence_json JSONB
);
```

### 2.5 Pattern Library (재사용 단위)
```sql
CREATE TABLE vdg_patterns (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  pattern_type VARCHAR(50), -- hook, scene, subtitle, audio, pacing
  description TEXT,
  created_at TIMESTAMP
);
```

### 2.6 Pattern Trace (변주별 적용 기록)
```sql
CREATE TABLE vdg_pattern_trace (
  id UUID PRIMARY KEY,
  variant_id UUID REFERENCES vdg_variants(id),
  pattern_id UUID REFERENCES vdg_patterns(id),
  weight FLOAT, -- 0~1 적용 강도
  evidence_note TEXT,
  created_at TIMESTAMP
);
```

### 2.7 Pattern Lift (증명/누적)
```sql
CREATE TABLE vdg_pattern_lift (
  id UUID PRIMARY KEY,
  pattern_id UUID REFERENCES vdg_patterns(id),
  parent_id UUID REFERENCES vdg_parents(id),
  depth INT,
  lift_score FLOAT,
  sample_size INT,
  updated_at TIMESTAMP
);
```

### 2.8 현재 코드베이스 매핑 (실제 구현)
`vdg_*`는 개념 스키마이며, 현재 구현은 아래 매핑을 사용합니다.

| 개념 | 실제 테이블/필드 |
| --- | --- |
| vdg_parents | `remix_nodes` (layer=MASTER, permission=READ_ONLY) |
| vdg_variants | `remix_nodes` (layer=FORK/FORK_OF_FORK, parent_node_id 연결) |
| vdg_metric_daily | `metric_daily` |
| vdg_evidence | `evidence_snapshots` (JSON 요약) |
| vdg_patterns / trace / lift | **Phase 2 이후 테이블 도입 예정** |

> 즉시 운영은 `remix_nodes` + `metric_daily` + `evidence_snapshots`로 충분하며,
> 패턴 테이블은 Evidence가 쌓일 때 추가합니다.

---

## 3) Evidence Score + Pattern Lift 계산
### 3.1 Evidence Score (기본형)
```
Score = (Views_norm * 0.5) + (Engagement_norm * 0.3) + (Tracking_norm * 0.2)

Views_norm = min(views / parent_views * 1.5, 1.0)
Engagement_norm = min(engagement_rate / 0.10, 1.0)
Tracking_norm = min(tracking_days / 14, 1.0)
```

> 이 계산은 **MVP 기준 기본값**입니다. 성과가 쌓이면 가중치 재조정.

### 3.2 Pattern Lift (기본형)
```
Lift = (Variant_metric - Parent_metric) / Parent_metric
Lift_score = avg(Lift_views, Lift_engagement, Lift_retention)
```

> Pattern Lift는 Pattern Trace와 Evidence 결과를 결합해 “공식”으로 승격합니다.

---

## 4) Pattern 유형 ↔ Mutation Profile 매핑
MVP 기준으로 mutation_profile의 타입을 Pattern 유형으로 매핑합니다.

| mutation_profile | pattern_type |
| --- | --- |
| audio | audio |
| visual | scene |
| hook | hook |
| setting | pacing |

> 이후 Pattern Library가 확장되면 세부 타입을 분리합니다.

---

## 5) Sequence Similarity (Microbeat 기반)
VDG v3.2의 `microbeats`/`sentiment_arc` 필드를 활용해 **구간 순서 유사도**를 계산합니다.

**목적**
- “같은 재료지만 순서가 다른 영상”을 잘못 묶는 오류 방지
- Depth 변주가 **시간 구조를 보존했는지** 판단

**권장 방식 (clustering.py 구현 기준)**
- **Microbeat Sequence**: edit distance → **30%**
- **Hook 유형/길이**: attention technique + duration 비교 → **25%**
- **시각 패턴**: 첫 3개 샷 visual pattern 매칭 → **20%**
- **오디오 패턴**: trending 여부 + pattern 매칭 → **15%**
- **타이밍 프로필**: 총 길이 차이 비교 → **10%**

**저장 필드 (권장)**
- `vdg_variants.structure_elements.microbeat_sequence`
- `vdg_pattern_trace.weight` (sequence 반영)
- `vdg_pattern_lift`는 sequence 유사도 기반으로 보정

---

## 5.1) VDG v3.3 스키마 확장 (2025-01)

**업데이트 목표**: 이전 Gemini 2.5 Pro 수준의 상세 분석을 Gemini 3.0 Pro에서 활용

### 5.1.1 새로운 필드 (v3.3)

| 필드 | 타입 | 용도 |
| --- | --- | --- |
| `focus_windows[]` | FocusWindow[] | RL 보상 신호용 구간별 분석 |
| `cross_scene_analysis` | CrossSceneAnalysis | 씬 간 패턴/일관성 분석 |
| `asr_transcript` | ASRTranscript | 음성 인식 원본 + 영어 번역 |
| `ocr_text[]` | OCRItem[] | 화면 내 텍스트 + 타임스탬프 |
| `upload_date` | string | OutlierItem 실제 업로드 날짜 |

### 5.1.2 Focus Window (RL 보상 신호)
```json
{
  "window_id": "W00",
  "t_window": [0, 3.5],
  "hotspot": {
    "reasons": ["hook", "cv_change"],
    "scores": {"hook": 0.9, "interest": 0.8, "boundary": 0.6}
  },
  "mise_en_scene": {
    "composition": {"grid": "center", "subject_size": "CU"},
    "lighting": {"type": "soft_light"},
    "lens": {"fov_class": "medium", "dof": "shallow"}
  },
  "entities": [
    {"label": "main_character", "traits": {"pose": "sitting", "emotion": "neutral"}}
  ],
  "tags": {"narrative_roles": ["SETUP"], "cinematic": ["STATIC_SHOT"]}
}
```

### 5.1.3 Cross-Scene Analysis (패턴 합성)
```json
{
  "global_summary": "A complete narrative arc from setup to punchline in one take.",
  "consistent_elements": [
    {"aspect": "composition", "evidence": "Center framing maintained throughout"}
  ],
  "evolving_elements": [
    {"dimension": "emotion_arc", "description": "Neutral → Tense → Comedic relief", "pattern": "escalating"}
  ],
  "director_intent": [
    {"technique": "slow_long_take", "intended_effect": "comedic_timing", "rationale": "..."}
  ],
  "entity_state_changes": [
    {"entity_id": "Customer", "initial_state": "Polite", "final_state": "Assertive", "triggering_event": "Owner's insult"}
  ]
}
```

### 5.1.4 메타데이터 통합 (OutlierItem → VDG)
VDG 저장 시 OutlierItem의 **실제 메트릭**을 병합:
```python
vdg_data["metrics"] = {
    "view_count": item.view_count,
    "like_count": item.like_count,
    "outlier_tier": item.outlier_tier,
    "outlier_score": item.outlier_score,
    "creator_avg_views": item.creator_avg_views,
}
```

### 5.1.5 댓글 증거 통합 (OutlierItem → VDG)
- `OutlierItem.best_comments`를 `vdg_data["audience_reaction"]["best_comments"]`에 병합
- `metrics.comment_count`는 **실제 댓글 수**(플랫폼 메타데이터) 기준을 유지  
  - 샘플 수는 `best_comments` 길이로 표현
- 댓글이 없거나 차단되면 `best_comments=[]`로 두고 VDG 분석은 진행

### 5.1.6 코드 위치
- 스키마: `backend/app/schemas/vdg.py`
- 프롬프트: `backend/app/services/gemini_pipeline.py` (VDG_PROMPT)
- 메타데이터 병합: `backend/app/routers/outliers.py` (_run_vdg_analysis_with_comments)

---

## 6) 플랫폼 우선순위
- **1순위**: TikTok / Instagram (가장 쉬운 수집 경로)
- **3순위**: YouTube Shorts (보조)

---

## 7) Evidence 생성 주기
- 매일: Metric Daily 갱신
- 주 1회: Evidence Snapshot 생성
- Depth 종료(14일) 시: Winner 확정
