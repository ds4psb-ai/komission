# Komission Roadmap: MVP → 완벽 (운영 증명)

> **현재 상태**: NotebookLM-ready + MVP 실행 가능  
> **목표**: 플라이휠이 실제로 굴러가는 "완벽" 상태  
> **작성일**: 2025-12-30

---

## Executive Summary

```
아키텍처/스키마/하드닝 ✅ 완료
          ↓
┌─────────────────────────────────────┐
│  🎯 운영 증명 단계 (현재 위치)       │
├─────────────────────────────────────┤
│  P1. 세션 로그 50-100개 확보        │
│  P2. 클러스터 10개 수동 생성        │
│  P3. 주간 DistillRun 운영           │
│  P4. google.genai 마이그레이션      │
└─────────────────────────────────────┘
          ↓
       "완벽" 선언 가능
```

---

## Part 1: 현재 상태 진단

### ✅ 이미 막은 치명적 결점

| 항목 | 상태 | 의미 |
|------|------|------|
| Metric Registry SSoT | ✅ | 1년 뒤에도 metric 의미 고정 |
| Deterministic IDs | ✅ | RL 조인키 안정 (ap_id, evidence_id) |
| Contract-First Compiler | ✅ | "침묵하는 감독" 방지 |
| Plan-based Frame Extraction | ✅ | 비용 절감 + 고정밀 |
| Promotion Safety | ✅ | canary/diversity/rollback |
| compliance_unknown_reason | ✅ | RL 데이터 품질 |

**결론**: "모델이 더 똑똑해져도 Pack의 가치가 올라가는 구조" 기술적 성립 ✅

### 🔶 아직 "운영 검증" 필요

| 항목 | 현재 | 목표 |
|------|------|------|
| 세션 로그 적재 | 0개 | 50-100개 |
| NotebookLM | ready | integrated |
| Cluster | 스키마만 | 10개 실제 데이터 |
| DistillRun | 미실행 | 주간 1회 |

---

## Part 2: 우선순위별 로드맵

### P1. 운영 가능한 최소 루프 증명 (Week 1-2)

**목표**: 세션 로그가 "끊김 없이" 쌓이는지 증명

#### 1.1 킬러 Pack 3개 선정
```
패턴 A: [훅 유형] - 가장 성공률 높은 패턴
패턴 B: [구도 유형] - 시각적 차별화 패턴
패턴 C: [오디오 유형] - 오디오 기반 패턴
```

#### 1.2 세션 50-100개 확보
| 모드 | 목표 세션 | 비고 |
|------|----------|------|
| 오마쥬 | 20개 | DNA 100% Lock |
| 변주 | 20개 | Mutation Slot 활용 |
| 체험단 | 10개 | Campaign 제약 |

#### 1.3 로그 3종 이벤트 검증 (DoD)

```python
# 반드시 기록되어야 할 이벤트
1. rule_evaluated      # 체크포인트마다 (개입 없는 구간 포함)
2. intervention_delivered  # 실제 코칭 전달
3. outcome_observed    # 즉시 + 지연(upload) 결과
```

**핵심**: 개입하지 않은 구간도 "규칙 평가 결과"가 남아야 학습 가능

#### 1.4 검증 체크리스트
- [ ] intervention_id로 intervention ↔ outcome 조인 100%
- [ ] compliance_unknown_reason 누락률 < 5%
- [ ] upload_outcome_proxy 입력률 > 30%

---

### P2. 클러스터 10개 수동 생성 (Week 1-2, 병행)

**목표**: NotebookLM Distill 가능한 Parent-Kids 구조

#### 2.1 클러스터 구성 템플릿

```yaml
cluster:
  cluster_id: "cluster_hook_question_v1"
  cluster_name: "질문형 훅 패턴"
  
  parent:
    vdg_id: "vdg_xxx"
    content_id: "tiktok_abc123"
    outlier_tier: "S"
    
  kids:  # 3-8개
    - vdg_id: "vdg_yyy"
      variation_type: "homage"
      success: true
    - vdg_id: "vdg_zzz"
      variation_type: "variation"
      success: false
      
  signature:
    hook_pattern: "question_hook"
    primary_intent: "curiosity"
    audio_style: "direct_address"
    avg_duration_sec: 28.5
    key_elements: ["question", "pause", "reveal"]
```

#### 2.2 Parent 선정 규칙

