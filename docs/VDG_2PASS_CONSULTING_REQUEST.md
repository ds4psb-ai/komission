# VDG 2-Pass 시스템 외부 컨설팅 요청서

> 작성일: 2025-12-31 | 버전: v1.0

---

## 1. 배경

### 현재 시스템 개요

VDG(Video Data Graph) v4.0 2-Pass Pipeline은 숏폼 비디오(15-60초) 분석을 위한 시스템입니다:

| Pass | 모델 | 입력 | 출력 |
|------|------|------|------|
| **Pass 1 (Semantic)** | Gemini 2.0 Flash | 전체 비디오 bytes + 댓글 | 씬 분석, 훅, 의도, 엔티티 힌트 |
| **Pass 2 (Visual)** | Gemini Pro | 프레임 추출본 + AnalysisPlan | 메트릭, 엔티티 해상도, 객체 추적 |

### 제기된 우려

> "VDG 2-Pass가 Gemini 3.0 Pro API 기반 2패스의 장점을 못살리고 오히려 1패스보다도 못한 영상해석 시스템"

---

## 2. 현재 구현 상세

### Pass 1: Semantic Pass

```python
# semantic_pass.py (요약)
class SemanticPass:
    model_name = "gemini-2.0-flash-exp"
    
    async def analyze(self, video_bytes, duration_sec, comments):
        # 전체 비디오 bytes를 Part로 변환
        video_part = Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        
        # Flash 모델로 단일 호출
        response = await client.aio.models.generate_content(
            model=self.model_name,
            contents=[video_part, user_prompt],
            config={"response_mime_type": "application/json"}
        )
```

**잠재적 문제점:**
1. 전체 비디오를 Flash 모델에 전송 → 약 263 tokens/초 비용
2. Gemini의 기본 1fps 샘플링에 의존 → FPS 제어 없음
3. 시각적 세부사항보다 "의미" 추출에 집중하지만, 전체 비디오 토큰 소비

### Pass 2: Visual Pass

```python
# visual_pass.py (요약)
class VisualPass:
    model_name = "gemini-2.0-pro-exp"
    
    async def analyze(self, video_bytes, plan, entity_hints):
        # P0-2: AnalysisPlan 기반 프레임 추출
        if self._use_frames and len(plan.points) > 0:
            frames = FrameExtractor.extract_for_plan(video_bytes, plan)
            video_parts = [Part.from_bytes(f["bytes"]) for f in frames]
        else:
            # Fallback: 전체 비디오
            video_parts = [Part.from_bytes(video_bytes)]
```

**잠재적 문제점:**
1. Pass 1의 AnalysisPlan에 의존 → Pass 1 품질이 병목
2. Pro 모델은 더 비쌈 → 프레임 선택이 최적화되지 않으면 비용 증가
3. 프레임 추출 시 ffmpeg 의존 → 가용하지 않으면 전체 비디오 fallback

---

## 3. 웹 리서치 결과

### Gemini 비디오 분석 Best Practices

| 항목 | Google 권장 | 현재 VDG 구현 | 차이 |
|------|-------------|--------------|------|
| **프롬프트 위치** | 비디오 데이터 뒤에 배치 | ✅ 준수 | - |
| **FPS 제어** | 작업에 따라 조정 (1fps~고속) | ❌ 기본값 사용 | 최적화 필요 |
| **media_resolution** | low/medium/high 선택 | ❌ 미사용 | 비용 최적화 가능 |
| **긴 영상** | 클리핑/세그먼트 | N/A (숏폼) | - |
| **모델 선택** | 작업 복잡도에 따라 | ⚠️ Flash+Pro 고정 | 유연성 필요 |

### Multi-Pass vs Single-Pass 분석

| 접근법 | 장점 | 단점 |
|--------|------|------|
| **Single-Pass** | 속도, 단순성, world knowledge 활용 | 정보 손실, 복잡한 temporal 이해 어려움 |
| **Multi-Pass** | 긴 영상에 유리, 특화된 처리, 동적 프레임 선택 | 복잡성, 느린 추론, 누적 오류 가능 |

### 핵심 인사이트

