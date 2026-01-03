# Page IA Redesign: Discover → Session 중심

**목표**: L1/L2 자동화 + Temporal Recurrence 도입에 맞춰 네비게이션 구조를 "탐색 중심 → 세션/추천 중심"으로 전환  
**Updated**: 2026-01-03 (Discover → 홈 통합, Ops 리다이렉트 반영)

---

## 1) 현재 IA 구조 (AS-IS)

### 메인 라우트
```
/                    → 홈 (Unified Outlier Discovery)
/(app)/discover      → `/` 리다이렉트 (legacy)
/(app)/boards        → Evidence Boards
/(app)/knowledge     → 지식 라이브러리
/for-you             → Answer-First 추천
/outliers            → `/ops/outliers` 리다이렉트 (Ops)
/remix/*             → 리믹스 세션
/guide/*             → 간단 촬영 가이드
/session/*           → 세션 기반 작업 흐름
/canvas              → `/ops/canvas` 리다이렉트 (Ops)
/pipelines           → `/ops/pipelines` 리다이렉트 (Ops)
/ops/*               → Ops Console (outliers/canvas/pipelines)
/o2o/*               → O2O 캠페인
/my/*                → 마이페이지
/calibration         → Taste Calibration
```

### 문제점
- **탐색 중심**: 홈 피드는 여전히 브라우징 중심
- **분산된 진입점**: `/for-you`와 `/remix`/`/session` 흐름이 분리됨
- **Role 게이팅 미구현**: Creator/Business/Ops 메뉴 분리 미완

---

## 2) 제안 IA 구조 (TO-BE)

### 2.1 핵심 원칙
1. **Answer-First (For You)**: 검색보다 추천을 먼저 제시하는 UX 원칙 (추천 결과가 첫 화면)
2. **두 가지 모드 분리**: 홈(Outlier Discovery) vs 과제(For You)
3. **세션 기반 흐름**: 상태가 유지되는 단일 작업 흐름
4. **Role 기반 게이팅**: Creator/Business/Ops 콘텐츠 분리 (planned)

### 2.2 새 라우트 구조 (2026-01-03 업데이트)
```
/                    → 홈 (Outlier Discovery 피드)
├── /for-you         → 과제 모드 (L1/L2 추천)
├── /session/*       → 세션 기반 작업 흐름
│   ├── /session/input    → 상황 입력
│   ├── /session/result   → 추천 결과 + EvidenceBar
│   └── /session/shoot    → 촬영 가이드 + CTA
├── /remix/*         → 리믹스 세션 (레거시 플로우 유지)
├── /guide/*         → 간단 촬영 가이드
├── /my/*            → 마이페이지 (성과/로열티)
└── /ops/*           → 운영자 도구 (admin/curator only)
    ├── /ops/outliers
    ├── /ops/canvas
    └── /ops/pipelines
```

> ⚠️ **리다이렉트**: `/discover` → `/`, `/outliers`/`/canvas`/`/pipelines` → `/ops/*`

---

## 3) 탭 네비게이션 (BottomNav)

### Creator 모드 (2025-12-31 업데이트)
| 순서 | 아이콘 | 라벨 | 라우트 |
|------|--------|------|--------|
| 1 | 🏠 | Home | `/` |
| 2 | ✨ | For You | `/for-you` |
| 3 | 🎬 | Shoot | `/session/shoot` |
| 4 | 👤 | My | `/my` |

### Business 모드
| 순서 | 아이콘 | 라벨 | 라우트 |
|------|--------|------|--------|
| 1 | 📊 | Patterns | `/for-you` |
| 2 | 📋 | Evidence | `/boards` |
| 3 | 🎁 | O2O | `/o2o` |
| 4 | 👤 | My | `/my` |

---

## 4) 페이지별 상세

### 4.1 `/` (홈 / 뉴스 모드)
> "요즘 뭐가 뜨는지 보고 싶다"

- **콘텐츠**: 아웃라이어 피드 (Discover 통합)
- **정렬**: 플랫폼/티어 필터 + 검색
- **카드**: `UnifiedOutlierCard` 재사용
- **CTA**: "이 패턴으로 촬영하기" → Session 진입

### 4.2 `/for-you` (과제 모드)
> "내 상황에 맞는 패턴 찾아줘"

