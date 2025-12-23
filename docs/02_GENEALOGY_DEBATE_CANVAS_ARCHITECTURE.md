# Genealogy Debate & Canvas Architecture: 완전 구현 가이드

**작성**: 2025-12-24  
**대상**: 개발팀 (Frontend + Backend + AI)  
**핵심**: Claude 토론 + Canvas 노드 + n8n 통합  
**길이**: 3-4시간 읽음

---

## Part 1: Genealogy Debate 시스템

### 1.1 개념

```
Genealogy Debate란?

Evidence Table을 읽은 Claude가
3명의 분석가 관점에서 토론을 벌이고,
합리적인 결론 + 실험 계획을 제시하는 시스템

3명 분석가:
1. Conservative (보수파): "신뢰도 관점에서..."
2. Aggressive (진취파): "최고 성과 관점에서..."
3. Pragmatic (실용파): "현실적으로..."

결과: 1500-2000 단어 토론 스크립트
```

### 1.2 Claude 프롬프트

```
System Prompt:

당신은 데이터 기반 의사결정 전문가입니다.
Evidence Table을 분석하고, 3명의 분석가 관점에서 토론합니다.

각 분석가의 특성:
- Conservative: 신뢰도(confidence score), 샘플 크기, 이상치 중심
- Aggressive: 최고 성과, 상한선(upper CI), 성장 잠재력 중심
- Pragmatic: 실행 가능성, 비용-효과, 다음 단계 중심

목표: 명확한 다음 액션 도출
```

User Prompt (Example):

```
다음 Evidence Table을 분석하고, 3명 분석가의 토론을 작성하세요.

Evidence Table: "마지막 클릭" (신뢰도 95%)

Depth 1 결과:
- 클리프행거식: 45,000 뷰, 신뢰도 0.72 ± 0.04
- 감정호소식: 38,000 뷰, 신뢰도 0.68 ± 0.05
- 반전식: 32,000 뷰, 신뢰도 0.65 ± 0.06

Depth 2 결과:
- 클리프 + 감정반전: 52,000 뷰, 신뢰도 0.85 ± 0.04 ⭐
- 감정 + 음악변경: 41,000 뷰, 신뢰도 0.78 ± 0.05

질문:
1. 가장 신뢰할 수 있는 결론은?
2. 다음 실험은 어떻게?
3. 위험 요소는?
4. 최종 추천은?

형식:
1. Conservative 발언 (200-300 단어)
2. Aggressive 발언 (200-300 단어)
3. Pragmatic 발언 (200-300 단어)
4. 종합 결론 (300-400 단어)
```

### 1.3 Claude 응답 예시

```
=== Conservative (보수파) ===

"신뢰도 관점에서 분석하면, 가장 신뢰할 수 있는 결론은 
'클리프 + 감정반전' 구조입니다. 

신뢰도 0.85, 신뢰구간 0.81-0.89는 통계적으로 견고합니다.
14일 추적 완료, 52,000 뷰, 충분한 샘플 크기.

흥미롭게도 Depth 1 단일 전략보다 Depth 2 조합이 더 강합니다.
이는 '구조의 조합이 시너지를 만든다'는 중요한 발견입니다.

위험: 이 패턴이 다른 Parent에도 적용될까?
→ 검증 필요: 다음 Parent에서 유사 구조 테스트"

=== Aggressive (진취파) ===

"성장 잠재력으로 보면 매우 흥미롭습니다.

Parent 1M 뷰 대비:
- Depth 1 최고: +4.5% (45K)
- Depth 2 최고: +5.2% (52K)

단순히 +0.7% 증가가 아니라, 참여율도 8% → 14%로 올랐습니다.
이는 구조의 질이 명확히 개선되었다는 의미입니다.

더 나아가, 이 패턴을 다른 콘텐츠에 적용하면?
예: 로맨스, 액션, 일상 콘텐츠 등

→ 스케일 가능성이 높습니다."

=== Pragmatic (실용파) ===

"현실적으로 다음 단계를 제안합니다:

1. 즉시 실행:
   - '클리프 + 감정반전' 구조로 25개 샘플 생성 (다양한 주제)
   - 14일 추적
   - 통계적 검증

2. 병렬 실험:
   - Depth 3 생성: 최고 2개 구조 조합
   - 예: (클리프 + 감정반전) + (음악집중) = ?

3. 리스크 관리:
   - 화제 변화에 따른 구조 효과 분석
   - Creator별 성공률 비교

→ 4주 내 명확한 패턴 확보 가능"

=== 종합 결론 ===

**최우선 추천: "클리프 + 감정반전" 구조**
신뢰도: 0.85 (매우 높음)
확신도: 매우 강함 (3명 분석가 동의)

다음 실험:
- 25개 샘플, 14일 추적
- 다양한 주제 테스트
- Depth 3 준비 (조합 확대)

결과 예상 타이밍:
- Week 1: 샘플 생성
- Week 2: 추적 진행 중
- Week 3: 중간 분석
- Week 4: 최종 결론 (다음 Parent 시작)
```

