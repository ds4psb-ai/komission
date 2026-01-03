# 2025 H2 UI/UX Architecture Guide

**Komission 프로젝트를 위한 최신 프론트엔드 아키텍처 및 애니메이션 전략**

**Updated**: 2026-01-04 | **Based on**: 웹검색 2025-12 기준

---

## 📋 Executive Summary

2025년 하반기 프론트엔드 UI 생태계는 **네이티브 브라우저 API + AI Agent 통합**을 중심으로 진화하고 있습니다. 본 문서는 Komission 에이전트 채팅 + Hub-Spokes UI에 즉시 적용 가능한 핵심 기술들을 정리합니다.

### 핵심 채택 권장 기술

| 우선순위 | 기술 | 적용 영역 | 난이도 | 상태 |
|----------|------|----------|--------|------|
| ⭐⭐⭐⭐⭐ | Motion 12 `layoutId` | Hub-Spokes Morph 애니메이션 | 하 | **Phase 1** |
| ⭐⭐⭐⭐⭐ | CSS Scroll-Driven | 카드 그리드 스크롤 효과 | 하 | **Phase 1** |
| ⭐⭐⭐⭐ | Next.js 15.2 `template.tsx` | 페이지 진입 애니메이션 | 하 | **Phase 1** |
| ⭐⭐⭐⭐ | **A2UI + CopilotKit** | 코미 Agent 동적 UI 생성 | 중 | **Phase 2** ✅ |
| ⭐⭐⭐⭐ | **AG-UI Protocol** | Agent↔App 양방향 통신 | 중 | **Phase 2** |
| ⭐⭐⭐ | React 19 View Transitions | 뷰 전환 (실험적) | 중 | Phase 3 |

---

## 1. Motion 12 (Framer Motion) Layout Animations

### 2025년 주요 업데이트 (웹검색 검증)

| 버전 | 주요 변경 |
|------|----------|
| v12.22.0 | `staggerChildren` deprecated → `delayChildren: stagger()` |
| v12.23.6 | 자동 `prefers-reduced-motion` 폴백 |
| v12.23.11 | `delayChildren: stagger({ from: "center" })` 지원 |
| v12.23.12 | View Animation 내부 API 노출 |

### layoutId를 활용한 Hub-Spokes Morph

```tsx
import { motion, AnimatePresence } from 'framer-motion';

function HubSpokesView({ parentCard, variationCards }) {
  return (
    <AnimatePresence>
      {/* Parent Card → Hub Center */}
      <motion.div
        layoutId={`card-${parentCard.id}`}
        className="hub-center"
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        <HubCard data={parentCard} />
      </motion.div>
      
      {/* Variation Cards → Spokes */}
      <motion.div
        className="spokes"
        initial="hidden"
        animate="visible"
        variants={{
          visible: { 
            transition: { 
              delayChildren: stagger(0.15, { from: "first" })
            } 
          }
        }}
      >
        {variationCards.map((card) => (
          <motion.div
            key={card.id}
            layoutId={`card-${card.id}`}
            variants={{
              hidden: { opacity: 0, y: 80, scale: 0.8 },
              visible: { opacity: 1, y: 0, scale: 1 }
            }}
          >
            <SpokeOption data={card} />
          </motion.div>
        ))}
      </motion.div>
    </AnimatePresence>
  );
}
```

### 성능 최적화 원칙

| ✅ 권장 | ❌ 회피 |
|---------|---------|
| `transform` (x, y, scale, rotate) | `width`, `height` |
| `opacity` | `top`, `left`, `margin` |
| GPU 가속 (`will-change`) | `box-shadow` 직접 애니메이션 |

---

## 2. CSS Scroll-Driven Animations

### 브라우저 지원 (2025년 말 기준)

> [!WARNING]
> **Firefox는 플래그 뒤에서만 지원**됩니다. `@supports (animation-timeline: view())` 필수.

| 브라우저 | 지원 상태 |
|----------|----------|
| Chrome 116+ | ✅ 완전 지원 |
| Firefox 114+ | ⚠️ 플래그만 (`layout.css.scroll-driven-animations.enabled`) |
| Safari 26+ | ✅ (2025-09-15+) |
| Edge 116+ | ✅ 완전 지원 |

### 두 가지 타임라인

**scroll() - 컨테이너 스크롤 진행도**
```css
.parallax-bg {
  animation: parallax linear;
  animation-timeline: scroll();
}
@keyframes parallax {
  from { transform: translateY(0); }
  to { transform: translateY(-50%); }
}
```

