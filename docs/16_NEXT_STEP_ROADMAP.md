# Next Step Roadmap: 바이럴 DNA 축적 + MCP 통합 전략

**작성**: 2025-12-28  
**버전**: v5.1  
**상태**: For You UX 완료 → **VDG 댓글 통합 완료** → MCP 통합 단계

---

## 1. Executive Summary

프로토타입 개발 완료 후, **Answer-First (For You)와 MCP 기반 AI 통합**으로 실질적인 바이럴 DNA 이식 가치를 실현하기 위한 전략 로드맵입니다.

**v5.0 핵심 변경**:
- ✅ For You 페이지 신설 (Answer-First (For You))
- 🚀 MCP Resources/Tools/Prompts 통합 설계
- 🔒 사용자 동의 UI (MCP 보안 원칙)

**아키텍처 검증**:
> 업계 베스트 프랙티스 대비 검증 완료. Answer-First (For You), MCP 분리 설계,
> 배치 기반 Recurrence, Evidence 기반 신뢰 구축 모두 최신 표준과 정합.

---

## 2. VDG 영상해석력 검증 - ✅ 완료

| 항목 | 상태 |
|-----|------|
| hook_genome 분석 | ✅ 정확 |
| commerce 제품 추출 | ✅ 정확 |
| remix_suggestions | ✅ 프롬프트 강화 완료 |
| 품질 검증기 | ✅ 구현 완료 |

---

## 2.5 VDG 댓글 통합 - ✅ 완료 (2025-12-28)

| 항목 | 상태 |
|-----|------|
| Cookie 추출 (sessionid) | ✅ Playwright persistent context |
| Secret Manager 등록 | ✅ `tiktok-cookies` v3 |
| Cloud Run 적용 | ✅ `tiktok-extractor`, `komission-api` |
| 댓글 추출 API | ✅ 5개 댓글 검증 완료 |
| VDG 프롬프트 통합 | ✅ `AUDIENCE REACTIONS` 섹션 |

**파이프라인 검증 결과:**
```
outliers.py → extract_best_comments()
         ↓
✅ 댓글 있음 → gemini_pipeline.analyze_video()
         ↓
⚠️ S/A 티어 + 댓글 실패 → 202 + comments_pending_review
         ↓
🚫 B/C 티어 + 댓글 실패 → 503 + comments_failed
```

**수동 검토 API:**
- `GET /outliers/items/pending-comments` - 검토 대기 목록
- `PATCH /outliers/items/{id}/comments` - 수동 댓글 입력 후 VDG 재시도

---

## 3. 콘텐츠 필터 - ✅ 구현 완료

| 카테고리 | 필터 방식 |
|----------|----------|
| 방송사 채널 | 채널명 매칭 |
| TV 프로그램 | 키워드 정규식 |
| 연예인/아이돌 | 키워드 매칭 |

```
Content Filter Test: 12/12 PASSED
```

---

## 4. 플랫폼 우선순위

| 플랫폼 | 우선순위 | 예상 사용률 |
|-------|---------|-----------:|
| TikTok | 🥇 1순위 | 70% |
| YouTube Shorts | 🥈 2순위 | 10% |
| Instagram Reels | 🥉 3순위 | 5% |

---

## 5. For You UX 전략 (신규)

### 5.1 Answer-First (For You) 원칙

**Answer-First (For You)**: 검색보다 추천을 먼저 제시하는 UX 원칙

```
기존: 사용자가 검색 → 결과 나열 → 선택
신규: 시스템이 추천 → 근거 제시 → 즉시 활용
```

### 5.2 페이지 구조

| 컴포넌트 | 용도 |
|---------|------|
| PatternAnswerCard | S/A/B 티어 패턴 카드 |
| EvidenceBar | 베스트 댓글 + 재등장 근거 |
| FeedbackWidget | 👍👎 피드백 수집 |

> ⚠️ **EvidenceBar Fallback**: TikTok 댓글 수집이 비활성화된 경우 (`SKIP_TIKTOK_COMMENTS=true`),
> VDG 기반 신호(hook_genome, remix_suggestions)로 대체 표시. 빈 상태 방지 필수.

### 5.3 세션 흐름

```
/for-you → 즉시 패턴 추천 (인라인 필터: 카테고리/플랫폼)
    ↓
/session/result → 맞춤 결과 + EvidenceBar (선택 시)
    ↓
/session/shoot → 촬영 가이드
```

> 💡 **Friction 최소화**: 초기 추천은 필터 없이 표시, 상세 입력은 선택적.

---

## 6. MCP 통합 전략 (2025-12-31 업데이트)

> MCP 2025-11-25 스펙 + FastMCP 2.14+ 기준

### 6.0 FastMCP 2.14+ 신기능 활용 현황

| 기능 | 활용 방안 | 상태 |
|------|----------|------|
| **Background Tasks** | `task=True` 데코레이터로 VDG 재분석 진행률 보고 | ✅ 적용 |
| **Progress 의존성** | `Progress` 의존성 주입으로 단계별 진행률 추적 | ✅ 적용 |
| **Elicitation** | 대량 생성/강제 재분석 시 사용자 확인 요청 | ✅ 적용 |
| **Server Composition** | VDG MCP + Coaching MCP 분리 고려 | 🥉 향후 |
| **Structured Output** | Pydantic 모델 반환 (`SearchResponse`, `SourcePackResponse`) | ✅ 적용 |

### 6.1 Resources (읽기 전용)