---

## Part 2: Canvas 노드 시스템

### 2.1 전체 아키텍처

```
Canvas Dashboard (5 TAB)
│
├─ TAB 1: Evidence Table (자동 생성)
│  ├─ Depth 1/2 모든 변주 표시
│  ├─ 신뢰도 점수, 신뢰구간
│  ├─ 순위 자동 정렬
│  └─ 최고 후보 하이라이트
│
├─ TAB 2: Debate Transcript (자동 생성)
│  ├─ 3명 분석가 토론 전문
│  ├─ 각 관점별 요약
│  └─ 색상 구분 (보수, 진취, 실용)
│
├─ TAB 3: Decision Summary (자동 생성)
│  ├─ 최우선 추천
│  ├─ 실험 계획 (구체적)
│  ├─ 리스크 & 대응
│  └─ 확신도 평가
│
├─ TAB 4: Progress Tracker (실시간)
│  ├─ 현재 진행 상황 (Depth 1/2/3)
│  ├─ 추적 일수 (0-14)
│  ├─ 현재 신뢰도 (실시간)
│  └─ 예상 완료일
│
└─ TAB 5: History Archive (자동 기록)
   ├─ 이전 Parent 결과
   ├─ 성공/실패 패턴
   ├─ 다음 세대에 학습 자료 제공
   └─ Genealogy 시각화 (트리 차트)
```

### 2.2 Canvas 노드 타입 (5가지)

#### Type 1: Data Input Nodes

```javascript
// Node: ParentSelector
class ParentSelector extends CanvasNode {
  type = "data_input";
  displayName = "Parent 선택";
  
  inputs = {
    parentList: {
      type: "array",
      description: "사용 가능한 Parent 목록"
    }
  };
  
  outputs = {
    selectedParent: {
      type: "object",
      schema: {
        id: "uuid",
        title: "string",
        views_baseline: "int",
        engagement_rate: "float"
      }
    }
  };
  
  uiComponent = "Dropdown with search";
  
  onSelect(parent) {
    // 선택된 Parent 데이터 로드
    this.outputs.selectedParent = {
      id: parent.id,
      title: parent.title,
      views_baseline: parent.views_baseline,
      engagement_rate: parent.engagement_rate_baseline
    };
    this.emit("outputChanged");
  }
}

// Node: DepthLevelSelector
class DepthLevelSelector extends CanvasNode {
  type = "data_input";
  displayName = "추적 Depth 선택";
  
  inputs = {
    currentDepth: { type: "int" }
  };
  
  outputs = {
    selectedDepth: { type: "int" } // 1 or 2
  };
  
  uiComponent = "Toggle (Depth 1 / Depth 2)";
}

// Node: TimePeriodSelector
class TimePeriodSelector extends CanvasNode {
  type = "data_input";
  displayName = "추적 기간 선택";
  
  uiComponent = "DatePicker (시작일 - 종료일)";
}
```