- **입력**: 제품/카테고리/플랫폼 (간단 폼)
- **출력**: `PatternAnswerCard` (Top 1) + Secondary (Top 2-5)
- **근거**: `EvidenceBar` (댓글 5개 + 재등장)
- **피드백**: `FeedbackWidget`
- **CTA**: "이 패턴으로 촬영하기" → Session 진입

### 4.3 `/session/*` (세션 흐름)
> 상태가 유지되는 단일 작업 흐름

**세션 상태 (SessionContext)**
```typescript
interface SessionState {
  pattern_id: string;
  cluster_id: string;
  input_context: {
    product?: string;
    category: string;
    platform: string;
  };
  evidence_viewed: boolean;
  shoot_started: boolean;
}
```

**세션 단계**
| 단계 | 라우트 | 설명 |
|------|--------|------|
| 1 | `/session/input` | 상황 입력 (For You에서 스킵 가능) |
| 2 | `/session/result` | 추천 결과 + EvidenceBar |
| 3 | `/session/shoot` | 촬영 가이드 + Variable Slot |

### 4.4 `/my` (마이페이지)
- 내 촬영 기록
- 성과/로열티
- 설정

### 4.5 `/ops` (운영자 전용, 숨김)
- Outlier 수집/선별
- Evidence/Decision 관리
- Cluster/Lineage 그래프
- Canvas Pro 접근

---

## 5) Role Switch (planned)

현재 헤더/사이드바에 Role Switch UI는 노출되지 않으며, BottomNav는 기본 `creator` 모드로 렌더링된다.

### 헤더 위치
```
┌─────────────────────────────────────┐
│ [Logo]         [Creator ↔ Business] │
└─────────────────────────────────────┘
```

### 상태 저장
```typescript
// localStorage + Context
const [role, setRole] = useState<'creator' | 'business'>('creator');
```

### 게이팅 규칙 (목표)
- Creator: `/`, `/for-you`, `/session/*`, `/my`
- Business: `/for-you`, `/boards`, `/o2o`, `/my`
- Ops (is_curator=true): `/ops/*`

---

## 6) 기존 라우트 매핑 (마이그레이션)

| AS-IS | TO-BE | 비고 |
|-------|-------|------|
| `/(app)/discover` | `/` | 리다이렉트 |
| `/outliers` | `/ops/outliers` | Ops 전용 리다이렉트 |
| `/canvas` | `/ops/canvas` | Ops 전용 리다이렉트 |
| `/pipelines` | `/ops/pipelines` | Ops 전용 리다이렉트 |
| `/remix/[id]` | 유지 | 레거시 플로우 유지 |
| `/guide/[id]` | 유지 | 간단 가이드 페이지 유지 |
| `/calibration` | `/calibration` | 유지 |
| `/o2o/*` | `/o2o/*` | 유지 (Business) |

---

## 7) 구현 우선순위

1. **`/for-you` + `PatternAnswerCard`** — 핵심 Answer-First (For You)
2. **`/session/*` 세션 흐름** — 상태 유지 작업
3. **`/discover` → `/` 리다이렉트** — 홈 통합
4. **`/outliers`/`/canvas`/`/pipelines` → `/ops/*`** — Ops 전용 이동
5. **Role Switch** — BottomNav 분기 (planned)

---

## 8) 현재 파일 구성 (요약)

### 구현된 라우트/컴포넌트
```
frontend/src/app/page.tsx
frontend/src/app/(app)/for-you/page.tsx
frontend/src/app/session/input/page.tsx
frontend/src/app/session/result/page.tsx
frontend/src/app/session/shoot/page.tsx
frontend/src/app/(app)/discover/page.tsx   # redirect → /
frontend/src/app/outliers/page.tsx         # redirect → /ops/outliers
frontend/src/app/canvas/page.tsx           # redirect → /ops/canvas
frontend/src/app/pipelines/page.tsx        # redirect → /ops/pipelines
frontend/src/contexts/SessionContext.tsx
frontend/src/components/PatternAnswerCard.tsx
frontend/src/components/EvidenceBar.tsx
frontend/src/components/FeedbackWidget.tsx
```

### 변경된 레이아웃/네비게이션
```
frontend/src/components/BottomNav.tsx       # role param 지원 (기본 creator)
frontend/src/components/AppHeader.tsx       # i18n + 고정 탭
frontend/src/app/layout.tsx                 # NextIntlClientProvider 적용
```
