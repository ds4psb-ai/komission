# Final Architecture Blueprint (Komission)

**작성**: 2026-01-07  
**목표**: 코드 기반 영상 해석 + 유사도 클러스터링을 본체로 고정하고, NotebookLM/Opal을 보조 레이어로 재정의

---

## 1) 최종 결론 (한 줄)
**해석은 코드, 학습은 DB, NotebookLM은 지식/가이드 레이어, Opal은 템플릿 시드 생성기**가 최선이다.

---

## 2) 역할 분리 (핵심 원칙)
- **영상 해석(코드)**: 스키마 생성, 재현성/버전관리 담당
- **유사도 클러스터링(DB)**: Parent‑Kids 변주를 데이터화, 패턴 뎁스 구조를 축적
- **NotebookLM**: 클러스터를 노트북 폴더로 정리, light RAG/가이드 생성
- **Opal**: 초기 템플릿/노드 설계 시드 생성, 의사결정 요약 보조
- **DB = SoR**, Sheets = 운영/공유 버스
- **Structured Output**: JSON Schema 강제, 재현성 보장

---

## 3) 전체 데이터 흐름 (최종)
```
Outlier 수집(구독/수동/YouTube API)
  → 영상 해석(코드, Gemini 3.0 Pro 기반 스키마)
  → 유사도 클러스터링(Parent‑Kids 패턴)
  → Notebook Library(DB) 저장
  → NotebookLM 노트북 폴더 동기화(선택)
  → Evidence Loop(VDG + Progress + Decision)
  → Opal 템플릿 시드 생성(선택)
  → Capsule/Template 실행(캔버스 노드)
  → 성과/편집 로그 → RL‑lite 정책 업데이트
```

---

## 4) NotebookLM의 정확한 역할
**NotebookLM은 “분석 엔진”이 아니라 “지식/가이드 레이어”**입니다.
- 클러스터별 노트북 폴더 관리 (예: 600개 패턴 백과사전)
- light RAG로 “오마주 변주 / 다음 뎁스 추천 / 복제 가이드” 생성
- 결과는 **DB에 래핑** 후 사용

> 중요한 점: NotebookLM은 보조 레이어이며, SoR는 절대 DB입니다.

---

## 5) Opal의 정확한 역할
**Opal은 “노드 템플릿 시드 생성기”이자 “의사결정 요약 보조”**입니다.
- 초기 템플릿/노드 스펙을 생성 (캡슐/템플릿 시드)
- 결과를 Sheet로 출력 → DB에 래핑
- 사용자에게는 **블랙박스 노드**로 노출 (입출력만 공개)

> Opal은 “구성/설계”를 돕고, 실행/학습은 DB가 담당합니다.

---

## 6) 핵심 데이터 모델 (요약)
- `outlier_items`: 원본 후보 (수집)
- `analysis_schema` (Notebook Library 내 포함): 코드 기반 해석 스키마
- `pattern_clusters`: 유사도 클러스터
- `notebook_library`: 분석 스키마 + (선택) NotebookLM 요약
- `evidence_snapshots`, `metric_daily`: 증거/성과
- `template_versions`, `template_feedback`, `template_policy`: RL‑lite 학습
- `template_seeds` (Opal): 초기 템플릿 시드 기록

---

## 7) 강화학습(RL‑lite) 전략
복잡한 RL 대신 **정책 업데이트(경량)**로 진행:
- 템플릿 수정 로그 + 성과 지표 → 승자 구조 업데이트
- 주간 배치 업데이트로 템플릿 기본값 개선
- 변주 생성은 **유전(변이)**, 선택은 **bandit 탐색**으로 현실화

---

## 8) 제품 UX와의 연결
- Creator: **가이드/브리프 중심**, 복잡한 체인은 숨김
- Business: Evidence/Decision 중심, 성과 기반 루프 운영
- Canvas: Opal/NotebookLM을 감춘 **Capsule Node**로 노출

---

## 9) 결정 기준 (왜 이 구조가 최선인가)
- **재현성/확장성**: 스키마/클러스터는 코드 기반이 가장 안정적
- **UX 품질**: NotebookLM은 가이드/요약에 최적화
- **운영 효율**: DB가 SoR일 때 자동화/검증 가능
- **장기 경쟁력**: 패턴 뎁스 데이터가 쌓일수록 진화하는 구조

---

## 10) 다음 단계 (문서/코드)
1. 이 설계를 모든 문서에 반영 (완료 목표)
2. 코드/스키마 정합성 반영
3. Canvas 노드와 Opal 시드 플로우 연결