#### Type 2: Analysis Nodes

```javascript
// Node: EvidenceTableBuilder
class EvidenceTableBuilder extends CanvasNode {
  type = "analysis";
  displayName = "Evidence Table 생성";
  
  inputs = {
    parentId: "uuid",
    depthLevel: "int"
  };
  
  outputs = {
    evidenceTable: {
      type: "object",
      schema: {
        parent_name: "string",
        variants: [{
          name: "string",
          views: "int",
          confidence_score: "float",
          confidence_interval: "array"
        }],
        winner: "object"
      }
    }
  };
  
  async execute(inputs) {
    // Step 1: Load data from DB
    const variants = await db.query(
      `SELECT * FROM depth${inputs.depthLevel}_variants 
       WHERE parent_id = $1`,
      [inputs.parentId]
    );
    
    // Step 2: Generate table
    const table = {
      parent_name: variants[0].parent_name,
      variants: variants
        .map(v => ({
          name: v.name,
          views: v.views,
          confidence_score: v.confidence_score,
          confidence_interval: [
            v.confidence_interval_lower,
            v.confidence_interval_upper
          ]
        }))
        .sort((a, b) => b.confidence_score - a.confidence_score),
      winner: variants[0] // Highest confidence
    };
    
    // Step 3: Save & output
    this.outputs.evidenceTable = table;
    return table;
  }
}

// Node: DebateGenerator
class DebateGenerator extends CanvasNode {
  type = "analysis";
  displayName = "Debate 생성 (Claude)";
  
  inputs = {
    evidenceTable: "object"
  };
  
  outputs = {
    debateTranscript: {
      type: "object",
      schema: {
        conservative: "string",
        aggressive: "string",
        pragmatic: "string",
        conclusion: "string"
      }
    }
  };
  
  async execute(inputs) {
    // Step 1: Format prompt
    const prompt = formatDebatePrompt(inputs.evidenceTable);
    
    // Step 2: Call Claude
    const response = await claude.messages.create({
      model: "claude-opus-4-5",
      max_tokens: 2000,
      messages: [{
        role: "user",
        content: prompt
      }]
    });
    
    // Step 3: Parse & structure
    const debate = parseDebateResponse(response.content[0].text);
    
    this.outputs.debateTranscript = debate;
    return debate;
  }
}
```

#### Type 3: Decision Nodes

```javascript
// Node: DecisionSummary
class DecisionSummary extends CanvasNode {
  type = "decision";
  displayName = "의사결정 요약";
  
  inputs = {
    debateTranscript: "object",
    evidenceTable: "object"
  };
  
  outputs = {
    decision: {
      topRecommendation: "string",
      confidenceLevel: "float",
      experimentPlan: "object",
      risks: "array",
      timeline: "string"
    }
  };
  
  async execute(inputs) {
    const decision = {
      topRecommendation: inputs.debateTranscript.conclusion,
      confidenceLevel: inputs.evidenceTable.winner.confidence_score,
      experimentPlan: {
        nextStep: "Generate 25 samples",
        structure: inputs.evidenceTable.winner.name,
        trackingDays: 14
      },
      risks: [
        "다른 주제에 미치는 영향 불명확",
        "창작자 역량 편차",
        "계절성 요소"
      ],
      timeline: "4주 내 완료 예정"
    };
    
    this.outputs.decision = decision;
    return decision;
  }
}
```

#### Type 4: Execution Nodes

