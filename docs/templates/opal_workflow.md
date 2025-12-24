# Opal Workflow Template

**목적**: Evidence Loop에서 수집된 데이터를 바탕으로, Opal(또는 대체 LLM)이 다음 의사결정(Decision)을 내리기 위한 프롬프트 및 로직 템플릿입니다.

---

## 1. Input Data (Context)
Opal에게 제공되어야 하는 핵심 데이터입니다.

### 1.1 VDG Evidence Summary
- **Parent**: `{parent_title}`
- **Current Depth**: `{depth}` (1 or 2)
- **Top Variation**: `{best_variant_name}` (Views: `{views}`, Retention: `{retention}`)
- **Insight**:
  > NotebookLM Insights Sheet의 `summary` 및 `key_patterns` 참조 (클러스터/패턴 라벨 포함)

### 1.2 Pattern Lift (옵션)
- **Pattern Lift Summary**: `{pattern_lift_summary}`
- **Top Patterns**: `{top_patterns}`

### 1.3 Constraints
- **Budget**: $500 (Depth 1) / $2000 (Depth 2)
- **Time**: 7 days
- **Brand Guardrails**: No political content, no controversy.

---

## 2. Opal Prompt Template (System Prompt)

```markdown
당신은 'Opal', 최고의 바이럴 콘텐츠 전략가입니다.
주어진 VDG(Viral DNA Graph) 증거 데이터를 분석하고, 다음 실험을 위한 구체적인 의사결정을 내려주세요.

**목표**:
현재 승자 변주(`{best_variant_name}`)의 핵심 성공 요인을 파악하고, 이를 유지하면서 새로운 변수를 추가하여 성과를 극대화하세요.

**출력 형식 (JSON)**:
{
  "decision": "GO" | "STOP" | "PIVOT",
  "rationale": "왜 이런 결정을 내렸는지 3가지 핵심 근거",
  "risks": "예상되는 2가지 리스크",
  "next_experiment": {
    "variant_name": "제안하는 새로운 변주 이름",
    "hypothesis": "이 변주가 성공할 것이라는 가설",
    "changes": [
      "Visual: 변경 사항 1",
      "Audio: 변경 사항 2",
      "Hook: 변경 사항 3"
    ]
  }
}
```

---

## 3. Decision Logic (Rule-based)

### 3.1 GO 조건
- **Retention Rate** > 35% (3s)
- **Viral Coefficient** (Shares/Views) > 0.01

### 3.2 STOP 조건
- **Retention Rate** < 20%
- **Negative Feedback** (Comments) > 10%

---

## 4. Output Contract (Capsule)
Opal 결과는 Capsule 노드의 출력으로 저장됩니다.

```json
{
  "decision": "GO|STOP|PIVOT",
  "rationale": "...",
  "risks": "...",
  "next_experiment": {
    "variant_name": "...",
    "hypothesis": "...",
    "changes": ["...", "..."]
  }
}
```

---

## 5. Execution Flow
1. **Evidence Gathering**: `EvidenceNode`에서 데이터 추출
2. **Analysis**: NotebookLM 리포트 참조
3. **Drafting**: 위 프롬프트로 Opal 호출 (API or Manual)
4. **Review**: `Decision Sheet`에 Draft 상태로 저장 → 인간 승인
5. **Action**: 승인 시 `Experiment Sheet`에 Row 추가 및 크리에이터 배정
