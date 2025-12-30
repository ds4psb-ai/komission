# 시간축 기반 바이럴 변주 이론 (Temporal Variation Theory)

**작성**: 2025-12-26  
**핵심 통찰**: 바이럴 변주는 시간 경과에 따라 오마쥬 비율이 감소하며, 핵심 로직은 불변/창의성은 가변

---

## 1) 핵심 원리

### 1.1 시간축에 따른 오마쥬 비율 감소

```
┌─────────────────────────────────────────────────────────────────────┐
│  T0 (Parent 등장)                                                   │
│  └── 100% 복제 Kids → 바이럴 성공                                    │
│                                                                     │
│  T1 (1-2주 후)                                                      │
│  └── 100% 복제 → 더 이상 바이럴 X                                    │
│  └── 95% 오마쥬 + 5% 창의성 Kids → 바이럴 성공                        │
│                                                                     │
│  T2 (3-4주 후)                                                      │
│  └── 95% 오마쥬 → 바이럴 감소                                        │
│  └── 90% 오마쥬 + 10% 창의성 Kids → 바이럴 성공                       │
│                                                                     │
│  T3 (5-6주 후)                                                      │
│  └── 85% 오마쥬 + 15% 창의성 → 바이럴 성공                            │
│  └── ...                                                            │
└─────────────────────────────────────────────────────────────────────┘
```

> **결론**: 플랫폼 알고리즘은 "신선함"을 선호하므로, 동일 콘텐츠는 시간이 지나면 노출 감소.
> 창의성 비율을 점진적으로 높여야 지속적 바이럴 가능.

---

## 2) 불변 요소 vs 가변 요소

### 2.1 불변 요소 (100% 유지 필수)

핵심 바이럴 로직은 **절대 변경 불가**:

| 요소 | 설명 | 예시 |
|------|------|------|
| **Hook 구조** | 첫 0.5-1초 시선 고정 패턴 | 표정 리액션, 충격적 비주얼, 질문 |
| **페이싱** | 컷 간격, 텐션 곡선 | 0.3초 컷, 중간 클라이맥스 |
| **핵심 전환점** | 시청자 이탈 방지 "킥" 위치 | 3초/7초/12초 타이밍 |
| **오디오 구조** | BGM 드롭, 효과음 타이밍 | 비트 드롭에 맞춘 액션 |
| **감정 페이오프** | 마지막 만족감 | 웃음, 놀람, 감동 |

> ⚠️ **핵심 로직을 변경하면 바이럴 확률 급감**

### 2.2 가변 요소 (창의성 추가 영역)

| 요소 | 창의성 비율별 예시 |
|------|-------------------|
| **소재 변경** | 음식→패션, 일상→직장, 한국→해외 |
| **인물 교체** | 1인→커플, 남자→여자, 성인→어린이 |
| **반전 추가** | 예상과 다른 결말, 트위스트 |
| **중간 킥** | 이탈 방지용 서브 훅 삽입 (5초/10초 위치) |
| **로컬라이징** | 문화권별 유머, 언어, 트렌드 |
| **포맷 변주** | POV→리액션, 튜토리얼→챌린지 |

---

## 3) Depth별 변주 전략

| Depth | 오마쥬 비율 | 창의성 비율 | 변주 가이드 |
|-------|------------|------------|-------------|
| **Depth 1** | 95-100% | 0-5% | 소재만 변경 (음식→뷰티) |
| **Depth 2** | 90-95% | 5-10% | 인물 변경 + 미세 반전 |
| **Depth 3** | 85-90% | 10-15% | 중간 킥 추가 + 로컬라이징 |
| **Depth 4+** | 80-85% | 15-20% | 포맷 변주 (새 구조 실험) |

> 📌 **Depth가 깊어질수록 창의성 비율 증가, 단 핵심 로직은 100% 유지**

---

## 4) 데이터 모델 반영

### 4.1 vdg_variants 확장 필드 (제안)