```javascript
// Node: CreatorAssignment
class CreatorAssignment extends CanvasNode {
  type = "execution";
  displayName = "창작자 할당";
  
  inputs = {
    decision: "object"
  };
  
  outputs = {
    assignmentResult: {
      creatorCount: "int",
      assignmentList: "array"
    }
  };
  
  uiComponent = "Multi-select dropdown + confirmation modal";
  
  async execute(inputs) {
    // Step 1: Get available creators
    const creators = await db.query(
      `SELECT * FROM creator_profiles WHERE status = 'active'`
    );
    
    // Step 2: Auto-suggest creators (highest success rate)
    const suggested = creators
      .sort((a, b) => b.success_rate - a.success_rate)
      .slice(0, 5);
    
    // Step 3: Display for manual selection
    const selected = await this.showSelectionUI(suggested);
    
    // Step 4: Create assignments
    const assignments = selected.map(c => ({
      creator_id: c.id,
      task: inputs.decision.nextStep,
      structure: inputs.decision.structure,
      created_at: new Date()
    }));
    
    // Step 5: Save to DB
    await db.insert("creator_assignments", assignments);
    
    this.outputs.assignmentResult = {
      creatorCount: assignments.length,
      assignmentList: assignments
    };
  }
}

// Node: NotificationSender
class NotificationSender extends CanvasNode {
  type = "execution";
  displayName = "알림 발송";
  
  async execute(inputs) {
    // Slack notification
    await slack.send({
      channel: "#content-team",
      text: "새로운 실험 할당됨",
      attachments: [{
        title: inputs.decision.topRecommendation,
        text: `구조: ${inputs.decision.structure}`
      }]
    });
    
    // Email notification
    await email.send({
      to: inputs.assignedCreators.map(c => c.email),
      subject: "새로운 영상 제작 과제",
      template: "experiment_assignment"
    });
  }
}
```

#### Type 5: Feedback & Heritage Nodes

```javascript
// Node: PerformanceDataCollector
class PerformanceDataCollector extends CanvasNode {
  type = "feedback";
  displayName = "성과 데이터 수집";
  
  inputs = {
    assignedVariants: "array"
  };
  
  outputs = {
    performanceData: {
      updated: "int",
      avgViews: "int",
      avgEngagement: "float"
    }
  };
  
  // Runs daily via n8n
  async execute(inputs) {
    for (const variant of inputs.assignedVariants) {
      // Call YouTube API
      const stats = await youtube.getVideoStats(variant.youtube_id);
      
      // Update DB
      await db.update("depth_variants", {
        views: stats.viewCount,
        engagement_rate: stats.likeCount / stats.viewCount,
        updated_at: new Date()
      });
    }
  }
}

// Node: WinnerDetermination
class WinnerDetermination extends CanvasNode {
  type = "feedback";
  displayName = "승자 결정";
  
  async execute(inputs) {
    // Calculate final confidence scores
    // Mark highest as winner
    // Update Heritage system
  }
}

// Node: HeritageUpdate
class HeritageUpdate extends CanvasNode {
  type = "feedback";
  displayName = "Heritage 업데이트";
  
  async execute(inputs) {
    // Save winning structure to heritage database
    // Mark for next generation learning
    // Update creator success metrics
  }
}
```

---

## Part 3: n8n 워크플로우

### 3.1 Workflow 1: Evidence Table & Debate 생성

```
Workflow: "Generate Evidence & Debate"

Manual Trigger: User clicks "Analyze" button

Step 1: Load Parent Data
  ├─ Input: parentId
  ├─ Query: SELECT * FROM parents WHERE id = $1
  └─ Output: parent data

Step 2: Load All Variants (Depth 1 & 2)
  ├─ Query Depth 1: depth1_variants WHERE parent_id = $1
  ├─ Query Depth 2: depth2_variants WHERE parent_id = $1
  └─ Output: combined variant list

Step 3: Generate Evidence Table (Local Node)
  ├─ Sort by confidence_score DESC
  ├─ Format as table
  └─ Identify winner

Step 4: Call Claude API
  ├─ Model: claude-opus-4-5
  ├─ Prompt: Genealogy Debate prompt
  ├─ Max tokens: 2000
  └─ Output: debate transcript

Step 5: Parse Debate Response
  ├─ Extract: conservative, aggressive, pragmatic, conclusion
  └─ Output: structured debate

Step 6: Generate Decision Summary (Claude)
  ├─ Extract: top recommendation
  ├─ Generate: experiment plan
  ├─ Identify: risks
  └─ Output: decision object

Step 7: Save to Database
  ├─ INSERT INTO debate_results
  └─ INSERT INTO decision_summaries

Step 8: Update Canvas Dashboard
  ├─ Emit: "evidenceTableUpdated"
  ├─ Emit: "debateGenerated"
  ├─ Emit: "decisionReady"
  └─ Refresh: All 5 TABs

Output:
  ✅ Evidence Table (TAB 1)
  ✅ Debate Transcript (TAB 2)
  ✅ Decision Summary (TAB 3)
  ✅ Ready for creator assignment
```

