# Proof Playbook v1.0

**작성일**: 2025-12-31  
**목적**: 오디오 코칭 효과 증명을 위한 3패턴 집중 전략

---

## 1. 증명 대상: TOP 3 패턴

| 순위 | pattern_id | DNA (불변) | 필요 메트릭 | 코칭 원라이너 |
|------|-----------|-----------|------------|-------------|
| **1** | `hook_start_within_2s_v1` | 0~2초 내 발화/액션 시작 | Semantic ASR | "지금 바로 치고 들어가요" |
| **2** | `hook_center_anchor_v1` | 훅 구간 중앙 이탈 금지 | `cmp.center_offset_xy.v1` | "중앙에 박아!" |
| **3** | `exposure_floor_v1` | 밝기 바닥선 유지 | `lit.brightness_ratio.v1` | "조명 켜요" |

### 선정 기준
- **Observability**: 저비용 측정 가능 (Semantic-only or 프레임 10장)
- **Interventionability**: 한 문장 코칭으로 행동 변화
- **Generalizability**: 2+ 클러스터에서 재현

---

## 2. 세션 로그 최소 스키마

### Session (한 줄)
```python
@dataclass
class SessionLog:
    session_id: str
    user_id_hash: str        # 개인정보 X
    mode: Literal["homage", "mutation", "campaign"]
    pattern_id: str
    pack_id: str
    started_at: datetime
    ended_at: datetime
```

### Intervention Event
```python
@dataclass
class InterventionEvent:
    t_sec: float
    rule_id: str
    ap_id: str               # ActionPoint
    evidence_id: str         # 프레임/오디오 증거
    coach_line_id: str       # 코칭 문장 ID
```

### Outcome
```python
@dataclass
class OutcomeEvent:
    t_sec: float
    rule_id: str
    compliance: Optional[bool]
    compliance_unknown_reason: Optional[str]  # occluded/out_of_frame/no_audio/ambiguous
```

### Upload Outcome Proxy
```python
upload_outcome_proxy: str  # uploaded/early_views_bucket/self_rating
```

---

## 3. 승격 기준 (Goodhart 방지)

### 승격 = "잘 지켰다"가 아니라:
> **"지키게 만들었고 → 성과가 올랐고 → 다른 클러스터에서도 재현됐다"**

### 2단계 Lift
1. `compliance_lift`: 코칭 → 행동 변화
2. `outcome_lift`: 행동 변화 → 업로드 성과 개선

### 필수 조건
- [ ] 최소 N=2 클러스터에서 재현
- [ ] 대조군 (코칭 OFF 세션) 대비 lift 존재
- [ ] Canary 10%에서 유지 → 롤백 게이트

---

## 4. 후보 10개 전체 (참조)

| # | pattern_id | 비용 | 주요 metric |
|---|-----------|------|------------|
| 1 | `hook_start_within_2s_v1` | Semantic-only | ASR 첫발화 |
| 2 | `hook_center_anchor_v1` | Visual cheap | center_offset |
| 3 | `no_shake_stability_v1` | Visual cheap | stability_score |
| 4 | `exposure_floor_v1` | Visual cheapest | brightness_ratio |
| 5 | `shot_distance_sweetspot_v1` | Visual cheap | subject_area_ratio |
| 6 | `headroom_discipline_v1` | Visual cheap | headroom_ratio |
| 7 | `early_caption_presence_v1` | Semantic-only | OCR content |
| 8 | `caption_safe_area_clear_v1` | Visual cheap | bbox 교차율 |
| 9 | `product_reveal_visibility_v1` | Visual medium | visibility_ratio |
| 10 | `transition_no_accidental_reframe_v1` | Visual cheap | composition_change |

---

## 5. 다음 단계

1. **세션 로그 테이블 생성** (위 스키마)
2. **3패턴 룰셋 구현** (DirectorPack에 연동)
3. **Canary 10% 실험 설계**
4. **Lift 측정 파이프라인 구축**
