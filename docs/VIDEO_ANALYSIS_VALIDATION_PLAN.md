# Video Analysis Validation Plan

목표는 "조용히 실패하는" 미세 오류를 조기에 발견하는 것이다. 파이프라인 계약, 리플레이 가능한 골든셋, 정적/동적 검증을 함께 운용한다.

## 1) 파이프라인 맵 (요약)
- Ingest: OutlierItem 생성 (`/outliers/items`, `/outliers/items/manual`)
- Promote: OutlierItem -> RemixNode 승격 (`/outliers/items/{id}/promote`)
- Approve: VDG 분석 승인 (`/outliers/items/{id}/approve`)
- Comment Gate: 댓글 추출/수동 입력 게이트
- VDG Analysis: Gemini 분석 + 품질 점수
- Cluster/Library: PatternCluster + NotebookLibraryEntry 생성
- Curation Learning: decision 기록 + rule 학습

## 2) 데이터 계약 (핵심 불변조건)
### OutlierItem 생성
- 필수: `video_url`, `platform`, `category`
- 상태: `PENDING`
- 불변조건: 동일 `video_url`/`external_id`는 중복 생성 금지

### Promote
- 입력: `item_id`, optional `campaign_eligible`, optional `matched_rule_id` + `rule_followed`
- 결과:
  - `status = PROMOTED`
  - `promoted_to_node_id` 설정
  - `analysis_status = pending`
  - `curation_decisions` 생성 (decision_type = normal|campaign)
- 불변조건: 이미 PROMOTED면 재승격 금지

### Approve + Comment Gate
- 승인 시: `analysis_status = approved`
- 댓글 확보 후: `analysis_status = analyzing`
- 댓글 실패 시:
  - 고가치(S/A): `comments_pending_review`
  - 저가치: `comments_failed`
- 수동 댓글 입력 후: `comments_ready` -> 승인 재호출

### VDG Analysis 완료
- `RemixNode.gemini_analysis` 저장
- `OutlierItem.vdg_quality_*` 저장
- `analysis_status = completed`
- `curation_decisions`의 `vdg_snapshot`/`extracted_features` 갱신

### Curation Learning
- `curation_decisions` 누적 -> `curation_rules` 생성/갱신
- 규칙 조건은 `extract_features_from_vdg`에서 생성 가능한 키여야 함

## 3) 상태 값 계약
### OutlierItemStatus (API/FE 공통)
정의 값: `pending`, `selected`, `rejected`, `promoted`

### analysis_status (canonical)
`pending`, `approved`, `analyzing`, `completed`, `comments_pending_review`, `comments_failed`, `comments_ready`, `skipped`

유의: 코드에 등장하는 값 목록과 모델/프론트 값의 정합성은 주기적으로 검증한다.

## 4) 골든셋 설계
### 구성 원칙
- 20~50개 영상, 플랫폼별 균형
- 엣지 케이스 포함:
  - 댓글 0개/비공개
  - 초단편 (<5s) / 장편 (>90s)
  - 다국어/이모지 중심 댓글
  - 중복 URL/재승격 시나리오

### 저장 구조 (예시)
```
backend/tests/fixtures/vdg_golden/
  manifest.json
  items/
    item_001.json  # OutlierItem payload
    item_001_comments.json
    item_001_vdg.json
```

### 리플레이 규칙
- 외부 API 호출은 고정된 댓글/VDG 결과로 대체
- 결과 비교는 키 존재/값 범위/배열 길이 기반으로 판단

## 5) 회귀 비교 기준
- 필수 키 존재율: 100%
- 배열 길이 허용 오차: ±10%
- 수치형 주요 값(예: hook_strength, duration_sec): ±15% 이내
- 텍스트 필드: 공백/정규화 후 비교

## 6) 자동 점검 스크립트
- 정적 계약 검사: `python backend/scripts/audit_pipeline_contracts.py`
- 로컬 학습 검증: `python backend/scripts/verify_curation_learning.py --allow-delete`

## 7) 운영 루프
- 주 1회: 계약 검사 + 골든셋 리플레이
- 주요 변경 시: 그림자 실행 후 diff 리포트 생성
- 이슈 발생 시: 재현 시나리오 추가 및 회귀 케이스로 고정