| 기준 | 조건 | 이유 |
|------|------|------|
| Tier | S 또는 A | 검증된 바이럴 |
| VDG 품질 | merger_quality = gold | 학습 데이터 품질 |
| 변주 수 | kids >= 3 | 통계적 유의성 |
| 댓글 | best_comments >= 5 | 미장센 신호 |

#### 2.3 Kids 선정 규칙

| 기준 | 조건 |
|------|------|
| 유사도 | cluster_signature 매칭 70%+ |
| 성공/실패 | 둘 다 포함 (대조군) |
| 시간 범위 | Parent ±30일 이내 |

#### 2.4 클러스터 10개 목표

| # | 패턴 유형 | Parent | Kids | 상태 |
|---|----------|--------|------|------|
| 1 | 질문형 훅 | 1개 | 5개 | ⬜ |
| 2 | 반전 훅 | 1개 | 4개 | ⬜ |
| 3 | 시각적 펀치 | 1개 | 6개 | ⬜ |
| 4 | 오디오 트렌드 | 1개 | 8개 | ⬜ |
| 5 | 튜토리얼 구조 | 1개 | 5개 | ⬜ |
| 6 | 리뷰 구조 | 1개 | 4개 | ⬜ |
| 7 | 브이로그 구조 | 1개 | 3개 | ⬜ |
| 8 | 제품 언박싱 | 1개 | 5개 | ⬜ |
| 9 | 챌린지 형 | 1개 | 6개 | ⬜ |
| 10 | 댓글 미장센 | 1개 | 4개 | ⬜ |

---

### P3. 주간 DistillRun 운영 (Week 3+)

**목표**: NotebookLM-integrated 달성

#### 3.1 주간 Distill 워크플로우

```
매주 월요일:
┌─────────────────────────────────────┐
│ 1. Cluster 1개 선택                 │
│    └─ 가장 세션 데이터 많은 것      │
├─────────────────────────────────────┤
│ 2. DistillRun 생성                  │
│    ├─ cluster_id                    │
│    ├─ source_refs (VDG IDs)         │
│    └─ prompt_version: "v1"          │
├─────────────────────────────────────┤
│ 3. NotebookLM 투입                  │
│    ├─ Parent VDG                    │
│    ├─ Kids VDGs                     │
│    └─ 성공/실패 라벨                │
├─────────────────────────────────────┤
│ 4. contract_candidates 추출         │
│    ├─ dna_invariants_candidates     │
│    ├─ mutation_slots_candidates     │
│    └─ forbidden_mutations_candidates│
├─────────────────────────────────────┤
│ 5. Pack 생성 (canary 10%)           │
│    ├─ parent_pack_id (계보)         │
│    └─ experiment_id                 │
├─────────────────────────────────────┤
│ 6. 1주일 후: 성과 비교              │
│    ├─ canary vs control             │
│    ├─ 승격 or 롤백 결정             │
│    └─ InvariantCandidate 상태 업데이트│
└─────────────────────────────────────┘
```

#### 3.2 Distill 프롬프트 (NotebookLM용)

```
이 클러스터의 Parent와 Kids를 분석해서:

1. 불변 규칙 (DNA Invariants)
   - 모든 성공 영상에서 유지된 요소
   - 실패 영상에서 깨진 요소

2. 가변 슬롯 (Mutation Slots)
   - 성공 영상 간에도 다른 요소
   - 창의성 발휘 가능 영역

3. 금지 변형 (Forbidden Mutations)
   - 실패 영상의 공통 실수
   - 절대 하면 안 되는 것

JSON 형태로 출력해주세요.
```

---

### P4. google.genai 마이그레이션 (Week 4+)

**전제**: P1-P3 루프가 안정된 후

#### 4.1 마이그레이션 전략

```
1. Wrapper 레이어 단일화
   └─ GeminiClient 인터페이스 고정

2. 백엔드 교체
   └─ google.generativeai → google.genai

3. 테스트
   ├─ VDG 분석 결과 동일성
   └─ AudioCoach 응답 품질
```

#### 4.2 리스크 관리

| 리스크 | 대응 |
|--------|------|
| SDK 단절 | 경고 모니터링, 빠른 대응 |
| API 변경 | Wrapper로 격리 |
| 성능 차이 | A/B 테스트 |

---

## Part 3: Goodhart 방지 + 3축 승격 기준

> **핵심 원칙**: 컴플라이언스만 올리면 게임된다.
> 승격은 **Compliance + Outcome + Robustness** 3축 모두 만족해야 함.

