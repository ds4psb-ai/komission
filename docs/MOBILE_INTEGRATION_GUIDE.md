# 📱 모바일 앱 통합 가이드: 코칭 시스템 Phase 1-5+

**작성일**: 2026-01-03  
**대상**: 모바일 앱 개발자  
**목적**: 실시간 코칭 시스템 고도화 기능 완전 통합

---

## 📋 목차

1. [개요](#1-개요)
2. [WebSocket 연결](#2-websocket-연결)
3. [Phase 1: 출력 모드 + 페르소나](#3-phase-1-출력-모드--페르소나)
4. [Phase 2: VDG 데이터 활용](#4-phase-2-vdg-데이터-활용)
5. [Phase 3: 적응형 코칭 (LLM)](#5-phase-3-적응형-코칭-llm)
6. [Phase 4: 페르소나별 TTS](#6-phase-4-페르소나별-tts)
7. [Phase 5+: 자동학습 시스템](#7-phase-5-자동학습-시스템)
8. [메시지 타입 레퍼런스](#8-메시지-타입-레퍼런스)

---

## 1. 개요

### 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     모바일 앱                                │
│  ┌─────────┐  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
│  │ 출력모드 │  │  페르소나  │  │ 적응형코칭 │  │ 자동학습  │  │
│  │ 선택 UI │  │  선택 UI  │  │  피드백 UI │  │  통계 UI  │  │
│  └────┬────┘  └─────┬─────┘  └─────┬──────┘  └─────┬─────┘  │
│       └───────────┬─┴──────────────┴───────────────┘        │
│                   ↓                                          │
│            WebSocket 연결                                    │
└───────────────────┬─────────────────────────────────────────┘
                    ↓
┌───────────────────┴─────────────────────────────────────────┐
│                  Backend (coaching_ws.py)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ AudioCoach│  │ Adaptive │  │ TTS      │  │ Advanced    │ │
│  │           │  │ Coaching │  │ Personas │  │ Analyzer    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. WebSocket 연결

### 연결 URL

```
wss://[서버주소]/ws/coaching/{session_id}
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|----------|------|------|------|--------|
| `output_mode` | string | ✅ | 출력 모드 | `"graphic"` |
| `persona` | string | ✅ | 코칭 페르소나 | `"chill_guide"` |
| `tier` | string | ✅ | 코칭 티어 | `"pro"` |

### 연결 예시 (Swift)

```swift
let sessionId = UUID().uuidString
let wsURL = URL(string: "wss://api.komission.app/ws/coaching/\(sessionId)?output_mode=graphic&persona=chill_guide&tier=pro")!
let webSocket = URLSession.shared.webSocketTask(with: wsURL)
webSocket.resume()
```

### 연결 예시 (Kotlin)

```kotlin
val sessionId = UUID.randomUUID().toString()
val wsUrl = "wss://api.komission.app/ws/coaching/$sessionId?output_mode=graphic&persona=chill_guide&tier=pro"
val client = OkHttpClient()
val request = Request.Builder().url(wsUrl).build()
val webSocket = client.newWebSocket(request, listener)
```

---

## 3. Phase 1: 출력 모드 + 페르소나

### 출력 모드 (Output Mode)

| 모드 | 키 | 설명 | 사용 케이스 |
|------|-----|------|-------------|
| 그래픽 | `graphic` | 화면 오버레이 (무음) | 🔇 촬영자 = 피사체 (기본) |
| 텍스트 | `text` | 자막 형태 | 🔇 조용한 환경 |
| 음성 | `audio` | TTS 코칭 | 🔊 촬영자 ≠ 피사체 |
| 그래픽+음성 | `graphic_audio` | 둘 다 | 🔊 풀 코칭 |

### 페르소나 (Persona)

| 페르소나 | 키 | 설명 | 톤 |
|----------|-----|------|-----|
| 빡센 디렉터 | `drill_sergeant` | 날카로운 촬영 감독 🎬 | 빠르고 단호 |
| 찐친 | `bestie` | 옆자리 친구 ✨ | 다정하고 자연스러움 |
| 릴렉스 가이드 | `chill_guide` | ASMR 급 차분함 🧘 | 느리고 여유 (기본) |
| 하이퍼 부스터 | `hype_coach` | 텐션 200% ⚡ | 빠르고 에너지 넘침 |

### UI 구현 예시

```swift
// iOS - 모드/페르소나 선택 UI
struct CoachingModeSelector: View {
    @Binding var outputMode: String
    @Binding var persona: String
    
    let outputModes = [
        ("graphic", "그래픽", "화면 오버레이"),
        ("text", "텍스트", "조용한 자막"),
        ("audio", "음성", "TTS 코칭"),
        ("graphic_audio", "그래픽+음성", "풀 코칭")
    ]
    
    let personas = [
        ("drill_sergeant", "빡센 디렉터", "🎬"),
        ("bestie", "찐친", "✨"),
        ("chill_guide", "릴렉스 가이드", "🧘"),
        ("hype_coach", "하이퍼 부스터", "⚡")
    ]
}
```

---

## 4. Phase 2: VDG 데이터 활용

### 수신 메시지: `vdg_coaching_data`

촬영 시작(start action) 직후 전송됨

```json
{
  "type": "vdg_coaching_data",
  "shotlist_sequence": [
    {"shot_id": 1, "description": "후킹 샷", "duration_sec": 3},
    {"shot_id": 2, "description": "메인 컨텐츠", "duration_sec": 10}
  ],
  "kick_timings": [
    {"type": "punch", "t_ms": 2000, "description": "첫 반전"},
    {"type": "end", "t_ms": 15000, "description": "마무리"}
  ],
  "mise_en_scene_guides": [
    {"element": "outfit_color", "suggestion": "노란색 계열 권장"}
  ],
  "timestamp": "2026-01-03T01:00:00Z"
}
```

### UI 구현

```swift
// iOS - VDG 데이터 표시
struct ShotlistOverlay: View {
    let sequence: [ShotGuide]
    @State var currentShot: Int = 0
    
    var body: some View {
        VStack {
            // 현재 샷 표시
            Text("📍 \(sequence[currentShot].description)")
            
            // 타임라인 바
            ProgressView(value: currentTime / totalDuration)
        }
    }
}
```

---

## 5. Phase 3: 적응형 코칭 (LLM)

### 사용자 피드백 전송

사용자가 "이거 안 돼요" 등 피드백을 보낼 때:

```json
// 전송 (앱 → 서버)
{
  "type": "user_feedback",
  "text": "역광이 안 돼요"
}
```

### 적응형 응답 수신

```json
// 수신 (서버 → 앱)
{
  "type": "adaptive_response",
  "accepted": false,
  "message": "'역광 필수'는 바이럴 핵심이에요.",
  "alternative": "측면광이나 자연광도 좋아요!",
  "affected_rule_id": "lighting_backlight",
  "reason": "priority=critical",
  "coaching_adjustment": null,
  "timestamp": "2026-01-03T01:00:00Z"
}
```

### 응답 처리 로직

```swift
// iOS - 적응형 응답 처리
func handleAdaptiveResponse(_ response: AdaptiveResponse) {
    if response.accepted {
        // ✅ 피드백 수락됨
        showSuccessToast(response.message)
        
        // coaching_adjustment가 있으면 코칭 방식 조정
        if let adjustment = response.coachingAdjustment {
            updateCoachingBehavior(adjustment)
        }
    } else {
        // ❌ 거절됨 - 대안 제시
        showAlternativeDialog(
            message: response.message,
            alternative: response.alternative
        )
    }
}
```

### UI 구현 (피드백 입력)

```swift
// 음성 또는 텍스트로 피드백 전송
struct FeedbackInput: View {
    @Binding var feedbackText: String
    var onSend: (String) -> Void
    
    var body: some View {
        HStack {
            TextField("피드백 입력...", text: $feedbackText)
            
            Button("보내기") {
                onSend(feedbackText)
                feedbackText = ""
            }
            
            // 음성 입력 버튼
            VoiceInputButton { transcript in
                onSend(transcript)
            }
        }
    }
}
```

---

## 6. Phase 4: 페르소나별 TTS

### 오디오 피드백 수신

`output_mode`가 `audio` 또는 `graphic_audio`인 경우:

```json
{
  "type": "audio_feedback",
  "text": "중앙에 맞춰봐요!",
  "audio": "base64_encoded_mp3_data...",
  "persona": "chill_guide",
  "source": "gtts_fallback",
  "timestamp": "2026-01-03T01:00:00Z"
}
```

### 오디오 재생

```swift
// iOS - TTS 오디오 재생
func playAudioFeedback(_ feedback: AudioFeedback) {
    guard let audioData = Data(base64Encoded: feedback.audio) else {
        // 폴백: 시스템 TTS 사용
        let utterance = AVSpeechUtterance(string: feedback.text)
        utterance.rate = getPersonaRate(feedback.persona)
        synthesizer.speak(utterance)
        return
    }
    
    // Base64 디코딩 후 재생
    do {
        let player = try AVAudioPlayer(data: audioData)
        player.play()
    } catch {
        print("Audio playback failed: \(error)")
    }
}

// 페르소나별 속도 조절
func getPersonaRate(_ persona: String) -> Float {
    switch persona {
    case "drill_sergeant": return 0.6  // 빠름
    case "bestie": return 0.5          // 보통
    case "chill_guide": return 0.4     // 느림
    case "hype_coach": return 0.55     // 빠름
    default: return 0.5
    }
}
```

---

## 7. Phase 5+: 자동학습 시스템

### 세션 종료 시 수신: `signal_promotion`

승격 가능한 패턴이 감지되면:

```json
{
  "type": "signal_promotion",
  "new_candidates": 2,
  "axis_metrics": {
    "compliance_lift": "18.5%",
    "outcome_lift": "5.2%",
    "cluster_count": 3,
    "persona_count": 2,
    "negative_rate": "8.0%",
    "is_ready": true
  },
  "failing_axes": [],
  "candidates": [
    {
      "signal_key": "composition.center",
      "metrics": { ... }
    }
  ],
  "timestamp": "2026-01-03T01:00:00Z"
}
```

### 코칭 로그 전송 (세션 중)

**중요**: 앱은 코칭 개입마다 로그를 세션에 기록해야 합니다.

```swift
// 코칭 개입 시 로그 기록
struct CoachingLogEntry: Codable {
    let rule_id: String
    let domain: String
    let priority: String
    let message: String
    let t_sec: Double
    let metric_id: String?
    let metric_before: Double?
    let metric_after: Double?
    let compliance: Bool
    let user_response: String  // "complied", "ignored", "questioned"
    let is_negative: Bool
    let negative_reason: String?
}

// 세션에 로그 추가
class CoachingSession {
    var coachingLog: [CoachingLogEntry] = []
    
    func logIntervention(
        ruleId: String,
        domain: String,
        priority: String,
        message: String,
        currentTime: Double
    ) {
        let entry = CoachingLogEntry(
            rule_id: ruleId,
            domain: domain,
            priority: priority,
            message: message,
            t_sec: currentTime,
            metric_id: nil,
            metric_before: nil,
            metric_after: nil,
            compliance: false,  // 나중에 업데이트
            user_response: "unknown",
            is_negative: false,
            negative_reason: nil
        )
        coachingLog.append(entry)
    }
    
    func updateCompliance(index: Int, complied: Bool, response: String) {
        coachingLog[index].compliance = complied
        coachingLog[index].user_response = response
    }
}
```

### 세션 종료 메시지

```json
// 세션 종료 시 수신
{
  "type": "session_status",
  "status": "ended",
  "stats": {
    "total_time": 45.2,
    "rules_evaluated": 12,
    "interventions_sent": 5,
    "ended_at": "2026-01-03T01:00:00Z"
  },
  "tracking_stats": {
    "signals_tracked": 8,
    "outcomes_recorded": 5,
    "promotion_ready": 1,
    "axis_metrics": {
      "compliance_lift": 0.18,
      "outcome_lift": 0.05,
      "is_promotion_ready": true
    },
    "assignment": "coached"
  }
}
```

---

## 8. 메시지 타입 레퍼런스

### 수신 메시지 (서버 → 앱)

| 타입 | Phase | 설명 |
|------|-------|------|
| `session_status` | - | 세션 상태 변경 |
| `coaching_feedback` | 1 | 기본 코칭 피드백 |
| `graphic_guide` | 1 | 그래픽 오버레이 가이드 |
| `text_coach` | 1 | 텍스트 코칭 메시지 |
| `audio_feedback` | 4 | TTS 오디오 (페르소나별) |
| `vdg_coaching_data` | 2 | VDG 데이터 (shotlist, kicks) |
| `adaptive_response` | 3 | 적응형 코칭 응답 |
| `signal_promotion` | 5+ | 자동학습 승격 알림 |
| `rule_update` | - | 규칙 상태 업데이트 |
| `pong` | - | 핑-퐁 응답 |
| `error` | - | 에러 메시지 |

### 발신 메시지 (앱 → 서버)

| 타입 | 설명 |
|------|------|
| `control` | 세션 제어 (start/pause/stop) |
| `frame` | 프레임 데이터 전송 |
| `audio` | 오디오 데이터 전송 |
| `user_feedback` | 사용자 피드백 (Phase 3) |
| `ping` | 연결 유지 |

---

## 📦 통합 체크리스트

### Phase 1: 출력 모드 + 페르소나
- [ ] WebSocket 연결 시 `output_mode`, `persona` 파라미터 전달
- [ ] `graphic_guide` 메시지 처리 (오버레이 UI)
- [ ] `text_coach` 메시지 처리 (자막 UI)
- [ ] 모드/페르소나 선택 UI 구현

### Phase 2: VDG 데이터
- [ ] `vdg_coaching_data` 메시지 처리
- [ ] Shotlist 타임라인 UI
- [ ] Kick timing 알림

### Phase 3: 적응형 코칭
- [ ] 피드백 입력 UI (텍스트/음성)
- [ ] `user_feedback` 메시지 전송
- [ ] `adaptive_response` 처리 (수락/거절/대안)

### Phase 4: 페르소나 TTS
- [ ] `audio_feedback` 메시지 처리
- [ ] Base64 오디오 디코딩 및 재생
- [ ] 페르소나별 폴백 TTS 속도 조절

### Phase 5+: 자동학습
- [ ] 코칭 로그 기록 (CoachingLogEntry)
- [ ] `signal_promotion` 메시지 처리
- [ ] 세션 종료 시 통계 표시

---

## 🆘 FAQ

### Q: 오디오 데이터가 null로 오면?
A: 서버 TTS 실패. 앱에서 시스템 TTS(AVSpeechSynthesizer, TextToSpeech)로 폴백.

### Q: adaptive_response의 accepted가 false면?
A: DNAInvariant(바이럴 핵심 규칙) 위반. `alternative` 필드의 대안을 사용자에게 제시.

### Q: coaching_log는 언제 서버로 전송?
A: 세션 종료 시 자동으로 서버에서 수집 (세션 객체에 저장됨).

### Q: 페르소나 기본값은?
A: `chill_guide` (릴렉스 가이드 🧘)

---

## 📞 지원

문의: Backend 담당자 또는 이 문서 작성자
