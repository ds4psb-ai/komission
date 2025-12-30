# Outlier Crawler Integration Design (Komission)

**Date**: 2026-01-07  
**Purpose**: Comprehensive design spec for integrating 3-platform outlier crawlers with Canvas/UI  
**Scope**: Crawlers + Canvas UX + OutlierCard Component + Data Flow

---

## 0) Evidence Sources

| Source | Description |
|--------|-------------|
| [13_PERIODIC_CRAWLING_SPEC.md](docs/13_PERIODIC_CRAWLING_SPEC.md) | Crawler API specs, rate limits, outlier formula |
| [11_VIRLO_BENCHMARK.md](docs/11_VIRLO_BENCHMARK.md) | Virlo IA/feature mapping |
| [08_CANVAS_NODE_CONTRACTS.md](docs/08_CANVAS_NODE_CONTRACTS.md) | Node type definitions |
| [02_EVIDENCE_LOOP_CANVAS.md](docs/02_EVIDENCE_LOOP_CANVAS.md) | VDG sheets + workflow |
| [10_UI_UX_STRATEGY.md](docs/10_UI_UX_STRATEGY.md) | UI principles |
| [15_FINAL_ARCHITECTURE.md](docs/15_FINAL_ARCHITECTURE.md) | Final architecture blueprint |

**Confidence Legend**
- **[OBSERVED]**: Extracted from existing Komission docs
- **[INFERRED]**: Derived from Virlo benchmark
- **[PROPOSED]**: New design decisions

---

## 1) Navigation & IA Structure

### 1.1 Left Rail Groups [PROPOSED]

```
┌──────────────────────┐
│  🔍 Research         │
│    ├─ Outliers       │  ← Crawler output
│    ├─ Genealogy      │  ← Parent-Kids tree
│    └─ Collections    │
├──────────────────────┤
│  🎬 Creator Hub      │
│    ├─ Canvas         │
│    └─ Shoot          │
├──────────────────────┤
│  💼 Business         │
│    ├─ Evidence       │
│    ├─ Decisions      │
│    └─ O2O            │
├──────────────────────┤
│  ⚙️ Account          │
│    ├─ Usage          │
│    └─ Settings       │
└──────────────────────┘
```

### 1.2 Top Bar [OBSERVED + PROPOSED]
- **Role Switch**: Creator / Business toggle (상단 고정)
- **Credit Balance**: 실시간 표시 (unused credits)
- **Simple/Pro Mode**: 기능 복잡도 전환

---

## 2) Outlier Discovery UX

### 2.1 Outlier List View [INFERRED from Virlo]

**필터 구성**
- Platform: `All` / `TikTok` / `YouTube` / `Instagram`
- Freshness: `24h` / `7d` / `30d` / `All`
- Category: Dynamic (beauty, meme, lifestyle...)
- Tier: `S` / `A` / `B` / `C` / `All`

**정렬 옵션**
- Outlier Score (default)
- View Count
- Engagement Rate
- Recency

### 2.2 OutlierCard Component [PROPOSED]

```
┌─────────────────────────────────────────┐
│ ┌───────────────┐  📊 2.5M views        │
│ │               │  🏆 523x outlier (S)  │
│ │  [Thumbnail]  │  ❤️ 12.3% engagement  │
│ │               │                       │
│ └───────────────┘  Creator Avg: 4.8K    │
│                                         │
│ "Hook가 미쳤다..." (title truncated)    │
│                                         │
│ 📍 TikTok · Beauty · 12h ago            │
│                                         │
│ ┌─────────────────┬───────────────────┐ │
│ │  🔗 View        │ ⭐ Promote to Parent│ │
│ └─────────────────┴───────────────────┘ │
└─────────────────────────────────────────┘
```