### 3.2 Workflow 2: Daily Performance Collection

```
Workflow: "Collect Performance Data"

Scheduled Trigger: Daily at 09:00 UTC

Step 1: Get Active Variants
  ├─ Query: SELECT * FROM depth_variants WHERE status = 'tracking'
  └─ Output: list of video_ids

Step 2: For Each Variant (Parallel)
  ├─ Call: YouTube API
  │  ├─ GET: statistics (viewCount, likeCount, commentCount)
  │  └─ Output: performance metrics
  │
  ├─ Calculate: engagement_rate, improvement_pct
  └─ Output: calculated metrics

Step 3: Update Database
  ├─ UPDATE depth_variants SET views = $1, engagement_rate = $2
  └─ Repeat for all variants

Step 4: Check Completion (14 days)
  ├─ IF tracking_days == 14:
  │  ├─ Calculate: confidence_score
  │  ├─ Calculate: confidence_interval
  │  ├─ SET status = 'complete'
  │  └─ Trigger: "Variant complete" event
  │
  └─ ELSE: Continue next day

Step 5: Regenerate Evidence Table (Daily)
  ├─ Call: generate_evidence_table()
  ├─ Save to DB
  ├─ Update: Progress Tracker (TAB 4)
  └─ Emit: "progressUpdated"

Output:
  ✅ All variants updated
  ✅ Progress tracker real-time
  ✅ Evidence table regenerated daily
```

---

## Part 4: API 스펙

### Canvas Node API

```typescript
interface CanvasNode {
  id: string;
  type: "data_input" | "analysis" | "decision" | "execution" | "feedback";
  displayName: string;
  
  inputs: Record<string, InputType>;
  outputs: Record<string, OutputType>;
  
  execute(inputs: Record<string, any>): Promise<any>;
  emit(eventName: string, data?: any): void;
}

interface InputType {
  type: "string" | "int" | "float" | "array" | "object" | "uuid";
  description?: string;
  schema?: object;
}

interface OutputType {
  type: string;
  schema?: object;
}

// Connection between nodes
interface NodeConnection {
  fromNode: string;
  fromOutput: string;
  toNode: string;
  toInput: string;
}
```

### n8n HTTP Node

```json
{
  "name": "Call Claude API",
  "type": "http",
  "typeVersion": 1,
  "position": [400, 300],
  "parameters": {
    "url": "https://api.anthropic.com/v1/messages",
    "method": "POST",
    "authentication": "predefinedCredential",
    "headers": {
      "anthropic-version": "2023-06-01",
      "content-type": "application/json"
    },
    "body": {
      "model": "claude-opus-4-5",
      "max_tokens": 2000,
      "messages": [
        {
          "role": "user",
          "content": "{{ $json.prompt }}"
        }
      ]
    }
  }
}
```

---

## Part 5: UI/UX 프로토타입

### TAB 1: Evidence Table UI

