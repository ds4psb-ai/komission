# VDG System: Viral Depth Genealogy 데이터 모델 (최신)

**작성**: 2026-01-06
**목표**: Parent → Depth1/Depth2 → Evidence 계산을 표준화

---

## 1) 핵심 개념
VDG는 **Parent(원본) → Depth1(1차 변주) → Depth2(최적화 변주)**의 구조를 기록합니다.
이 계보를 통해 **성공 구조를 데이터로 증명**하고 다음 실험을 자동 제안합니다.

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

---

## 3) Evidence Score 계산 (기본형)
```
Score = (Views_norm * 0.5) + (Engagement_norm * 0.3) + (Tracking_norm * 0.2)

Views_norm = min(views / parent_views * 1.5, 1.0)
Engagement_norm = min(engagement_rate / 0.10, 1.0)
Tracking_norm = min(tracking_days / 14, 1.0)
```

> 이 계산은 **MVP 기준 기본값**입니다. 성과가 쌓이면 가중치 재조정.

---

## 4) 플랫폼 우선순위
- **1순위**: TikTok / Instagram (가장 쉬운 수집 경로)
- **3순위**: YouTube Shorts (보조)

---

## 5) Evidence 생성 주기
- 매일: Metric Daily 갱신
- 주 1회: Evidence Snapshot 생성
- Depth 종료(14일) 시: Winner 확정