**Required Fields**
| Field | Source | Description |
|-------|--------|-------------|
| thumbnail_url | Crawler | 썸네일 |
| view_count | Crawler | 조회수 |
| outlier_score | Calculated | 아웃라이어 점수 |
| outlier_tier | Calculated | S/A/B/C 등급 |
| engagement_rate | Calculated | 참여율 |
| creator_avg_views | Calculated | 크리에이터 평균 |
| title | Crawler | 제목 (100자 제한) |
| platform | Crawler | 플랫폼 |
| category | Crawler | 카테고리 |
| crawled_at | Crawler | 수집 시각 |

### 2.3 Tier Badge Styling [PROPOSED]

| Tier | Score | Color | Badge |
|------|-------|-------|-------|
| S | ≥500x | Gold gradient | `🏆 S-Tier` |
| A | ≥200x | Purple | `⭐ A-Tier` |
| B | ≥100x | Blue | `💎 B-Tier` |
| C | ≥50x | Gray | `📈 C-Tier` |

---

## 3) Canvas Integration

### 3.1 Outlier Node [OBSERVED from 08_CANVAS]

**Node Spec**
```json
{
  "type": "outlier",
  "inputs": 0,
  "outputs": 1,
  "data": {
    "outlier_id": "uuid",
    "external_id": "platform_id",
    "video_url": "https://...",
    "platform": "tiktok|youtube|instagram",
    "outlier_score": 523.0,
    "outlier_tier": "S"
  }
}
```

**Canvas Display**
- 컴팩트 카드 형태 (mini OutlierCard)
- 클릭 시 상세 패널 확장
- 드래그하여 Parent Node로 연결

**Implementation (2025-12-25)**
- Component: `CrawlerOutlierNode` in `CustomNodes.tsx`
- Selector: `CrawlerOutlierSelector.tsx` modal with platform/tier filters
- Node Type: `crawlerOutlier` registered in Canvas page

### 3.2 Promotion Flow [INFERRED]

```
Outlier Node ─────────────────▶ Parent Node
     │                              │
     │ "Promote to Parent" CTA      │
     ▼                              ▼
┌─────────────┐              ┌─────────────┐
│ status:     │              │ type:       │
│ "pending"   │  ──────▶     │ "parent"    │
└─────────────┘              └─────────────┘
```

**Promotion Creates:**
1. `remix_nodes` record (type=MASTER)
2. Links `outlier_items.promoted_to_node_id`
3. Updates status: `pending → promoted`

### 3.3 Node Port Logic [PROPOSED]

| Node Type | Inputs | Outputs | Description |
|-----------|--------|---------|-------------|
| Outlier | 0 | 1 | Entry point (raw content) |
| Parent | 1 | N | Master node (connects evidence) |
| Evidence | 1 | 1 | Pattern analysis |
| Decision | N | 1 | Aggregates evidence |
| Capsule | N | 1 | Execution (hidden chain) |

---

## 4) Data Flow Architecture

### 4.1 Crawler → Analysis → Library Flow [OBSERVED]

```
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌────────────────┐
│  Crawlers   │───▶│ outlier_     │───▶│ analysis_schema  │───▶│ notebook_      │
│  (3 platforms)   │ items (DB)   │    │ (code, DB)       │    │ library (DB)   │
└─────────────┘    └──────────────┘    └──────────────────┘    └────────────────┘
       │                  │                    │                      │
       ▼                  ▼                    ▼                      ▼
   API/Apify        Source of Record      Clustering             Insights/Sheet
```

**Key Principle**: DB = Source of Record, Sheets = 공유 버스

### 4.2 API Endpoints [PROPOSED]

```
GET  /api/v1/outliers              # List with filters
GET  /api/v1/outliers/{id}         # Detail view
POST /api/v1/outliers/{id}/promote # Promote to Parent
POST /api/v1/crawlers/run          # Trigger crawl (admin)
GET  /api/v1/crawlers/status       # Crawl status
```

### 4.3 Duplicate Prevention Architecture [IMPLEMENTED 2024-12-30]

중복 크롤링 방지를 위한 이중 방어 체계:

