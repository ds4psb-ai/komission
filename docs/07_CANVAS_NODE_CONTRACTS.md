# Canvas + Node Contracts (최신)

**작성**: 2026-01-07
**목표**: 노드 입력/출력 계약과 UI 노출 원칙을 고정

---

## 1) 노드 타입
**Implemented**
- **Source Node (Outlier/Remix)**: 원본 링크/기초 메타 (RemixNode 기반)
- **CrawlerOutlier Node**: 3-플랫폼 크롤러 수집 아웃라이어 (`CrawlerOutlierItem` 기반)
- **Process Node**: 분석/파이프라인 실행 상태
- **Output Node**: 결과 요약 카드
- **Notebook Node**: Notebook Library 요약 (현재는 정적 표시)
- **Evidence Node**: Evidence Sheet 요약
- **Decision Node**: Decision Sheet 요약
- **Capsule Node**: 내부 체인 실행(숨김)
- **Template Seed Node (Opal)**: 템플릿 시드/초안 (선택)
- **Guide Node**: 실행 브리프 렌더링

**Representation**
- **Parent Node (MASTER)**: 별도 타입이 아니라 Source Node의 `isLocked`/badge로 표현

**Planned (not in current build)**
- **Pattern Answer Node (For You)**: L1/L2 검색 결과 + Evidence 표시
- **O2O Node**: 캠페인 타입/게이팅 규칙

---

## 2) Capsule Node 계약
**UI Contract (CapsuleDefinition)**
- id/title/summary/provider
- inputs: string[] (표시용)
- outputs: string[] (표시용)
- params: key/label/type/options/value
- persona_context (optional)

**Execution Output**
- GuideNode payload: hook/shotlist/audio/scene/timing/do_not
- 현재는 로컬 시뮬레이션 (backend 연결 예정)

### Capsule Output (Short-form 실행 브리프)
레거시처럼 긴 텍스트 가이드가 아니라, **실행 가능한 숏폼 브리프**만 노출합니다.

**필수 필드**
- `hook`: 0~2초 훅 문장/장면
- `shotlist`: 3~6개 샷 시퀀스
- `audio`: 추천 사운드/리듬/볼륨 레벨
- `scene`: 장소/소품/분위기
- `timing`: 컷 길이/템포 (예: 1.2s / 0.8s / 1.5s)
- `do_not`: 금지 요소(브랜드/법적/리스크)

> 이 출력은 Canvas에서 **Guide Node**로 표시됩니다.

**UI 노출 원칙**
- 사용자는 **입력/출력만** 본다
- 내부 체인(Opal/NotebookLM/n8n) 세부 로직은 **숨김**

---

## 2.1) Pattern Answer Node (Planned)
Pattern Answer Node는 현재 빌드에 포함되어 있지 않으며, 향후 For You UI 전용 노드로 추가 예정.

---

## 3) Evidence/Decision 노드 UI 규칙
- Evidence: 상위 5개 패턴 + 리스크 2개 (best_comments/recurrence 배지는 현재 미표시)
- Decision: 결론 1줄 + 근거 3개 + 다음 실험 1개
- 길고 무거운 설명은 접힘 처리

---

## 4) 템플릿 연결 원칙
- 템플릿은 **노드 결과를 소비**하는 레이어
- 사용자 커스터마이징은 **캡슐 입력 슬롯**만 허용
- 캔버스는 **설명 가능성**이 아니라 **실행 가능성**을 우선
