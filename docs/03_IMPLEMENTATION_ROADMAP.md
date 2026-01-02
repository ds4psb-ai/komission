# 통합 로드맵: Komission Development Roadmap

> **최종 수정**: 2026-01-02  
> **상태**: 모바일 앱 Week 1 완료, 웹앱 고도화 대기  
> **통합 대상**: 03_IMPLEMENTATION, 16_NEXT_STEP, ROADMAP_MVP_TO_PERFECT, COMPUTATIONAL_TRUTH

---

## Executive Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    현재 위치 (2026-01-02)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [완료] VDG 2-Pass ─────────────────────────────┐           │
│  [완료] Director Pack ───────────────────────────┤           │
│  [완료] Audio Coach ─────────────────────────────┤           │
│  [완료] Session DB ──────────────────────────────┤           │
│  [완료] MCP 통합 ────────────────────────────────┤           │
│  ✅ [완료] 모바일 앱 Week 1 ─────────────────────┤           │
│                                                  ▼           │
│  🟡 [대기] 앱스토어 등록 ◄───────────── Week 2             │
│  🟡 [대기] 웹앱 코칭 개선 ◄────────── 새 개발자            │
│  🟡 [대기] 클러스터 10개 생성                               │
│  🟡 [대기] DistillRun 주간 실행                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: 완료된 작업 (2025-12 ~ 2026-01-02)

### ✅ VDG v4.0 2-Pass Pipeline
- Semantic Pass (Gemini 3.0 Pro)
- Visual Pass (CV 측정)
- Director Pack 컴파일러

### ✅ 실시간 AI 코칭
- WebSocket `/coaching/live/{session_id}`
- Audio Coach (Gemini 2.5 Flash)
- TTS 음성 피드백

### ✅ 모바일 앱 Week 1 (2026-01-02)

| 기능 | 상태 | 파일 |
|------|------|------|
| 4K/H.265 촬영 | ✅ | `recordingConfig.ts` |
| 프레임 레이트 안정화 | ✅ | `useCameraFormat.ts` |
| 적응형 화질 | ✅ | `useDeviceStatus.ts` |
| H.264 스트리밍 | ✅ | `videoStreamService.ts` |
| 음성/텍스트 토글 | ✅ | `CoachingOverlay.tsx` |
| DB 세션 저장 | ✅ | `useSessionPersistence.ts` |

### ✅ MCP 통합
- `/backend/app/mcp/` 폴더 구조
- Claude Desktop 연동
- Resources + Tools + Prompts

### ✅ For You UX + 댓글 통합
- PatternAnswerCard
- EvidenceBar
- TikTok 댓글 추출

---

## Part 2: 진행 중 / 대기 중

### 🟡 Week 2: 앱스토어 등록

```bash
cd mobile && npm install
npx expo prebuild --platform ios
npx expo run:ios --device
# → TestFlight → 앱스토어 심사
```

**예상 일정**: 2026-01-03 ~ 2026-01-07

### 🟡 웹앱 코칭 개선 (새 개발자)

| Phase | 목표 | 우선순위 |
|-------|------|----------|
| 1 | CV 메트릭 기반 실시간 코칭 | P0 |
| 2 | 체험단 캠페인 시스템 | P1 |

**참고 문서**: `22_DEVELOPER_ONBOARDING.md`

### 🟡 데이터 축적

| 항목 | 현재 | 목표 |
|------|------|------|
| 세션 로그 | 0개 | 50-100개 |
| 클러스터 | 스키마만 | 10개 |
| DistillRun | 미실행 | 주간 1회 |

---

## Part 3: Computational Truth (장기 로드맵)

> 상세: `STPF_V3_ROADMAP.md` 참조

### Phase 1: 제1원리 (95% 완료)
- Invariant vs Variable 분리
- Entropy 최소화
- Scale Invariance

### Phase 2: 비선형 변환 (70% 완료)
- Exponential (네트워크 효과)
- Logarithmic (한계효용 체감) ← TODO

### Phase 3: 베이지안 갱신 (50% 완료)
- PatternCalibrator ✅
- CoachingOutcome ✅
- 정밀 베이지안 공식 ← TODO

### Phase 4: Kelly Criterion (10% 완료)
- 최적 자원 배분 ← TODO
- Go/No-Go 신호 ← TODO

---

## Part 4: 성공 지표

### 기술 지표
| 지표 | 목표 |
|------|------|
| VDG 품질 점수 | 0.7+ |
| 4K 촬영 성공률 | 95%+ |
| 코칭 지연시간 | < 300ms |

### UX 지표
| 지표 | 목표 |
|------|------|
| 촬영 완료율 | 50%+ |
| 코칭 채택률 | 60%+ |

---

## Part 5: 문서 체계

### 현행 문서 (Always Up-to-Date)
- `ARCHITECTURE_FINAL.md` - 최종 아키텍처
- `21_PARALLEL_DEVELOPMENT_STRATEGY.md` - 병렬 개발 현황
- `22_DEVELOPER_ONBOARDING.md` - 온보딩
- `CHANGELOG.md` - 개발 이력

### 이론/장기 계획
- `STPF_V3_ROADMAP.md` - Computational Truth 상세
- `COMPUTATIONAL_TRUTH_ROADMAP.md` - 이론적 배경 (참조용)

### 아카이브
- `_archive_20260102/` - 완료된 작업 문서들

---

## 한 줄 요약

> **"모바일 4K 앱 Week 1 완료 → Week 2 앱스토어 등록 + 웹앱 고도화 병렬 진행"**