| URI | 설명 |
|-----|------|
| `komission://patterns/{cluster_id}` | Pattern Library 항목 |
| `komission://comments/{outlier_id}` | 베스트 댓글 5개 (수집 시점 스냅샷) |
| `komission://evidence/{pattern_id}` | Evidence 요약 (댓글+신호+지표 종합) |
| `komission://recurrence/{cluster_id}` | 재등장 lineage (배치 처리 결과) |
| `komission://vdg/{outlier_id}` | VDG 분석 결과 |
| `komission://director-pack/{outlier_id}` | Director Pack (VDG v4 기반, on-demand 생성) |

> ⚠️ `recurrence`는 배치 파이프라인에서 사전 계산된 결과를 노출. 실시간 매칭 아님.

### 6.2 Tools (실행)

| Tool | 용도 | 동의 | 비고 |
|------|------|------|------|
| `search_patterns` | L1/L2 패턴 검색 | 자동 | 읽기 전용 |
| `generate_source_pack` | NotebookLM 팩 생성 | 명시적 | 데이터 생성 |
| `reanalyze_vdg` | VDG 재분석 | 명시적 | 비용 발생 |

> ⚠️ `detect_recurrence`는 배치 파이프라인 전용. 사용자 Tool 아님 → Resource로 결과만 노출.
> ✅ `search_patterns`/`generate_source_pack`는 `output_format="json"` 지원.

### 6.3 Prompts (템플릿)

| Prompt ID | 용도 |
|-----------|------|
| `explain_recommendation` | 추천 이유 설명 |
| `shooting_guide` | 촬영 가이드 요약 |
| `risk_summary` | 리스크 정리 |

### 6.4 보안 강화 로드맵 (2025)

| 항목 | 현재 | 목표 |
|------|------|------|
| 인증 | 없음 (로컬 전용) | OAuth 2.1 (원격 배포 시) |
| 권한 | 도구별 동의 | RBAC (role 기반) |
| 입력 검증 | 기본 | Pydantic strict validation |
| Transport | stdio | Streamable HTTP (원격 시) |

---

## 7. 사용자 동의 UI 설계 (신규)

> MCP 보안 원칙: 사용자 동의 없이 데이터 수정 금지

### 7.1 동의 레벨

| 레벨 | 적용 대상 | UI |
|------|---------|-----|
| 자동 허용 | 검색, 조회 | 없음 |
| 알림만 | 분석 실행 | Toast |
| 명시적 승인 | 데이터 생성/수정 | Modal |

### 7.2 자동 승인 범위 설정

```tsx
// 사용자 설정 가능
autoApprove: {
  search_patterns: true,      // 자동
  generate_source_pack: false, // 승인 필요
  reanalyze_vdg: false,       // 승인 필요
}
```

---

## 8. 성공 지표

### 8.1 기술 지표

| 지표 | 목표 |
|------|------|
| VDG 품질 점수 평균 | 0.7+ |
| 콘텐츠 필터 정확도 | 95%+ |
| 주간 Outlier 수집 | 100개 |

### 8.2 UX 지표 (신규)

| 지표 | 목표 |
|------|------|
| For You 체류 시간 | 2분+ |
| Evidence 확장률 | 40%+ |
| Shoot 전환율 | 15%+ |

### 8.3 MCP 지표 (신규)

| 지표 | 목표 |
|------|------|
| Resources 호출/세션 | 5+ |
| Tool 승인율 | 80%+ |
| Prompt 사용률 | 30%+ |

---

## 9. 실행 계획

### Week 1-2 ✅ 완료
- VDG 프롬프트 강화
- 콘텐츠 필터 구현
- 품질 검증기 구현

### Week 3 ✅ 완료
| 태스크 | 상태 |
|-------|------|
| For You 백엔드 API | ✅ |
| VDG 댓글 통합 파이프라인 | ✅ |
| Cookie/Secret Manager 설정 | ✅ |
| MCP Resources 서버 | ✅ |

### Week 4 (예정)
| 태스크 | 우선순위 |
|-------|---------|
| MCP Tools 서버 | 🥇 |
| Explain/Why 버튼 연동 | 🥈 |
| MCP Prompts 템플릿 정의 | 🥉 |

---

## 10. 핵심 원칙

1. **품질 우선** - remix_suggestions 품질 검증 자동화
2. **다중 신호 필터** - TV/연예인을 채널+제목+해시태그로 차단
3. **Answer-First (For You)** - 검색보다 추천을 먼저 제시하는 UX 원칙
4. **MCP Resources 우선** - 근거는 읽기 전용으로 노출
5. **Tool 실행 동의** - 사용자 승인 없이 데이터 수정 금지
6. **Prompt 표준화** - 설명 템플릿으로 출력 품질 보장

---

## Appendix: 관련 파일

| 파일 | 용도 |
|-----|------|
| `frontend/src/app/(app)/for-you/page.tsx` | For You 페이지 |
| `frontend/src/components/PatternAnswerCard.tsx` | 패턴 카드 |
| `frontend/src/components/EvidenceBar.tsx` | 증거 바 |
| `backend/app/services/gemini_pipeline.py` | VDG 프롬프트 |
| `backend/app/crawlers/content_filter.py` | 콘텐츠 필터 |
| `backend/scripts/run_scheduled_crawl.py` | 배치 크롤러 (댓글 설정) |
| `backend/scripts/export_tiktok_cookies.py` | TikTok 쿠키 추출 (신규) |
| `backend/app/services/comment_extractor.py` | 댓글 추출 서비스 |