```sql
ALTER TABLE vdg_variants ADD COLUMN homage_ratio FLOAT; -- 0.8 ~ 1.0
ALTER TABLE vdg_variants ADD COLUMN creativity_elements JSONB;
-- 예: {"subject_change": true, "mid_kick": true, "twist_ending": false}

ALTER TABLE vdg_variants ADD COLUMN invariant_preserved BOOLEAN; -- 핵심 로직 유지 여부
ALTER TABLE vdg_variants ADD COLUMN invariant_check JSONB;
-- 예: {"hook": true, "pacing": true, "payoff": true, "audio": false}
```

### 4.2 Evidence 스코어링 반영

Pattern Lift 계산 시 `invariant_preserved = false`인 변주는 **제외**:

```python
if not variant.invariant_preserved:
    continue  # 핵심 로직 이탈 → 분석 대상에서 제외

adjusted_lift = base_lift * (1 - (1 - variant.homage_ratio) * penalty_factor)
```

### 4.3 Temporal Diffusion 필드 (연구 기반 추가 제안)

```sql
ALTER TABLE vdg_variants ADD COLUMN temporal_phase TEXT; -- T0/T1/T2/T3
ALTER TABLE vdg_variants ADD COLUMN variant_age_days INT;
ALTER TABLE vdg_variants ADD COLUMN novelty_decay_score FLOAT; -- 0~1 (낮을수록 신선도 하락)
ALTER TABLE vdg_variants ADD COLUMN burstiness_index FLOAT; -- 댓글/조회 급등도
```

> **의도**: 시간 지연, 집중도(주의 경쟁), 버스트 패턴을 정량화해 변주 비율을 자동 조정

---

## 5) 템플릿 가이드 반영

### 5.1 Shotlist + 불변/가변 표시

```yaml
template:
  parent_id: "abc-123"
  invariant:  # ⚠️ 절대 변경 불가
    - hook: "첫 0.5초 표정 리액션"
    - pacing: "0.3초 컷편집"
    - payoff: "마지막 손동작으로 마무리"
  variable:   # ✅ 창의성 추가 가능
    - subject: "음식 → 패션 변경 가능"
    - mid_kick: "7초에 서브 훅 추가"
    - character: "성별/연령 변경 가능"
```

### 5.2 Creator 가이드 UI

```
┌─────────────────────────────────────────┐
│ 🔒 이건 꼭 지켜주세요 (불변)            │
│ • 첫 0.5초 표정 리액션                  │
│ • 0.3초 컷편집 유지                     │
│ • 마지막 손동작 마무리                  │
├─────────────────────────────────────────┤
│ ✨ 여기서 창의력 발휘! (가변)           │
│ • 소재: 음식→패션 변경 OK              │
│ • 중간 킥: 7초에 서브 훅 추가 추천      │
│ • 반전: 예상 뒤집는 결말 시도           │
└─────────────────────────────────────────┘
```

---

## 6) 운영 체크리스트

### 6.1 Parent 선정 시

- [ ] 핵심 바이럴 로직이 명확히 추출 가능한가?
- [ ] Hook/Pacing/Payoff가 분리 가능한가?
- [ ] 변주 가능한 가변 요소가 3개 이상인가?

### 6.2 Depth 실험 설계 시

- [ ] 불변 요소를 명시적으로 고정했는가?
- [ ] 해당 Depth에 맞는 오마쥬 비율을 지정했는가?
- [ ] 창의성 요소(소재/인물/반전 등)를 1-2개로 제한했는가?

### 6.3 Evidence 분석 시

- [ ] 불변 요소 이탈 변주는 분석에서 제외했는가?
- [ ] 시간축(T0~Tn)에 따른 성과 변화를 추적했는가?
- [ ] 다음 Depth의 창의성 비율을 높일지 판단했는가?

---

## 7) 연구 근거(웹 리서치 요약)

### 7.1 핵심 근거
- **시간 가변 파라미터**가 확산 패턴 예측에 중요(temporal dynamics, time‑varying parameters)  
  → 확산 속도/형태가 시간에 따라 달라진다는 점을 모델링해야 함.  
  Ref: arXiv 1302.5235 (Guille et al., 2013)  
