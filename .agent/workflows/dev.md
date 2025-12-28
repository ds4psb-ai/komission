---
description: Convert user request to 2025-style structured prompt and execute
---

# /dev - Development Task Executor

When user mentions `/dev` or you receive a development request, auto-convert to this format:

## Template

```
[PERSONA] Act as Komission [role based on task: backend/frontend/data/fullstack] engineer.

[CONTEXT]
Project: Komission
Non-negotiables:
- DB = SoR, Sheets = ops bus
- NotebookLM = Pattern Engine (outputs DB-wrapped)
- VDG/DB가 패턴 경계를 고정
- Canvas = I/O only
Use docs: [relevant docs based on task type]

[TASK] [Action verb] [what] for [purpose].

[CONSTRAINTS]
- [2-3 key constraints from project principles]
- Align with existing patterns
- Minimal changes

[FORMAT] [Specific output: code/component/script/migration]

[POWER] Think step-by-step. Critique for edge cases.
```

## Role Selection

| Task Type | Persona | Key Docs |
|-----------|---------|----------|
| API/Backend | backend engineer | 15_FINAL_ARCHITECTURE, 07_PIPELINE_PLAYBOOK |
| UI/Frontend | frontend expert | 10_UI_UX_STRATEGY, 17_TEMPORAL_VARIATION_THEORY |
| Pipeline/Script | data engineer | 01_VDG_SYSTEM, 02_EVIDENCE_LOOP_CANVAS |
| Integration | fullstack architect | 15_FINAL_ARCHITECTURE, 08_CANVAS_NODE_CONTRACTS |
| Bug fix | debugging specialist | [relevant to bug area] |

## Execution Flow

1. Parse user request
2. Select appropriate persona and docs
3. Apply template
4. Execute with step-by-step thinking
5. Critique own output before delivery
