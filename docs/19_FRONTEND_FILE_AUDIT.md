# Frontend File Removal/Demotion List

**기준**: `18_PAGE_IA_REDESIGN.md` 기반, L1/L2 자동화 + Session 중심 전환에 맞춘 파일 정리

---

## 1) 제거 대상 (Delete)

> L1/L2 자동화로 불필요해지거나, 새 구조로 완전히 대체되는 파일

| 파일 경로 | 제거 사유 |
|-----------|----------|
| `app/(app)/discover/page.tsx` | `/trending`으로 완전 대체 |
| `components/CrawlerOutlierCard.tsx` | `UnifiedOutlierCard`로 통합 |
| `components/OutlierCard.tsx` | `PatternAnswerCard`와 `UnifiedOutlierCard`로 분리 대체 |
| `components/OutlierAnalysisCard.tsx` | Ops 전용으로 이동 또는 제거 |

---

## 2) Ops 전용으로 격하 (Demote to /ops)

> 일반 사용자에게 불필요, 운영자만 접근

| 파일 경로 | 새 위치 | 비고 |
|-----------|---------|------|
| `app/outliers/page.tsx` | `app/ops/outliers/page.tsx` | Outlier 수집/관리 |
| `app/canvas/page.tsx` | `app/ops/canvas/page.tsx` | Canvas Pro |
| `app/pipelines/page.tsx` | `app/ops/pipelines/page.tsx` | 파이프라인 관리 |
| `components/GenealogyWidget.tsx` | Ops 전용 | Cluster/Lineage 그래프 |
| `components/PatternConfidenceChart.tsx` | Ops 전용 | 내부 분석 차트 |
| `components/PipelineProgress.tsx` | Ops 전용 | 파이프라인 상태 |
| `components/SessionHUD.tsx` | Ops 전용 유지 | 운영자 HUD |
| `components/MutationStrategyCard.tsx` | Ops 전용 | 변주 전략 상세 |

---

## 3) 리팩토링 대상 (Refactor/Rename)

> 기존 기능 유지하되 새 IA에 맞게 수정

| 파일 경로 | 액션 | 비고 |
|-----------|------|------|
| `components/BottomNav.tsx` | **수정** | Role 기반 탭 분기 추가 |
| `components/AppHeader.tsx` | **수정** | Role Switch 토글 추가 |
| `app/remix/[nodeId]/page.tsx` | **이동** | `/session/result/[id]`로 통합 |
| `app/guide/[patternId]/page.tsx` | **이동** | `/session/shoot/[id]`로 통합 |
| `components/FilmingGuide.tsx` | **유지** | Session Shoot에서 재사용 |
| `components/ViralGuideCard.tsx` | **유지** | Session Result에서 재사용 |
| `components/UnifiedOutlierCard.tsx` | **유지** | Trending 피드에서 사용 |

---

## 4) 신규 생성 필요 (New Files)

| 파일 경로 | 용도 |
|-----------|------|
| `app/for-you/page.tsx` | 과제 모드 메인 (L1/L2 추천) |
| `app/trending/page.tsx` | 뉴스 모드 메인 (아웃라이어 피드) |
| `app/session/input/page.tsx` | 상황 입력 |
| `app/session/result/page.tsx` | 추천 결과 + EvidenceBar |
| `app/session/shoot/page.tsx` | 촬영 가이드 |
| `contexts/SessionContext.tsx` | 세션 상태 관리 |
| `components/PatternAnswerCard.tsx` | Answer-First (For You) 카드 |
| `components/EvidenceBar.tsx` | 댓글 5개 + 재등장 근거 |
| `components/FeedbackWidget.tsx` | 👍👎 피드백 수집 |

---

## 5) 유지 (Keep As-Is)

> 새 IA에서도 그대로 사용

| 파일 경로 | 비고 |
|-----------|------|
| `app/my/page.tsx` | 마이페이지 |
| `app/my/royalty/page.tsx` | 로열티 |
| `app/o2o/page.tsx` | O2O 메인 |
| `app/o2o/campaigns/create/page.tsx` | 캠페인 생성 |
| `app/calibration/page.tsx` | Taste Calibration |
| `app/login/page.tsx` | 로그인 |
| `app/(app)/boards/*` | Evidence Boards |
| `app/(app)/knowledge/*` | 지식 라이브러리 |
| `components/RoyaltyBadge.tsx` | 로열티 뱃지 |
| `components/CelebrationModal.tsx` | 축하 모달 |
| `components/Toast.tsx` | 알림 |
| `components/LoadingSpinner.tsx` | 로딩 |
| `components/EmptyState.tsx` | 빈 상태 |
| `components/ErrorBoundary.tsx` | 에러 핸들링 |
| `components/GoogleLoginButton.tsx` | 구글 로그인 |

---

## 6) 컴포넌트 통합 맵

```
┌─────────────────────────────────────────────────────────┐
│ AS-IS                      │ TO-BE                      │
├────────────────────────────┼────────────────────────────┤
│ OutlierCard.tsx            │ ┌→ PatternAnswerCard.tsx  │
│ CrawlerOutlierCard.tsx     │ │  (과제 모드)             │
│                            │ └→ UnifiedOutlierCard.tsx │
│                            │    (뉴스 모드, 유지)       │
├────────────────────────────┼────────────────────────────┤
│ (없음)                     │ EvidenceBar.tsx           │
│                            │ FeedbackWidget.tsx        │
├────────────────────────────┼────────────────────────────┤
│ GenealogyWidget.tsx        │ Ops 전용 격하             │
│ PatternConfidenceChart.tsx │ Ops 전용 격하             │
│ PipelineProgress.tsx       │ Ops 전용 격하             │
└────────────────────────────┴────────────────────────────┘
```

---

## 7) 마이그레이션 순서 (권장)

1. **신규 파일 생성**: `PatternAnswerCard`, `EvidenceBar`, `FeedbackWidget`
2. **세션 라우트 생성**: `/for-you`, `/trending`, `/session/*`
3. **BottomNav/AppHeader 수정**: Role Switch 추가
4. **기존 라우트 리다이렉트**: `/discover` → `/trending`
5. **Ops 전용 이동**: `/outliers` → `/ops/outliers`
6. **제거**: 중복 컴포넌트 삭제

---

## 8) Outlier 공용 컴포넌트 디렉토리 [NEW 2024-12-30]

> `/components/outlier/` 디렉토리로 통합된 아웃라이어 관련 컴포넌트

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
- **재사용**: `/ops/outliers`, `/canvas`, `/` (메인 페이지) 등에서 공용 사용
- **코드 감소**: `ops/outliers/page.tsx` 559줄 → 270줄 (52% 감소)

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
