# Komission Content Studio: Technical Specification

**Version**: 1.1 (CTO Release)
**Date**: 2026-01-07
**Derived From**: Virlo Content Studio Reverse Engineering + Notebook Library Spec
**Status**: Ready for Implementation

---

## 1. Executive Vision

Komission Content Studio is not just a form-filler; it is a **visual reasoning engine**. By adopting the node-based architecture proven by market leaders (Virlo), we shift the user model from "Input → Wait → Output" to "**Connect → Architect → Flow**".

This specification defines the "Best of Breed" features extracted from our deep-dive research, tailored strictly for the Komission Evidence Loop ecosystem.

### Core Value Proposition
- **Visual Evidence Chain**: Users see *why* a decision was made by tracing the graph from `Evidence Node` → `Capsule Node` → `Decision Node` (planned; current build does not enforce chain/provenance rendering).
- **Transparent Economy**: First-class credit visibility ensures users understand the cost of "intelligence" vs "generation".
- **Context-Aware Processing**: The AI Processor is not a black box; it visibly consumes up-stream evidence.
- **Notebook Library Integration**: 분석 스키마/클러스터는 **DB로 래핑**되어 노드로 소비된다 (planned; current build shows static notebook summaries).

---

## 2. Architecture: The Node Graph

We adopt a strictly typed node system to prevent "garbage graphs".

### 2.1 Core Node Types

1.  **Evidence Source (Input)**
    *   *Visual*: Square node, distinct source icon (TikTok/Web/PDF).
    *   *Data*: Holds `snapshot_id` pointing to `VDG_Evidence`.
    *   *Behavior*: Passive. Cannot define logic, only supplies context.

2.  **Notebook Library (Context)**
    *   *Visual*: Rounded node, library icon.
    *   *Data*: `library_entry_id`, `cluster_id`.
    *   *Behavior*: 현재는 정적 요약 표시; DB 연동/NotebookLM 결과 주입은 planned.

3.  **Template Seed (Opal, Optional)**
    *   *Visual*: Dotted outline, "Seed" badge.
    *   *Data*: `seed_id`, `template_type`, `hook`, `shotlist`, `audio`, `timing`, `parent_id`, `cluster_id`.
    *   *Behavior*: Opal이 만든 템플릿 시드를 캡슐/템플릿의 기본값으로 공급.

4.  **Capsule Processor (Decision Engine)**
    *   *Visual*: Larger rectangular node with "Pulse" animation when active.
    *   *Data*: `execution_context` (upstream aggregation), `config` (user prompts).
    *   *Behavior*: The "Brain". Consumes Evidence + Notebook Library, produces Decision.
    *   *Note*: LLM 모델 선택은 캡슐 내부에서 관리한다.

5.  **Brief/Draft (Output)**
    *   *Visual*: Document shape, previewable inline.
    *   *Data*: `markdown_body`, `media_assets`.
    *   *Behavior*: Actionable. Export to PDF, Sync to Notion.

6.  **Template Node (Execution)**
    *   *Visual*: Check‑list panel.
    *   *Data*: `template_version_id`, `slots`.
    *   *Behavior*: 창작자/PD/작가의 커스텀 실행 단계.

### 2.2 Connection Rules (Schema)
The graph allows **Many-to-One** for context, but **One-to-One** for flow control.

```json
{
  "rules": [
    { "from": "EvidenceSource", "to": "CapsuleProcessor", "type": "context", "max": 5 },
    { "from": "NotebookLibrary", "to": "CapsuleProcessor", "type": "context", "max": 3 },
    { "from": "CapsuleProcessor", "to": "BriefDraft", "type": "flow", "max": 1 },
    { "from": "BriefDraft", "to": "TemplateNode", "type": "flow", "max": 1 }
  ]
}
```
Note: Connection rule enforcement is planned; current build does not enforce schema validation on connections.

---

## 3. The Komission Visual System (UI/UX)

Derived from Virlo's "Dark Studio" aesthetic but refined for professional analytics clarity.

### 3.1 Color DNA
*   **Canvas Background**: `#F5F5F7` (Apple‑like neutral)  
*   **Panel Surface**: `#FFFFFF` (Clean white)  
*   **Accent (Primary)**: `#007AFF` (Apple Blue)  
*   **Status Signals**:
    *   *Success*: `#10B981` (Emerald)
    *   *Processing*: `#7C3AED` (Violet)
    *   *Error*: `#EF4444` (Red)

> Pro 모드에서는 캔버스 배경만 **다크 옵션**으로 토글 가능.

### 3.2 Layout & Navigation
*   **Left Rail (Fixed)**: 
    *   `Dashboard` (Overview)
    *   `Evidence` (Research)
    *   `Studio` (The Canvas) - **Default Home**
    *   `Credits` (Wallet) - *High visibility*
*   **Right Rail (Context)**:
    *   *Inspector*: "Selected Node" properties.
    *   *Mini-Map*: Navigational aid.

### 3.3 Interaction Micro-interactions
*   **Drag-to-Connect**: Rubber-band line with "snap" effect on valid ports.
*   **Port Hover**: Valid target ports glow Green (Context) or Blue (Flow).
*   **Live Token Counter**: Capsule Processor node displays estimated cost *before* run (planned).

---

## 4. Economic Model: Credits & Billing

We adopt the **Dual-Wallet** system to separate "SaaS Value" from "Compute Cost".

### 4.1 Credit Types
1.  **Creator Credits (Subscription)**: Monthly allowance. Use for standard features (Layouts, simple summaries).
2.  **Neural Credits (Pay-as-you-go)**: High-power usage. Use for Deep Reasoning (Capsule/LLM) and broad crawling.

### 4.2 UI Representation
*   **Top Bar Pilla**: Always visible `[ ⚡️ 4,200 | 🧠 150 ]` (Standard | Neural).
*   **Low Balance Action**: "Auto-top up" or "Buy Pack" modal triggers at <10% threshold.
*   **Affiliate Integration**: "Earn Neural Credits" link next to wallet.

---

## 5. Implementation Roadmap (Phased)

### Phase 1: The "Skeleton" Canvas
*   [ ] Initialize `React Flow` or `XYFlow`.
*   [ ] Implement specific `NodeSpec` types (Input/Notebook/Capsule/Output/Template).
*   [ ] Build "Drag-Connect" validation logic.

### Phase 2: The "Capsule Brain" Integration
*   [ ] Connect Capsule Processor Node to `run_real_evidence_loop.py` backend (planned, not implemented in current build).
*   [ ] Stream "Status" (Running/Done) via WebSocket/Polling to node UI (planned).
*   [ ] Visualize `VDG_Evidence` data when clicking Input nodes (planned).
*   [ ] Notebook Library Node 연동 (DB → 노드) (planned).

### Phase 3: The "Credit Wallet"
*   [ ] Implement Credit Ledger in Postgres.
*   [ ] Add "Cost Estimation" hook to Capsule Node.
*   [ ] Build Billing Page UI.

### Phase 4: Template Learning (RL-lite)
*   [ ] Template Versioning + Feedback 로그 수집
*   [ ] 성과 기반 기본값 업데이트 (Bandit/Ranking)

---

## 6. Closing Note

This specification represents the functional endpoint of our research. It strips away the "social features" of Virlo (Community, Yap) to focus entirely on **high-fidelity evidence processing**.

**Komission Studio is the IDE for Viral Engineering.**