1. **Gemini의 네이티브 비디오 이해**: 모델은 오디오+비주얼 동시 처리 가능 → 분리된 패스가 이 장점을 상쇄할 수 있음
2. **토큰 효율성**: 263 tokens/sec에서 60초 영상 = ~15,780 토큰 × 2패스 = 31,560 토큰
3. **1-Pass 가능성**: 숏폼 비디오는 단일 컨텍스트 윈도우 내 처리 가능 → 2-Pass가 오버엔지니어링일 수 있음

---

## 4. 핵심 질문 (컨설팅 요청)

### A. 아키텍처 적합성

1. **숏폼(15-60초) 비디오에 2-Pass가 정말 필요한가?**
   - Gemini의 컨텍스트 윈도우(2M 토큰)는 6시간 이상 비디오 처리 가능
   - 숏폼에서 2-Pass의 ROI는?

2. **Pass 1→Pass 2 의존성이 병목인가?**
   - AnalysisPlan 품질이 Pass 2를 제한
   - 독립적인 병렬 패스가 더 나은가?

### B. Gemini 활용 최적화

3. **네이티브 오디오+비주얼 통합을 활용하고 있는가?**
   - 현재: 비디오만 분석, 오디오 별도
   - Gemini 3.0의 네이티브 오디오 코칭 가능

4. **FPS와 media_resolution 파라미터를 사용해야 하는가?**
   - 숏폼에 최적의 FPS는?
   - 비용 vs 품질 트레이드오프

### C. 비용 효율성

5. **2-Pass가 1-Pass 대비 비용 효율적인가?**
   - Flash + Pro = X 비용
   - Pro 단독 (1-Pass) = Y 비용
   - 실제 측정 필요

6. **프레임 추출 vs 전체 비디오 전송의 실질적 이점은?**
   - 토큰 절약 실측치
   - ffmpeg 의존성 제거 가능성

### D. 품질 평가

7. **2-Pass 출력이 1-Pass보다 실제로 우수한가?**
   - 동일 비디오에 대한 A/B 평가 필요
   - 골든 테스트셋 구축

8. **"오히려 못하다"의 구체적 증거는?**
   - 어떤 메트릭에서 실패하는가?
   - 재현 가능한 실패 사례

---

## 5. 제안하는 컨설팅 범위

### Phase 1: 현상 진단 (1주)

- [ ] 현재 2-Pass 시스템 코드 리뷰
- [ ] 10개 샘플 비디오로 1-Pass vs 2-Pass 비교 분석
- [ ] 토큰 소비, 지연시간, 출력 품질 측정

### Phase 2: 개선안 설계 (1주)

- [ ] 아키텍처 옵션 제시 (1-Pass / 2-Pass 개선 / 하이브리드)
- [ ] Gemini 3.0 최신 기능 활용 방안
- [ ] 비용 최적화 전략

### Phase 3: PoC 구현 (선택, 2주)

- [ ] 선택된 아키텍처 프로토타입
- [ ] 벤치마크 결과 제공

---

## 6. 관련 파일

| 파일 | 설명 |
|------|------|
| [semantic_pass.py](file:///Users/ted/komission/backend/app/services/vdg_2pass/semantic_pass.py) | Pass 1 구현 (128줄) |
| [visual_pass.py](file:///Users/ted/komission/backend/app/services/vdg_2pass/visual_pass.py) | Pass 2 구현 (223줄) |
| [vdg_v4.py](file:///Users/ted/komission/backend/app/schemas/vdg_v4.py) | VDG 스키마 (1039줄) |
| [gemini_utils.py](file:///Users/ted/komission/backend/app/services/vdg_2pass/gemini_utils.py) | retry/fallback 유틸 |
| [analysis_pipeline.py](file:///Users/ted/komission/backend/app/services/analysis_pipeline.py) | 레거시 1-Pass (비교용) |

---

## 7. 연락처

- **프로젝트**: Komission (K-숏폼 크리에이터 지원 플랫폼)
- **기술 스택**: Python 3.13, FastAPI, google-genai v1.56.0, Next.js 16
- **환경**: Gemini 2.0 Flash/Pro (마이그레이션 완료), Sentry 모니터링

---

> 본 요청서는 외부 전문가에게 VDG 2-Pass 시스템의 진단 및 개선 방향 컨설팅을 의뢰하기 위해 작성되었습니다.
