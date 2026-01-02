# 코미션 2026 병렬 개발 전략

> **문서 생성**: 2026-01-02  
> **최종 수정**: 2026-01-02 (모바일 앱 하드닝 완료)  
> **핵심 결정**: 모바일 4K 촬영 앱 + 웹앱 고도화 병렬 진행

---

## Executive Summary

```
                    ┌─────────────────────────────┐
                    │      SHARED BACKEND         │
                    │   FastAPI + PostgreSQL      │
                    │   (변경 최소화)              │
                    └────────────┬────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌─────────────────────┐                   ┌─────────────────────┐
│   TRACK A: MOBILE   │                   │   TRACK B: WEB      │
├─────────────────────┤                   ├─────────────────────┤
│ ✅ 4K 촬영 (완료)    │                   │ • 코칭 품질 향상     │
│ ✅ H.265 코덱       │                   │ • 체험단 고도화      │
│ ✅ 코칭 오버레이     │                   │ • 캠페인 시스템      │
│ ✅ 음성/텍스트 토글  │                   │                     │
├─────────────────────┤                   ├─────────────────────┤
│ 담당: Claude         │                   │ 담당: 새 개발자      │
│ 폴더: /mobile        │                   │ 폴더: /frontend      │
│ 상태: ✅ Week 1 완료  │                   │ 기간: 지속적         │
└─────────────────────┘                   └─────────────────────┘
```

---

## 모바일 앱 구현 완료 상태

### ✅ 완료된 기능 (Phase 1 + Phase 2)

| 기능 | 상태 | 파일 |
|------|------|------|
| **4K 촬영** | ✅ | `app/camera.tsx` |
| **H.265 (HEVC)** | ✅ | `src/config/recordingConfig.ts` |
| **프레임 레이트 안정화** | ✅ | `src/hooks/useCameraFormat.ts` |
| **배터리/네트워크 적응** | ✅ | `src/hooks/useDeviceStatus.ts` |
| **H.264 스트리밍 최적화** | ✅ | `src/services/videoStreamService.ts` |
| **적응형 비트레이트** | ✅ | `src/services/videoStreamService.ts` |
| **음성 코칭 토글** | ✅ | `src/components/CoachingOverlay.tsx` |
| **텍스트 코칭 토글** | ✅ | `src/components/CoachingOverlay.tsx` |
| **DB 세션 저장** | ✅ | `src/hooks/useSessionPersistence.ts` |

### 📁 실제 폴더 구조

```
/mobile
├── app.json                          # Expo 설정 (카메라/마이크 권한)
├── package.json                      # expo-battery, expo-network 등 포함
├── tsconfig.json
├── .gitignore
├── README.md
│
├── app/                              # expo-router 라우트
│   ├── _layout.tsx                   # 루트 레이아웃
│   ├── index.tsx                     # 홈 화면
│   └── camera.tsx                    # ⭐ 4K 촬영 화면 (하드닝 완료)
│
├── src/
│   ├── config/
│   │   └── recordingConfig.ts        # H.265/H.264 코덱 설정
│   │
│   ├── hooks/
│   │   ├── useCameraFormat.ts        # 프레임 레이트 안정화
│   │   ├── useCoachingWebSocket.ts   # ⭐ Phase 2 스트리밍 최적화
│   │   ├── useDeviceStatus.ts        # 배터리/네트워크/저장공간
│   │   └── useSessionPersistence.ts  # DB 연동 (RL용)
│   │
│   ├── services/
│   │   └── videoStreamService.ts     # H.264 스트림 + 적응형 비트레이트
│   │
│   └── components/
│       ├── CoachingOverlay.tsx       # ⭐ 음성/텍스트 토글, 확장 슬롯
│       ├── RecordButton.tsx
│       ├── QualityBadge.tsx
│       └── DeviceStatusBar.tsx
│
└── assets/
```

---

## 핵심 기술 명세 (하드닝 완료)

### 4K 촬영 + H.265

```typescript
// recordingConfig.ts
const BITRATE_MAP = {
  '4k': { h265: 15_000_000, h264: 30_000_000 },
  '1080p': { h265: 6_000_000, h264: 12_000_000 },
};

// 자동 품질 선택
export function getOptimalRecordingConfig(quality, preferH265) {
  const supportsH265 = isH265Supported();
  return { quality, codec: supportsH265 ? 'h265' : 'h264', ... };
}
```

### Phase 2: H.264 스트리밍 최적화

```typescript
// videoStreamService.ts
export class FrameProcessor {
  throttler: FrameThrottler;       // 2fps 제한 (코칭용)
  bitrateController: AdaptiveBitrateController;  // 네트워크 적응
  
  async processFrame(frameBase64, width, height) {
    if (!this.throttler.shouldSendFrame()) return null;
    return { data: frameBase64, codec: 'h264', ... };
  }
}
```

### 음성/텍스트 토글 UI

```typescript
// CoachingOverlay.tsx
<View style={styles.settingsPanel}>
  <Switch value={voiceEnabled} onValueChange={onVoiceToggle} />
  <Switch value={textEnabled} onValueChange={onTextToggle} />
</View>
```

