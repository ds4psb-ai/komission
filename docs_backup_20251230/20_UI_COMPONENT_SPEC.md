# UI Component Spec: PatternAnswerCard / EvidenceBar / Feedback

**목표**: L1/L2 Pattern Retrieval + Temporal Recurrence 출력을 사용자에게 전달하는 핵심 UI 컴포넌트 정의

---

## 1) PatternAnswerCard

> **역할**: "이 패턴이 너에게 맞다"는 Answer-First (For You) 핵심 카드

### 1.1 Data Binding (API → Component)
```typescript
interface PatternAnswerCardProps {
  // Pattern Library 출력
  pattern_id: string;
  cluster_id: string;
  pattern_summary: string;         // 한 줄 정의
  signature: {
    hook: string;
    timing: string;
    audio: string;
  };
  
  // L2 Reranker 출력
  fit_score: number;               // 0~1
  evidence_strength: number;       // source_count + variant_lift
  
  // Recurrence (있으면 표시)
  recurrence?: {
    status: 'confirmed' | 'candidate';
    ancestor_cluster_id: string;
    recurrence_score: number;
    origin_year?: number;
  };
  
  // CTA
  onShoot: () => void;
  onViewEvidence: () => void;
}
```

### 1.2 Visual Structure
```
┌─────────────────────────────────────┐
│ [Platform Badge]  [Tier Badge: S/A] │
├─────────────────────────────────────┤
│ ◉ Pattern Summary (1줄)             │
│                                     │
│ Hook: "2초 텍스트 펀치"              │
│ Audio: "K-POP 트렌딩"               │
│ Timing: "5 cuts/10sec"             │
├─────────────────────────────────────┤
│ ○ Fit Score: 87%   ○ Evidence: 12  │
│ 🔁 "2023 성공 패턴과 동일 구조"      │  ← Recurrence Badge (confirmed만)
├─────────────────────────────────────┤
│ [👁️ Evidence]  [🎬 Shoot Guide]    │  ← CTA 버튼
└─────────────────────────────────────┘
```

### 1.3 Design Rules
- **크기**: 카드 최대 너비 360px (모바일 풀, 데스크톱 그리드)
- **그림자**: `shadow-sm` (얕은 레벨)
- **색상**: fit_score ≥ 0.8 → 포인트 컬러 테두리
- **Recurrence Badge**: confirmed만 표시, candidate는 숨김

---

## 2) EvidenceBar

> **역할**: "왜 이 패턴인가"를 댓글 5개 + 재등장 근거로 증명

### 2.1 Data Binding
```typescript
interface EvidenceBarProps {
  // Best Comments 5
  best_comments: Array<{
    text: string;
    likes: number;
    lang: 'ko' | 'en' | 'other';
    tag: 'hook' | 'payoff' | 'product_curiosity' | 'confusion' | 'controversy';
  }>;
  
  // Recurrence Evidence (있으면)
  recurrence?: {
    ancestor_cluster_id: string;
    recurrence_score: number;
    historical_lift: string;      // "+127% avg"
    origin_year: number;
  };
  
  // Risk Tags
  risk_tags: Array<{
    type: 'confusion' | 'controversy' | 'weak_evidence';
    label: string;
  }>;
  
  // Confidence
  evidence_count: number;
  confidence_label: 'strong' | 'moderate' | 'weak';
}
```

### 2.2 Visual Structure
```
┌─────────────────────────────────────┐
│ 💬 Best Comments                    │
├─────────────────────────────────────┤
│ [hook] "이거 첫 2초 보고 멈췄다" 👍1.2K│
│ [payoff] "끝까지 보니까 이해됨" 👍987 │
│ [product] "What brand?" 👍421        │
│ [confusion] "뭔데 인기임?" 👍312     │
│ [controversy] "좀 불편한데…" 👍288   │
├─────────────────────────────────────┤
│ 🔁 Recurrence: 2023 패턴과 92% 유사  │
│    과거 성과: +127% avg lift         │
├─────────────────────────────────────┤
│ ⚠️ Risk: 일부 혼란 반응 있음          │
│ Confidence: Strong (12개 증거)       │
└─────────────────────────────────────┘
```

### 2.3 Design Rules
- **접힘 기본**: 모바일에서는 기본 접힘, 탭하면 펼침
- **태그 색상**: hook/payoff = 녹색, confusion/controversy = 주황
- **없는 경우**: "증거 수집 중..." 표시

---

## 3) Feedback Widget

> **역할**: L2 리랭커 품질 개선을 위한 사용자 피드백 수집

### 3.1 Data Binding
```typescript
interface FeedbackWidgetProps {
  pattern_id: string;
  user_id: string;
  context: 'answer_card' | 'after_shoot';
  
  onSubmit: (feedback: {
    helpful: boolean;
    reason?: string;           // 선택 입력
    tag?: 'wrong_category' | 'outdated' | 'too_hard' | 'perfect';
  }) => void;
}
```