- **한정된 주의력 경쟁**이 밈 수명과 성과를 좌우  
  → 동일 포맷/오마쥬는 시간이 지날수록 경쟁 심화로 성과 하락.  
  Ref: Weng et al., Scientific Reports 2012 (limited attention, meme competition)  
- **사용자 행동의 버스트/긴 꼬리 분포**  
  → 조회/댓글 급등 구간이 짧고 비대칭적으로 발생.  
  Ref: Barabási 2005 (bursty dynamics, heavy tails)  
- **시간 지연(Delay)과 확산 도달 범위의 관계**  
  → peak speed time이 커버리지 예측에 핵심.  
  Ref: MDPI Applied Sciences 2025 (diffusion delay mechanisms)

### 7.2 왜 Temporal Variation Theory와 일치하는가
- **시간이 지날수록 동일 포맷의 경쟁이 증가** → 오마쥬 비율 감소 필요  
- **버스트 타이밍이 핵심 신호** → T0/T1/T2 구간별 변주 전략 필요  
- **확산 지연이 성과를 좌우** → 동일 변주도 시간대/주기별 성과가 달라짐

---

## 8) Komission 적용 인사이트 (파이프라인 전반)

### 8.1 영상해석 (VDG)
- **Temporal Phase 자동 분류**: parent_first_seen_at 기준으로 T0/T1/T2 구간 부여  
- **Invariant Fingerprint**: hook microbeats + pacing + audio drop 타이밍을 해시로 고정  
- **Variant Divergence**: 가변 요소(소재/인물/반전/포맷)를 벡터화해 `creativity_elements`에 기록

### 8.2 DB화/클러스터링
- **cluster_id에 시간축 라벨 추가**: `cluster_id + temporal_phase`  
- **novelty_decay_score** 도입: 동일 패턴 반복 시 하향, 일정 시간이 지나면 리셋  
- **burstiness_index**: 댓글/조회 급등 구간 밀도 측정

### 8.3 NotebookLM 활용
- **Notebook 묶음 기준 = (pattern + temporal_phase)**  
  → 같은 패턴이라도 T0/T2는 별도 노트북으로 분리  
- **노트북 히스토리 카드**: “이 패턴은 T2에서 성과가 좋음” 같은 히스토리 요약

### 8.4 사용자 경험 (UX)
- **창의성 가이던스 슬라이더**: 현재 Phase 기준 자동 프리셋(95→90→85%)  
- **불변/가변 강조 UI**: T가 내려갈수록 가변 영역 비중 증가 표시  
- **타이밍 알림**: “이 패턴은 최근 3주 반복됨 → 변주 비율 +10% 권장”

### 8.5 강화학습/정책
- **Temporal Context Bandit**: 상태에 `phase`, `variant_age_days`, `burstiness_index` 포함  
- **Reward = lift × novelty_decay_score**  
  → 동일 패턴 반복만으론 보상이 줄어드는 구조

---

## 9) 바로 반영 가능한 개선 포인트

1. **VDG 결과에 temporal_phase 계산 로직 추가**  
2. **Evidence Runner에 novelty_decay_score 반영**  
3. **NotebookLM Source Pack 생성 시 phase별 묶음 추가**

---

## 10) 관련 문서

- [01_VDG_SYSTEM.md](01_VDG_SYSTEM.md) - 기본 VDG 데이터 모델
- [14_PDR.md](14_PDR.md) - 제품 요구사항
- [03_IMPLEMENTATION_ROADMAP.md](03_IMPLEMENTATION_ROADMAP.md) - 구현 로드맵

---

## 11) 참고 링크 (웹)
- https://arxiv.org/abs/1302.5235  
- https://www.nature.com/articles/srep00335  
- https://arxiv.org/abs/cond-mat/0505371  
- https://www.mdpi.com/2076-3417/15/11/6092