### 확장 슬롯 (Phase 2+ 준비)

```typescript
interface CoachingOverlayProps {
  // 구현됨
  voiceEnabled, textEnabled, onVoiceToggle, onTextToggle
  
  // 확장 슬롯 (UI만 준비, 로직 연결 대기)
  compositionGuide?: { type: 'rule_of_thirds' | 'golden_ratio', enabled: boolean }
  lightingRecommendation?: { currentBrightness: 'too_dark' | 'optimal' | 'too_bright' }
  miseEnSceneHint?: string  // 미장센 추천
}
```

### DB/RL 통합

```typescript
// useSessionPersistence.ts
const { createSession, logIntervention, endSession } = useSessionPersistence();

// 세션 생성 → 개입 로깅 → 결과 저장 → RL 피드백 루프
await createSession({ mode: 'homage', patternId: 'xxx' });
await logIntervention({ ruleId: 'hook_2s', tSec: 1.5, message: '...' });
await endSession({ durationSec: 60, complianceRate: 0.85 });
```

---

## 트랙 B: 웹앱 고도화 상세

### Phase 1: 코칭 품질 향상

**목표**: CV 메트릭 기반 실시간 피드백

| 메트릭 | 코칭 메시지 |
|--------|------------|
| center_offset_xy | "피사체가 왼쪽에 있어요. 중앙으로 맞춰주세요!" |
| brightness_ratio | "조명이 어두워요! 밝은 곳으로 이동해주세요" |
| blur_score | "화면이 흔들려요! 카메라를 안정시켜주세요" |

**구현 위치**:
- `/backend/app/services/frame_analyzer.py`
- `/backend/app/routers/coaching_ws.py`

### Phase 2: 체험단 고도화

**목표**: 캠페인 → 신청 → 선발 → 제출 → 보상 전체 플로우

**새 컴포넌트**:
- `CampaignCreator.tsx` - 캠페인 생성
- `CampaignApply.tsx` - 크리에이터 신청
- `CampaignReview.tsx` - 영상 검수

---

## 백엔드 통합 현황

### 기존 모델 활용

```python
# models.py
class CoachingSession(Base):       # L1745 - 세션 저장
class CoachingIntervention(Base):  # L1792 - 개입 이벤트
class CoachingOutcome(Base):       # L1836 - 준수 결과

# 모바일에서 호출하는 API
POST /api/v1/coaching/sessions
POST /api/v1/coaching/sessions/{id}/events/intervention
POST /api/v1/coaching/sessions/{id}/events/outcome
POST /api/v1/coaching/sessions/{id}/end
```

### WebSocket 개선 (Phase 2)

```python
# coaching_ws.py L231-237
elif msg_type == "ping":
    await manager.send_message(session_id, {
        "type": "pong",
        "client_t": message.get("t"),  # RTT 측정용
    })

# coaching_ws.py L1001-1012
if t_ms:
    await manager.send_message(session_id, {
        "type": "frame_ack",
        "frame_t": t_ms,
        "codec": codec,
    })
```

### MCP 활용

```
/backend/app/mcp/
├── tools/       # smart_pattern_analysis, ai_batch_analysis 등
├── resources/   # 데이터 리소스
├── prompts/     # 프롬프트 템플릿
└── server.py    # MCP 서버
```

---

## 일정 현황

| Week | 모바일 (Track A) | 웹앱 (Track B) |
|------|------------------|----------------|
| Week 1 | ✅ Expo 프로젝트 초기화<br>✅ vision-camera 설정<br>✅ 4K 촬영 구현<br>✅ H.265/H.264 코덱<br>✅ 프레임 레이트 안정화<br>✅ Phase 2 스트리밍<br>✅ 음성/텍스트 토글<br>✅ DB 연동 | (새 개발자 온보딩 대기) |
| Week 2 | ⬜ 딥링크 연결<br>⬜ TestFlight 등록<br>⬜ 내부 테스트 | ⬜ CV 메트릭 통합<br>⬜ 코칭 메시지 매핑 |
| Week 3 | ⬜ 앱스토어 제출<br>⬜ 구도/빛 추천 UI | ⬜ 체험단 API<br>⬜ 캠페인 CRUD |

---

## 다음 단계

### 모바일 (즉시)

```bash
cd mobile && npm install
npx expo prebuild --platform ios
npx expo run:ios --device
```

### 웹앱 (새 개발자)

1. `docs/22_DEVELOPER_ONBOARDING.md` 읽기
2. `frontend/` 환경 세팅
3. CV 메트릭 기반 코칭 개선 시작

---

## 관련 문서

- [개발자 온보딩](docs/22_DEVELOPER_ONBOARDING.md)
- [VDG 2-Pass 프로토콜](docs/vdg_v4_2pass_protocol.md)
- [기존 로드맵](docs/ROADMAP_MVP_TO_PERFECT.md)
- [MCP 설정](docs/MCP_CLAUDE_DESKTOP_SETUP.md)