### 3.2 Visual Structure
```
┌─────────────────────────────────────┐
│ 이 추천이 도움이 됐나요?              │
│                                     │
│ [👍 맞아]  [👎 아니야]               │
│                                     │
│ (선택) 이유: [드롭다운]              │
│  - 카테고리가 안 맞아                 │
│  - 이미 지난 트렌드야                 │
│  - 너무 어려워                       │
│  - 완벽해!                          │
└─────────────────────────────────────┘
```

### 3.3 Design Rules
- **위치**: PatternAnswerCard 하단 또는 Shoot 완료 후 모달
- **필수/선택**: 👍👎만 필수, 이유는 선택
- **저장**: `template_feedback` 테이블 활용 가능

---

## 4) Component Composition (Page Level)

### For You 페이지 (과제 해결 모드)
```tsx
<ForYouPage>
  <UserContextInput />           {/* 제품/카테고리/플랫폼 입력 */}
  
  <PatternAnswerCard             {/* Top 1 Answer */}
    pattern={topPattern}
    onViewEvidence={() => setShowEvidence(true)}
    onShoot={() => router.push('/shoot')}
  />
  
  {showEvidence && (
    <EvidenceBar
      best_comments={topPattern.best_comments}
      recurrence={topPattern.recurrence}
      risk_tags={topPattern.risk_tags}
    />
  )}
  
  <FeedbackWidget
    pattern_id={topPattern.pattern_id}
    context="answer_card"
  />
  
  <SecondaryPatterns patterns={restPatterns} />  {/* Top 2-5 접힘 */}
</ForYouPage>
```

### Trending 페이지 (뉴스/발견 모드)
```tsx
<TrendingPage>
  <OutlierFeed>                  {/* 기존 Outlier 브라우징 유지 */}
    <UnifiedOutlierCard />
    <UnifiedOutlierCard />
    ...
  </OutlierFeed>
</TrendingPage>
```

---

## 5) API Endpoint 매핑

| Component | API | 비고 |
|-----------|-----|------|
| PatternAnswerCard | `GET /v1/patterns/recommend` | L1+L2 결과 |
| EvidenceBar | `GET /v1/patterns/{id}/evidence` | 댓글+재등장 |
| FeedbackWidget | `POST /v1/feedback/pattern` | 신규 필요 |

---

## 6) 구현 우선순위

1. **PatternAnswerCard** - 핵심 가치 전달
2. **EvidenceBar** - 신뢰 구축
3. **FeedbackWidget** - 품질 개선 루프
4. **ForYouPage 조합** - 전체 흐름

---

## 7) 기존 컴포넌트 활용

| 신규 | 기존 활용 |
|------|----------|
| PatternAnswerCard | `OutlierCard.tsx` 구조 참고 |
| EvidenceBar | 신규 |
| FeedbackWidget | `TemplateFeedback` 모델 활용 |
| ForYouPage | `SessionHUD.tsx` 패턴 참고 |

---

## 8) Outlier 공용 컴포넌트 [NEW 2024-12-30]

> `/components/outlier/` 디렉토리에 통합된 아웃라이어 관련 공용 컴포넌트

### 8.1 Component List

| Component | 파일명 | 용도 |
|-----------|--------|------|
| TikTokPlayer | `TikTokPlayer.tsx` | TikTok 임베드 재생 (Virlo-style postMessage unmute) |
| TierBadge | `TierBadge.tsx` | S/A/B/C 티어 뱃지 (그라디언트) |
| OutlierMetrics | `OutlierMetrics.tsx` | 조회수/좋아요/공유 메트릭 표시 |
| PipelineStatus | `PipelineStatus.tsx` | 파이프라인 단계 뱃지 (pending→promoted→analyzing→completed) |
| FilmingGuide | `FilmingGuide.tsx` | VDG hook_genome 기반 3단계 촬영 가이드 |
| OutlierDetailModal | `OutlierDetailModal.tsx` | 통합 상세 모달 (TikTok 플레이어 + 메타 + 승격 액션) |

### 8.2 OutlierDetailModal Actions

```
┌─────────────────────────────────────────┐
│ [Pending Stage]                         │
│   ┌────────────┐  ┌────────────────────┐│
│   │  [승격]    │  │  [체험단 선정]    ││
│   │  (파란색)  │  │  (핑크색 + Gift)  ││
│   └────────────┘  └────────────────────┘│
│                                         │
│ [Promoted Stage]                        │
│   ┌────────────────────────────────────┐│
│   │  [VDG 분석 시작]                   ││
│   └────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 8.3 Import

```typescript
import {
    TikTokPlayer,
    TikTokHoverPreview,
    TierBadge,
    OutlierMetrics,
    PipelineStatus,
    FilmingGuide,
    OutlierDetailModal,
} from '@/components/outlier';
```
