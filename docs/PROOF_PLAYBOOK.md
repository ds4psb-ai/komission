# Proof Playbook v1.1

**작성일**: 2025-12-31  
**최종 수정**: 2026-01-02 (모바일 앱 연동 추가)  
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

## 2. 플랫폼별 데이터 수집

### 모바일 앱 (`/mobile`) ⭐ NEW

```typescript
// useSessionPersistence.ts
const { createSession, logIntervention, logOutcome, endSession } = useSessionPersistence();

// 세션 생성
await createSession({
  mode: 'homage',
  patternId: 'hook_start_within_2s_v1',
  packId: 'pack_xxx',
});

// 개입 로깅
await logIntervention({
  ruleId: 'hook_2s',
  tSec: 1.5,
  message: '지금 바로 치고 들어가요',
  priority: 'high',
});

// 결과 로깅
await logOutcome({
  interventionId: 'int_xxx',
  ruleId: 'hook_2s',
  tSec: 3.0,
  result: 'complied',
});
```

### 웹앱 (`/frontend`)

```typescript
// useCoachingWebSocket.ts
const { feedback, sendControl, sendFrame } = useCoachingWebSocket(sessionId);
```

---

## 3. 세션 로그 스키마

### DB 모델 (`models.py`)

```python
class CoachingSession(Base):
    __tablename__ = "coaching_sessions"
    session_id: str           # unique
    user_id_hash: str         # 개인정보 X
    mode: CoachingMode        # homage | mutation | campaign
    pattern_id: str
    pack_id: str
    assignment: CoachingAssignment  # coached | control (10% 대조군)
    holdout_group: bool       # 5% 홀드아웃
    device_type: str          # ios | android | web ← NEW

class CoachingIntervention(Base):
    __tablename__ = "coaching_interventions"
    t_sec: float
    rule_id: str
    ap_id: str                # ActionPoint
    evidence_id: str          # 프레임/오디오 증거
    coach_line_id: str        # 코칭 문장 ID
    message: str              # 실제 코칭 메시지

class CoachingOutcome(Base):
    __tablename__ = "coaching_outcomes"
    t_sec: float
    rule_id: str
    intervention_id: str      # 어떤 개입에 대한 결과인지
    result: ComplianceResult  # complied | violated | unknown
    evidence_type: str        # frame | audio | text
    compliance_unknown_reason: str  # occluded/out_of_frame/no_audio/ambiguous
```

---

## 4. WebSocket 프로토콜 (Phase 2)

### 클라이언트 → 서버

```json
{
  "type": "video_frame",
  "frame_b64": "...",
  "t_sec": 1.5,
  "t_ms": 1704200000000,
  "codec": "h264",
  "quality_hint": "high"
}
```

### 서버 → 클라이언트

```json
// 피드백
{
  "type": "feedback",
  "message": "지금 바로 치고 들어가요",
  "audio_b64": "...",
  "rule_id": "hook_start_within_2s_v1",
  "priority": "high"
}

// 프레임 ACK (RTT 측정)
{
  "type": "frame_ack",
  "frame_t": 1704200000000,
  "codec": "h264"
}
```

---

## 5. 승격 기준 (Goodhart 방지)

### 승격 = "잘 지켰다"가 아니라:
> **"지키게 만들었고 → 성과가 올랐고 → 다른 클러스터에서도 재현됐다"**

### 2단계 Lift
1. `compliance_lift`: 코칭 → 행동 변화
2. `outcome_lift`: 행동 변화 → 업로드 성과 개선

### 필수 조건
- [x] 코칭/대조군 10% 자동 할당 (`assignment` 필드)
- [ ] 최소 N=2 클러스터에서 재현
- [ ] 대조군 (코칭 OFF 세션) 대비 lift 존재
- [ ] Canary 10%에서 유지 → 롤백 게이트

---

## 6. 모바일 앱 특수 고려사항 ⭐ NEW

### 음성/텍스트 토글
```typescript
// CoachingOverlay.tsx
interface CoachingOverlayProps {
  voiceEnabled: boolean;   // 음성 코칭 ON/OFF
  textEnabled: boolean;    // 텍스트 코칭 ON/OFF
  onVoiceToggle: (enabled: boolean) => void;
  onTextToggle: (enabled: boolean) => void;
}
```

### 비방해 UI
- 피드백 위치: 하단 중앙 (촬영 영역 최소 간섭)
- 자동 fade: 4초 후 70% 투명도
- 글래스모피즘 디자인

### 확장 슬롯 (Phase 2+)
```typescript
compositionGuide?: { type: 'rule_of_thirds', enabled: boolean }
lightingRecommendation?: { currentBrightness: 'too_dark' | 'optimal' }
miseEnSceneHint?: string
```

---

## 7. 후보 10개 전체 (참조)

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

## 8. 현재 상태 (2026-01-02)

| 항목 | 상태 | 비고 |
|------|------|------|
| 세션 로그 테이블 | ✅ 완료 | `coaching_sessions`, `interventions`, `outcomes` |
| 3패턴 룰셋 구현 | ✅ 완료 | DirectorPack 연동 |
| 모바일 앱 연동 | ✅ 완료 | `useSessionPersistence.ts` |
| 웹앱 연동 | ✅ 완료 | `CoachingSession.tsx` |
| Canary 10% 실험 | 🟡 대기 | 베타 테스트 후 |
| Lift 측정 파이프라인 | 🟡 대기 | 데이터 축적 필요 |

---

## 9. 다음 단계

1. ✅ **세션 로그 테이블 생성** → 완료
2. ✅ **3패턴 룰셋 구현** → 완료
3. ⬜ **Canary 10% 실험 설계** → 베타 테스트 시작 후
4. ⬜ **Lift 측정 파이프라인 구축** → 데이터 축적 후
