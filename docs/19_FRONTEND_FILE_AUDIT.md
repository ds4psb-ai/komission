# Frontend File Audit (Current)

**Updated**: 2026-01-03
**Scope**: 실제 라우트/컴포넌트 기준으로 정리 상태만 기록

---

## 1) Redirect stubs (legacy routes)

| Route | File | Target | Status |
|------|------|--------|--------|
| `/discover` | `app/(app)/discover/page.tsx` | `/` | redirect 유지 |
| `/outliers` | `app/outliers/page.tsx` | `/ops/outliers` | redirect 유지 |
| `/canvas` | `app/canvas/page.tsx` | `/ops/canvas` | redirect 유지 |
| `/pipelines` | `app/pipelines/page.tsx` | `/ops/pipelines` | redirect 유지 |

---

## 2) Ops-only pages (active)
- `/ops` (console)
- `/ops/outliers` (+ `/ops/outliers/manual`)
- `/ops/canvas`
- `/ops/pipelines`
- `/ops/crawlers`

---

## 3) Creator-facing flows (active)
- `/` (Unified Outlier Discovery)
- `/(app)/for-you` (Answer-First 추천)
- `/session/input`, `/session/result`, `/session/shoot`
- `/remix/[nodeId]` (레거시 플로우 유지)
- `/guide/[patternId]` (간단 가이드)
- `/wizard`, `/my`, `/boards`, `/knowledge/*`

---

## 4) Component status

| Component | Status | Notes |
|-----------|--------|------|
| `UnifiedOutlierCard` | in use | 홈 피드 카드 |
| `CrawlerOutlierCard` | in use | Canvas outlier selector |
| `PatternAnswerCard` | in use | `/for-you` |
| `EvidenceBar` | in use | `/for-you` |
| `FeedbackWidget` | in use | `/for-you` (UI only) |
| `OutlierAnalysisCard` | unused | cleanup 후보 |

---

## 5) Outlier 공용 컴포넌트 디렉토리

> `/components/outlier/` 디렉토리에 통합된 아웃라이어 관련 공용 컴포넌트

### 구조
```
frontend/src/components/outlier/
├── index.ts                  # 통합 export
├── TikTokPlayer.tsx          # TikTok 임베드 재생 (postMessage unmute)
├── TierBadge.tsx             # S/A/B/C 티어 뱃지
├── OutlierMetrics.tsx        # 조회수/좋아요/공유 메트릭
├── PipelineStatus.tsx        # 파이프라인 단계 뱃지
├── FilmingGuide.tsx          # VDG 기반 촬영 가이드
└── OutlierDetailModal.tsx    # 통합 상세 모달
```

### 특징
- **중복 제거**: 여러 페이지에 흩어진 Outlier 관련 UI 통합
- **일관성**: Tier, Platform 스타일 일치
- **재사용**: `/ops/outliers`, `/ops/canvas`, `/` 등에서 공용 사용

### Import 예시
```typescript
import {
    TikTokPlayer,
    TierBadge,
    OutlierMetrics,
    FilmingGuide,
    OutlierDetailModal,
} from '@/components/outlier';
```
