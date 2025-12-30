# Debate Script Template (Condition-based)

**목적**: Top 1과 Top 2 변주의 성과 차이가 미비하거나(Diff < 0.03), 리스크가 높은 경우 두 AI 페르소나(Optimist vs Skeptic)가 토론하여 결론을 도출합니다.

---

## 1. Debate Trigger Conditions
다음 중 하나라도 해당되면 토론 모듈이 활성화됩니다.
1. **Low Confidence**: 1위와 2위의 점수 차이가 3% 미만일 때.
2. **High Risk**: 브랜드 안전성(Safe) 점수가 기준 이하일 때.
3. **High Variance**: 조회수는 높지만 참여율이 낮을 때 (Clickbait 의심).

---

## 2. Personas

### 🟢 The Optimist (Max)
- **성격**: 바이럴 잠재력과 성장에 집중. 리스크를 감수하고서라도 기회를 포착하려 함.
- **관점**: "이 지표는 초기 폭발력을 의미해. 조금만 다듬으면 터질 거야."

### 🔴 The Skeptic (Raven)
- **성격**: 데이터 정합성과 리스크 관리에 집중. 일시적 유행이나 어뷰징을 의심함.
- **관점**: "유지율이 떨어지고 있어. 이건 단순 낚시성 콘텐츠야. 예산을 태우면 안 돼."

---

## 3. Script Structure

### Round 1: Opening
- **Max**: 1위 변주를 지지하는 이유 (Viral Factor)
- **Raven**: 1위 변주의 취약점 지적 (Retention, Negative Comments)

### Round 2: Counter-Argument
- **Max**: 리스크 완화 방안 제시 + 2위 변주의 한계 지적
- **Raven**: 1위 변주의 리스크가 치명적임을 재강조 + 대안(Stop/Pivot) 제시

### Round 3: Synthesis (Moderator)
- **Moderator (Opal)**: 두 의견을 종합하여 최종 권고안 도출.

---

## 4. Output Example (Markdown)

> **Max**: "Variant A의 초반 3초 이탈률이 획기적으로 낮아요. 이건 훅이 제대로 먹혔다는 증거입니다. 무조건 GO 해야 합니다."
>
> **Raven**: "하지만 10초 이후 급격히 빠지죠. 내용은 알맹이가 없다는 뜻입니다. 댓글에도 '낚였다'는 반응이 15%나 돼요. 브랜드 이미지 망칩니다."
>
> **Max**: "그건 편집 템포 조절로 해결할 수 있어요. 소재 자체는 훌륭합니다."
>
> **Opal (Decision)**: "토론 결과, **Variant A 수정 후 재실험**으로 결정합니다. Raven이 지적한 후반부 이탈을 막기 위해 B-roll 영상을 보강하세요."
