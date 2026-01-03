# User Flow (2025-12-30)

**Updated**: 2025-12-30  
**목표**: Creator 중심 E2E 흐름 (Outlier → 코칭 → 제출)

---

## 1) 역할 정의

| 역할 | 주요 action |
|------|------------|
| **Creator** | Outlier 발견 → AI 코칭 촬영 → 제출 |
| **Curator** | Outlier 수집 → Parent 승격 → Pack 검증 |
| **Brand** | 캠페인 설정 → 체험단 운영 |

---

## 2) Creator 흐름 (핵심)

```
[Outlier 탐색] → [카드 상세] → [🎬 촬영 시작] → [모드 선택]
                                                      ↓
                                          ├─ 오마쥬 (DNA Lock)
                                          ├─ 변주 (Mutation Slot)
                                          └─ 체험단 (Campaign)
                                                      ↓
                                          [CoachingSession]
                                          ├─ 카메라 프리뷰
                                          ├─ 🎙️ AI 오디오 피드백
                                          └─ 규칙 체크리스트
                                                      ↓
                                          [결과 확인 + 제출]
```

### 2.1 상세 단계

1. **Outlier 발견**
   - For You / Trending / 검색
   - S/A-Tier Outlier 카드 탐색

2. **카드 상세 확인**
   - `/video/{id}` 페이지
   - 바이럴 가이드 (훅/타이밍/불변/가변)
   - Storyboard 확인

3. **AI 코칭 촬영**
   - "🎬 촬영 시작하기" 버튼
   - 모드 선택 (오마쥬/변주/체험단)
   - `CoachingSession` 진입

4. **실시간 코칭**
   - 카메라 프리뷰 (세로)
   - AI 음성 피드백
   - 규칙 체크리스트 (Pack 기반)
   - 진행률 표시 (R_ES)

5. **제출/추적**
   - 촬영 완료 → 제출
   - My 페이지에서 성과 확인

---

## 3) Curator 흐름

1. **Outlier 수집**
   - 수동 링크 입력 / 크롤러

2. **VDG 분석**
   - 2-Pass Pipeline 실행
   - VDGv4 생성

3. **Pack 컴파일**
   - DirectorPack 생성
   - 규칙 검증

4. **Parent 승격**
   - S/A-Tier 후보 검토
   - Parent로 승격

---

## 4) 체험단 (O2O) 흐름

| 타입 | 흐름 |
|------|------|
| **즉시형** | 신청 → 촬영 → 제출 |
| **방문형** | 신청 → 위치인증 → 촬영 → 제출 |
| **배송형** | 신청 → 선정 → 배송 → 촬영 → 제출 |

---

## 5) API Endpoints

| Action | Endpoint |
|--------|----------|
| 카드 조회 | `GET /api/v1/outliers/items/{item_id}` |
| 가이드 조회 | `GET /api/v1/outliers/items/{item_id}` (shooting_guide 포함) |
| 코칭 시작 | `POST /api/v1/coaching/sessions` |
| 피드백 제출 | `POST /api/v1/coaching/sessions/{session_id}/feedback` |
| 코칭 종료 | `POST /api/v1/coaching/sessions/{session_id}/end` 또는 `DELETE /api/v1/coaching/sessions/{session_id}` |

코칭 시작 응답의 `websocket_url`로 WebSocket에 연결합니다.

---

## 6) Reference

- [CoachingSession.tsx](../frontend/src/components/CoachingSession.tsx) - 코칭 UI
- [video/[id]/page.tsx](../frontend/src/app/video/[id]/page.tsx) - 카드 상세
