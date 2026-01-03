# Virlo Benchmark + 적용 계획 (최신)

**작성**: 2026-01-07
**범위**: 로그인 상태 UI 탐색 기반. 보안 토큰/비공개 키 추출은 하지 않음.

---

## 1) 관찰된 IA/기능 구조 (요약)
### Dashboard
- 섹션: **Niches / Trends / Recently Added Outliers**
- 필터: **Global / For You**
- 플랫폼 토글: **TikTok / YouTube / Instagram(BETA)**
- 요소: **Custom Niche**, **Leaderboard**, **Research** 진입

### Outlier
- 필터: **Fresh Content**, **All Platforms**
- 리스트 중심 탐색 + 가시적인 성과 지표(배수형 강조)

### Creator Search
- 플랫폼 토글: **TikTok / YouTube**
- **Analyze** 버튼 존재
- **Search History** 제공

### Orbit Search
- 신규 고급 검색(“Create Your First Orbit Search” 형태)
- 특정 주제/패턴의 심화 검색 허브로 보임

### Collections
- **New collection box**로 큐레이션 그룹 관리

### Knowledge Center
- **Virality Puzzle**, **Trial Reels Strategy**, **Hook Library** 콘텐츠 제공
- 교육형/레퍼런스 허브 성격

### Content Studio
- 개인 워크스페이스 기반
- **Create New Canvas** 플로우

### Media Generation
- **Create Your First Flow**형 실행 플로우

---

## 2) Komission 적용 방향 (차별화 포함)
### 공통 방향
- 탐색 UI가 아닌 **Evidence 기반 실행 브리프**로 연결
- Role Switch(Creator/Business)로 컨텍스트 이동 최소화
- Notebook Library는 **DB로 래핑** 후 사용 (NotebookLM = Pattern Engine, 기본 실행)

### 매핑 제안
| Virlo 기능 | Komission 대응 | 차별화 포인트 |
| --- | --- | --- |
| Dashboard (Niches/Trends/Outliers) | Discover + Evidence Radar | Evidence/Pattern Lift 중심 우선 노출 |
| Outlier 리스트 | Outlier 후보 + Parent 승격 | “Promote to Parent” + Evidence 스냅샷 |
| Creator Search | Creator/O2O 매칭 | Role Switch로 비즈니스 컨텍스트 유지 |
| Orbit Search | Genealogy/Pattern Search | Parent-Kids 구조 기반 검색 |
| Collections | Evidence Boards | 실험 단위로 묶고 KPI/결론 표시 |
| Knowledge Center | Evidence Brief + Hook Library | 검증된 패턴만 노출 |
| Content Studio | Canvas / Capsule | 캡슐 입출력 중심 UI |
| Media Generation | Capsule 후속 자동화 | 숏폼 브리프 기반 실행 템플릿 |

---

## 3) 우선 적용 계획 (Phased)
### Phase A: Discover + Outlier 강화 (✅ Implemented 2025-12-25)
- [x] Niches/Trends/Recently Added 섹션 추가 → `/` (홈, Unified Outlier Discovery)
- [x] 플랫폼 토글 + Fresh Content 필터 → `CrawlerOutlierSelector`
- [x] "Promote to Parent" CTA 고정 → `CrawlerOutlierCard` + `CrawlerOutlierNode`

**구현 파일:**
- `frontend/src/app/page.tsx` (홈 피드)
- `frontend/src/app/outliers/page.tsx` (Ops 리다이렉트 스텁)
- `frontend/src/components/CrawlerOutlierCard.tsx`
- `frontend/src/components/canvas/CrawlerOutlierNode` (in CustomNodes.tsx)
- `frontend/src/components/canvas/CrawlerOutlierSelector.tsx`

### Phase B: Orbit/Collections 개념 도입
- Orbit Search → Genealogy/Pattern Search로 변환
- Collections → Evidence Boards로 고정

### Phase C: Knowledge Center 재해석
- Hook Library = Pattern Lift 상위 패턴만 노출
- Trial Strategy = Evidence 기반 실행 가이드 요약

### Phase D: Studio/Media Generation
- Canvas에서 Capsule Output을 기반으로 Shotlist/Audio/Timing 생성
- 자동 생성은 Pro 모드에서만 활성화

---

## 4) 데이터/통합 원칙
- **토큰/비공개 키 추출 금지**
- 통합은 **공식 API/Export**만 사용
- 외부 데이터는 반드시 **Evidence Loop 구조로 정규화**

---

## 5) 즉시 반영 대상 (UI/UX)
- Dashboard에 **Niche/Trends/Recently Added** 섹션
- Outlier 리스트의 **Fresh/Platform 필터**
- Role Switch 상단 고정
- Evidence-first 카드 재배치