**view() - 요소 뷰포트 진입/이탈**
```css
.fade-in-card {
  animation: fadeIn ease-out;
  animation-timeline: view();
  animation-range: entry 10% cover 30%;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(50px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### Komission 적용: Masonry 카드 그리드 스크롤 효과

> [!NOTE]
> `09_UI_UX_STRATEGY.md` 원칙 준수: **150-250ms, 페이드/슬라이드만, 3D 효과 금지**

```css
.outlier-card {
  animation: cardReveal 0.2s ease-out both;
  animation-timeline: view();
  animation-range: entry 20% cover 40%;
}

@keyframes cardReveal {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## 3. Next.js 15.2 Page Transitions

### 핵심 기능 (웹검색 검증)

| 기능 | 설명 |
|------|------|
| `viewTransitions` | `next.config.js`에서 플래그 활성화 |
| `template.tsx` | 라우트 변경 시마다 리마운트 → 진입 애니메이션 트리거 |
| Speculation Rules | View Transitions + 프리렌더링 = 즉각적 전환 |

### template.tsx 활용 패턴

```tsx
// app/template.tsx
'use client';
import { motion } from 'framer-motion';

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}
```

### next.config.js 설정

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    viewTransitions: true,  // React View Transitions 활성화
  },
};
module.exports = nextConfig;
```

---

## 4. MCP Apps UI Integration (SEP-1865)

### 2025년 MCP 생태계 현황 (웹검색 검증)

| 날짜 | 이벤트 |
|------|--------|
| 2025-11 | MCP 신규 스펙 (OAuth 2.1, Structured Tool Output, Tasks) |
| 2025-11 | MCP Apps Extension (SEP-1865) 발표 |
| 2025-12-09 | Anthropic → AAIF 기증 |

### MCP Apps 아키텍처

```
┌─────────────────────────────────────────────────┐
│                   MCP Host                      │
│  ┌──────────────┐    ┌──────────────────────┐  │
│  │   LLM Agent  │────│   MCP Client         │  │
│  │   (코미)     │    │   (JSON-RPC 2.0)     │  │
│  └──────────────┘    └──────────┬───────────┘  │
│                                 │              │
└─────────────────────────────────┼──────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   ▼                   │
              │             MCP Server                │
              │  ┌─────────────────────────────────┐  │
              │  │ Tools    │ Resources │ Prompts  │  │
              │  │ (Actions)│ (Data)    │ (Instruct)│  │
              │  └─────────────────────────────────┘  │
              │                   │                   │
              │  ┌───────────────────────────────┐    │
              │  │      UI Resource (ui://)      │    │
              │  │   (Sandboxed iframe HTML)     │    │
              │  └───────────────────────────────┘    │
              └───────────────────────────────────────┘
```

### Komission 적용: 코미 동적 UI 생성

```python
# MCP Server: Hub-Spokes UI Tool
@mcp.tool()
async def show_hub_preview(
    parent_id: str,
    variations: list[str],
    ctx: Context = None
) -> dict:
    """Hub-Spokes 프리뷰를 인터랙티브 UI로 표시"""
    
    preview_html = generate_hub_spokes_html(parent_id, variations)
    
    return {
        "type": "resource",
        "uri": f"ui://hub-preview/{parent_id}",
        "content": preview_html,  # Sandboxed iframe에서 렌더링
    }
```

---

## 5. Google A2UI (Agent-to-UI) Protocol

### 2025-12 발표 (웹검색 검증)

Google이 2025년 12월에 발표한 **A2UI 프로토콜**은 AI 에이전트가 네이티브 컴포넌트를 JSON Blueprint로 전송하는 방식입니다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **보안** | 실행 가능 코드 대신 JSON description 전송 |
| **크로스 플랫폼** | React, Flutter, SwiftUI 네이티브 렌더링 |
| **신뢰 카탈로그** | 미리 승인된 컴포넌트만 참조 |

### A2UI Blueprint 예시

```json
{
  "type": "a2ui_blueprint",
  "components": [
    {
      "type": "Card",
      "props": { "variant": "hub", "title": "부모 패턴" },
      "children": [
        { "type": "Text", "content": "28만뷰 훅 패턴..." },
        { "type": "Button", "action": "select_variation", "label": "선택" }
      ]
    },
    {
      "type": "OptionGroup",
      "props": { "layout": "horizontal" },
      "children": [
        { "type": "OptionCard", "props": { "label": "훅 변형", "id": "var-1" } },
        { "type": "OptionCard", "props": { "label": "오디오 변형", "id": "var-2" } },
        { "type": "OptionCard", "props": { "label": "비주얼 변형", "id": "var-3" } }
      ]
    }
  ]
}
```

### Komission 향후 적용

| 단계 | 적용 |
|------|------|
| Phase 1 | MCP-UI (SEP-1865) 위젯 |
| Phase 2 | A2UI Blueprint 렌더러 (React) |
| Phase 3 | Gemini 3 Flash + A2UI 통합 |

---

## 6. Hub-Spokes 최종 구현 전략

### 4단계 시퀀스 (Morph Transition)

```tsx
function HubSpokesTransition({ parentCard, variations, onComplete }) {
  const [phase, setPhase] = useState<'idle' | 'dim' | 'morph' | 'complete'>('idle');
  
  return (
    <>
      {/* Phase 1: Confirmation */}
      {phase === 'idle' && (
        <ConfirmDialog
          message="이대로 찾으시겠습니까?"
          onConfirm={() => setPhase('dim')}
        />
      )}
      
      {/* Phase 2: Dim Overlay */}
      <motion.div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: phase === 'dim' || phase === 'morph' ? 1 : 0 }}
        onAnimationComplete={() => phase === 'dim' && setPhase('morph')}
      />
      
      {/* Phase 3: Morph + Stagger */}
      <AnimatePresence>
        {phase === 'morph' && (
          <>
            {/* Parent → Hub */}
            <motion.div
              layoutId={`card-${parentCard.id}`}
              className="hub-position"
              transition={{ type: 'spring', duration: 0.25 }}
            />
            
            {/* Variations → Spokes */}
            <motion.div
              variants={{ 
                show: { 
                  transition: { 
                    delayChildren: stagger(0.15, { from: "first" })
                  } 
                } 
              }}
              initial="hidden"
              animate="show"
              onAnimationComplete={() => setPhase('complete')}
            >
              {variations.map(v => (
                <motion.div
                  key={v.id}
                  layoutId={`card-${v.id}`}
                  variants={{
                    hidden: { opacity: 0, y: 80, scale: 0.8 },
                    show: { opacity: 1, y: 0, scale: 1 }
                  }}
                />
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
      
      {/* Phase 4: Complete */}
      {phase === 'complete' && <HubSpokesView onExit={onComplete} />}
    </>
  );
}
```

### 애니메이션 타이밍 표

| 단계 | 요소 | 지속시간 | Easing |
|------|------|----------|--------|
| 1 | 배경 dim overlay | 100ms | ease-out |
| 2 | Hub 카드 fly-in | 250ms | spring (stiffness: 300) |
| 3 | Spokes stagger fly-in | 150ms × 3 | spring |
| 4 | 체험단 fade-in | 200ms | ease-in |
| 5 | 입력창 slide-up | 150ms | ease-out |

---

## 7. 접근성 (prefers-reduced-motion)

### Motion 12 자동 폴백 (v12.23.6+)

```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  // 자동으로 reduced-motion 감지 시 즉시 최종 상태로 전환
/>
```

### CSS 폴백

```css
@media (prefers-reduced-motion: reduce) {
  .outlier-card {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
```

---

## 8. 적용 로드맵

### Phase 1 (즉시 적용)

- [ ] Motion 12 `layoutId` 기반 카드 Morph 구현
- [ ] `template.tsx` 페이지 진입 애니메이션
- [ ] CSS Scroll-Driven 카드 그리드 효과

### Phase 2 (A2UI + CopilotKit 통합)

> [!NOTE]
> Phase 1 완료 후 즈시 시작 가능

- [ ] CopilotKit 설치 및 기본 연동
- [ ] A2UI Hub-Spokes 위젯 JSON 스키마 정의
- [ ] AG-UI 프로토콜로 코미 Agent↔Frontend 연결
- [ ] Motion layoutId와 A2UI 렌더러 통합
- [ ] `staggerChildren` → `delayChildren: stagger()` 마이그레이션

### Phase 3 (선택적 확장)

> [!WARNING]
> 이 항목들은 **실험적**이며 프로덕션 사용을 권장하지 않습니다.
> Phase 1-2 완료 및 제품 검증 후 리서치 단계로만 검토하세요.

- [ ] React 19 View Transitions — Next.js 16에서도 "experimental, not for production" 상태
- [ ] MCP Apps (SEP-1865) — MCP 에코시스템 확장 시 검토
- [ ] A2A (Agent-to-Agent) 프로토콜 — 멀티 에이전트 필요 시

---

### 언어 적합성 게이트 (Phase 2)

> [!IMPORTANT]
> 외국어 아웃라이어는 **자동 캡션 정확도 제한**이 있습니다.
> 번역/요약을 필수로 제공하고, 신뢰도 배지를 표시하세요.

| 조건 | 처리 |
|------|------|
| 한국어 콘텐츠 | 바로 노출 |
| 영어 + 자동캡션 | `번역 제공` + `⚠️ 자동생성` 배지 |
| 기타 언어 | 번역 없으면 노출 제외 |

```python
# 예시: 언어 게이트 로직
def should_show_outlier(outlier: Outlier) -> bool:
    if outlier.language == 'ko':
        return True
    if outlier.language == 'en' and outlier.has_translation:
        return True
    return False  # 번역 없으면 숨김
```

---

## 9. 데이터 소스 전략

> [!IMPORTANT]
> **점진적 전환 계획**
> NotebookLM RAG 데이터셋이 완성되기까지 시간이 필요합니다.
> 그동안 Outlier VDG Pass DB로 운영하고, 점진적으로 강화합니다.

### 9.1 초기 (Now → 3개월)

```
┌─────────────────────────────────────────────────────┐
│                Outlier VDG Pass DB                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │ TikTok    │  │ YouTube   │  │ Instagram │       │
│  │ Outliers  │  │ Shorts    │  │ Reels     │       │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘       │
│        └───────────────┼───────────────┘           │
│                        ▼                            │
│              코미 Agent → A2UI JSON                │
│                  (Hub-Spokes UI)                   │
└─────────────────────────────────────────────────────┘
```

| 데이터 소스 | 역할 |
|------------|------|
| `outliers` 테이블 | VDG Pass 카드 (개별 영상) |
| `evidence` | 댓글 분석, lift 지표 |
| `campaigns` | 체험단 연결 |

### 9.2 점진적 강화 (3개월+)

```
┌─────────────────────────────────────────────────────┐
│        NotebookLM RAG 데이터셋 (점진적 축적)        │
│  ┌────────────────────────────────────────────────┐ │
│  │ 바이럴 패턴 공식 │ Parent/Kids 클러스터  │     │ │
│  │ 훅 공식 요약    │ 크리에이터 스타일 분류 │     │ │
│  └────────────────────────────────────────────────┘ │
│                        │                            │
│                        ▼                            │
│  ┌────────────────────────────────────────────────┐ │
│  │           Outlier VDG Pass DB                  │ │
│  │           (기존 유지 + 연동)                   │ │
│  └────────────────────────────────────────────────┘ │
│                        ▼                            │
│              코미 Agent → A2UI JSON                │
│                  (Hub-Spokes UI)                   │
└─────────────────────────────────────────────────────┘
```

| 단계 | 트리거 | 추가 데이터 |
|------|--------|-------------|
| RAG Gate 통과 | 클러스터 ≥10, 댓글 ≥50 | NotebookLM 요약 주입 |
| RAG Gate 실패 | 데이터 sparse | DB-only 폴백 |

> 자세한 RAG Reliability Gate 로직은 [AGENT_TRAIN_SPEC.md §6](./AGENT_TRAIN_SPEC.md#6-notebooklm-rag-reliability-gate-️) 참조

---

## 10. 기존 접근 vs 2025 H2 권장 접근

| 기존 접근 | 2025 H2 권장 접근 |
|----------|-------------------|
| JS 기반 스크롤 이벤트 | CSS `animation-timeline: scroll()` |
| 수동 FLIP 구현 | React View Transitions |
| 정적 UI | MCP Apps 동적 생성 |
| 개별 요소 transition | Motion `layoutId` Morph |
| `staggerChildren` | `delayChildren: stagger()` |
| 커스텀 reduced-motion 처리 | Motion 12 자동 폴백 |

---

## 10. Web Evidence

| 기술 | 출처 |
|------|------|
| CSS Scroll-Driven | [caniuse.com](https://caniuse.com), [webkit.org](https://webkit.org) |
| Motion 12 stagger | [motion.dev/releases](https://motion.dev/releases) |
| Next.js viewTransitions | [nextjs.org/docs](https://nextjs.org/docs) |
| MCP Apps (SEP-1865) | [modelcontextprotocol.io](https://modelcontextprotocol.io) |
| Google A2UI | [googleblog.com](https://googleblog.com), [marktechpost.com](https://marktechpost.com) |
| AAIF | [agenticaifoundation.org](https://agenticaifoundation.org) |

---

## 결론

> "Hub-Spokes UI는 기술적 트릭이 아니라, **사용자의 의도를 시각적으로 구현**하는 것입니다."

Morph Transition + Stagger를 위 기술들로 구현하면, Komission만의 독보적인 사용자 경험을 만들 수 있습니다.