**1차 방어: Application Layer (API 코드)**
```python
# create_item, bulk_import 엔드포인트에서
existing = await db.execute(
    select(OutlierItem).where(OutlierItem.video_url == item.video_url)
)
if existing.scalar_one_or_none():
    return existing_item  # 새로 만들지 않고 기존 것 반환
```

**2차 방어: Database Layer (UNIQUE 제약조건)**
```sql
ALTER TABLE outlier_items ADD CONSTRAINT outlier_items_video_url_key UNIQUE (video_url);
CREATE INDEX ix_outlier_items_video_url ON outlier_items(video_url);
```

**흐름 요약**
| 시나리오 | 1차(App) | 2차(DB) | 결과 |
|---------|----------|---------|------|
| 새 URL 등록 | 통과 ✓ | 통과 ✓ | 정상 저장 |
| 중복 URL 등록 | **차단** ⛔ | 도달 안 함 | 기존 항목 반환 |
| 1차 우회 시도 | 통과 | **차단** ⛔ | DB 에러 (극히 드묾) |

---

## 5) Outlier Score Formula [OBSERVED from 13_PERIODIC_CRAWLING_SPEC]

```
Score = (Views / Baseline) × (1 + (Engagement - BaselineEngagement))
```

**Platform Baselines**
| Platform | Engagement Baseline |
|----------|---------------------|
| YouTube | 5% (0.05) |
| TikTok | 8% (0.08) |
| Instagram | 10% (0.10) |

**Tier Thresholds**
| Tier | Score | Description |
|------|-------|-------------|
| S | ≥500 | Mega-viral |
| A | ≥200 | Strong outlier |
| B | ≥100 | Notable |
| C | ≥50 | Emerging |

---

## 6) Environment Variables [OBSERVED]

```bash
# Required for crawlers
YOUTUBE_API_KEY=xxx           # YouTube Data API v3
APIFY_API_TOKEN=xxx           # TikTok/Instagram via Apify

# Optional (Instagram Graph API)
INSTAGRAM_ACCESS_TOKEN=xxx
IG_BUSINESS_ACCOUNT_ID=xxx
```

---

## 7) Implementation Checklist

### Phase 1: Crawler Integration (✅ Complete)
- [x] YouTube crawler with outlier scoring
- [x] TikTok crawler with Apify
- [x] Instagram crawler with Apify/Graph API
- [x] Factory pattern for crawler selection
- [x] Schema with outlier metrics

### Phase 2: API & DB Integration
- [ ] REST API endpoints for outliers
- [ ] Promotion logic (outlier → parent)
- [ ] Sheet sync script completion

### Phase 3: UI Components (✅ Complete)
- [x] `CrawlerOutlierCard` component → `frontend/src/components/CrawlerOutlierCard.tsx`
- [x] Outlier list view with filters → `/outliers` page
- [x] `CrawlerOutlierNode` for Canvas → `frontend/src/components/canvas/CustomNodes.tsx`
- [x] `CrawlerOutlierSelector` modal → `frontend/src/components/canvas/CrawlerOutlierSelector.tsx`
- [x] Promotion flow UX (placeholder, pending backend API)

### Phase 4: Automation
- [ ] Scheduled crawler runs (cron/n8n)
- [ ] Real-time Sheet sync
- [ ] Notification on new S-tier outliers

---

## 8) Canvas Controls (Reference)

| Control | Behavior |
|---------|----------|
| Minimap | Bottom-right floating |
| Zoom | 10% ~ 200% |
| Select | Shift + Drag (lasso) |
| Delete | Backspace |
| Connect | Drag from output port |

---

## 9) Validation Checklist

Before execution:
- [x] Outlier API response schema confirmed
- [x] OutlierCard props finalized (`CrawlerOutlierItem` interface)
- [x] Canvas node integration tested (build passed)
- [ ] Sheet column contract verified
- [ ] Crawler quota management confirmed