```
╔════════════════════════════════════════════════════════════════╗
║ Evidence Table: "마지막 클릭" (신뢰도 95%)              [보고서] ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ 🏆 최고 후보: 클리프 + 감정반전 (신뢰도 0.85)                  ║
║                                                                ║
║ ┌─────────────────────────────────────────────────────────┐   ║
║ │ Variant Name         │ Views  │ Confidence │ 신뢰도   │ │   ║
║ ├─────────────────────────────────────────────────────────┤   ║
║ │ 📊 Depth 1 결과:                                        │   ║
║ │ ✓ 클리프행거식      │ 45K  │ 0.72      │ ±0.04 │ 🥇 │   ║
║ │   감정호소식       │ 38K  │ 0.68      │ ±0.05 │ 🥈 │   ║
║ │   반전식           │ 32K  │ 0.65      │ ±0.06 │ 🥉 │   ║
║ │                                                       │   ║
║ │ 📊 Depth 2 결과:                                      │   ║
║ │ ⭐ 클리프 + 감정반전│ 52K  │ 0.85      │ ±0.04 │ 최고 │   ║
║ │   감정 + 음악변경 │ 41K  │ 0.78      │ ±0.05 │ 2순위 │   ║
║ └─────────────────────────────────────────────────────────┘   ║
║                                                                ║
║ 📈 성과 분석:                                                  ║
║ • Parent 대비 최고 성과: +31% (32K → 52K)                     ║
║ • 참여율 개선: 8% → 14% (+6%)                                ║
║ • 구조 조합의 시너지 확인됨                                    ║
║                                                                ║
║ ✅ [다음 단계: Debate 분석으로 이동]                          ║
╚════════════════════════════════════════════════════════════════╝
```

### TAB 2: Debate Transcript UI

```
╔════════════════════════════════════════════════════════════════╗
║ Debate Transcript                                      [내보내기] ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ 🔴 Conservative (보수파)                                       ║
║ ─────────────────────────────────────────────────────────     ║
║ "신뢰도 관점에서 분석하면, 가장 신뢰할 수 있는 결론은        ║
║  '클리프 + 감정반전' 구조입니다.                              ║
║  신뢰도 0.85, 신뢰구간 0.81-0.89는 통계적으로 견고합니다.  ║
║  ...                                                         ║
║ (총 250 단어)                                                ║
║                                                                ║
║ 🔵 Aggressive (진취파)                                         ║
║ ─────────────────────────────────────────────────────────     ║
║ "성장 잠재력으로 보면 매우 흥미롭습니다.                      ║
║  Parent 1M 뷰 대비 +5.2%는 단순한 증가가 아니라...          ║
║  ...                                                         ║
║ (총 280 단어)                                                ║
║                                                                ║
║ 🟢 Pragmatic (실용파)                                          ║
║ ─────────────────────────────────────────────────────────     ║
║ "현실적으로 다음 단계를 제안합니다.                          ║
║  1. 즉시 실행: '클리프 + 감정반전' 구조로 25개 샘플         ║
║  ...                                                         ║
║ (총 320 단어)                                                ║
║                                                                ║
║ ✅ [결론: Decision Summary로 이동]                             ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Part 6: n8n 와이어링 예시

```
┌─────────────┐
│  Manual     │
│  Trigger    │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Load Parent Data │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Load Variants    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Generate Table   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Claude API Call  │
│ (Debate)         │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Parse Response   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Save to DB       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Update Canvas    │
│ (All 5 TABs)     │
└──────┬───────────┘
       │
       ▼
   ✅ Complete
```

---

## Part 7: 통합 흐름

```
User: Canvas 열기 → Parent "마지막 클릭" 선택
         │
         ▼
n8n Workflow 시작
         │
         ├─ Evidence Table 생성 (3초)
         ├─ Claude 토론 생성 (15초)
         └─ Decision Summary 생성 (10초)
         │
         ▼
Canvas TAB 1-3 업데이트 (실시간)
         │
         ▼
User: "이 계획으로 진행" 클릭
         │
         ▼
Creator Assignment Node 실행
         │
         ▼
25개 샘플 생성 시작
         │
         ▼
14일 추적 시작
         │
         ├─ Daily: Performance Collection (자동)
         ├─ Daily: Progress Tracker 업데이트
         └─ Day 14: 최종 Evidence Table 생성
         │
         ▼
다음 Parent 시작
```

---

**이것이 완전 자동화된 "증거 기반 의사결정" 시스템입니다.**