### 3.1 Control Group (10% 필수)

```python
# CoachingIntervention 필드 (이미 추가됨)
assignment: str = "coached"  # "coached" | "control"
holdout_group: bool = False  # 승격 판단에서 제외
```

**운영 정책**:
- 모든 세션의 10%는 `assignment="control"` (코칭 안 함)
- Holdout 5%는 승격 검증용으로 별도 분리
- **Control 없으면 인과 증명 불가**

### 3.2 Negative Evidence 저장

```python
# CoachingOutcome 필드 (이미 추가됨)
is_negative_evidence: bool = False
negative_reason: str  # "compliance_but_poor_outcome", "rule_caused_harm"
```

**목적**: 실패 케이스도 학습에 활용
- "이 규칙 따랐는데 결과가 나빴다" → 승격 차단

### 3.3 3축 승격 기준 (Goodhart 방지)

#### A) Signal → MutationSlot (즉시 반영)
- **조건**: 댓글/VDG에서 신호 포착
- **처리**: Slot으로만 노출 (Lock 없음)

#### B) MutationSlot → InvariantCandidate
| 기준 | 조건 |
|------|------|
| 샘플 | N ≥ 10 세션 |
| Compliance Lift | ≥ +0.15 (vs control) |
| Unknown Rate | ≤ 15% |
| Persona 다양성 | ≥ 2종 |

#### C) Candidate → DNA Invariant
| 기준 | 조건 |
|------|------|
| 샘플 | N ≥ 50 세션 |
| Cluster 다양성 | ≥ 2 클러스터 |
| **Outcome Lift** | ≥ threshold (완주율↑, 업로드율↑) |
| DistillRun 검증 | distill_validated = True |
| Negative Evidence | 동일 signal 실패 < 20% |

**롤백 조건**: Canary에서 outcome_lift 2회 연속 음수 → DNA → Candidate 강등

### 3.4 "완벽" 판정 체크리스트 (10개)

| # | 항목 | DoD | 상태 |
|---|------|-----|------|
| 1 | E2E UX | 카드 → 모드 → 코칭 끊김 없음 | 🔶 |
| 2 | 1-Command | cooldown 강제 | ✅ |
| 3 | rule_evaluated | 개입 없는 구간 포함 기록 | ⬜ |
| 4 | Intervention-Outcome Join | join key 100% | ✅ |
| 5 | Two-stage Outcome | 즉시 + 업로드 | ✅ |
| 6 | **Control Group** | 10% assignment=control | ✅ |
| 7 | **Negative Evidence** | 실패 케이스 저장 | ✅ |
| 8 | **3축 승격** | Compliance + Outcome + Diversity | ✅ |
| 9 | Cluster + Distill | 10개 + 주간 1회 | ⬜ |
| 10 | Canary/Rollback | 실제 발생 | ⬜ |

---

## Part 4: 타임라인

```
Week 1-2: P1 + P2 병행
├─ 킬러 Pack 3개로 세션 50개
├─ 클러스터 10개 수동 생성
└─ 로그 3종 이벤트 검증

Week 3-4: P3 시작
├─ 첫 DistillRun 실행
├─ Canary 배포
└─ 승격/롤백 첫 사례

Week 5+: 자동화 + P4
├─ DistillRun 자동화
├─ google.genai 마이그레이션
└─ "완벽" 선언
```

---

## Part 5: 다음 액션 아이템

### 즉시 (이번 주)

1. **킬러 패턴 3개 선정** (VDG 품질 gold 기준)
2. **테스트 세션 10개** 생성 후 로그 검증
3. **클러스터 첫 3개** 수동 생성

### 다음 주

4. **세션 50개** 달성
5. **클러스터 10개** 완성
6. **첫 DistillRun** 실행

---

## Conclusion

> **"완벽"의 정의**  
> 코드를 안 바꿔도, 데이터가 시스템을 강화하는 상태

**현재**: 아키텍처/스키마 "최상급" ✅  
**다음**: 운영 루프로 "증명" 필요

```
세션 로그 50개 → 클러스터 10개 → 주간 Distill
     ↓                ↓               ↓
   개입 증명       상관 데이터       인과 데이터
               ↘       ↓       ↙
                  🎯 해자 완성
```

**→ "클러스터(상관) + 코칭 로그(개입) + 결과(성과)" = 진짜 인과 데이터 = 해자**
