# VDG 파이프라인 컨설팅 요청

> 작성일: 2026-01-01
> 샘플 영상: @goodworkmb - every company is every company (17.5M views, S-Tier)

---

## 1. 현재 DB 상태 (실제 데이터)

### ✅ 정상 작동
| 필드 | 값 | 설명 |
|------|-----|------|
| `provenance.viral_kicks` | 3개 | 킥 포인트 + creator_instruction |
| `semantic.hook_genome` | 7개 키 | pattern, delivery, end_sec 등 |
| `semantic.intent_layer` | hook_trigger 등 | 호기심 유발 정보 |
| `analysis_plan.points` | 9개 | CV 측정 포인트 |
| `mise_en_scene_signals` | 8개 | 미장센 신호 |

### ❌ 빈 값 또는 미존재
| 필드 | 상태 | 영향 |
|------|------|------|
| `semantic.scenes` | **0개** (빈 배열) | 스토리보드 없음 |
| `capsule_brief.shotlist` | **0개** | 샷리스트 없음 |
| `capsule_brief.do_not` | **0개** | 주의사항 없음 |
| `director_pack` | **미존재** | 촬영 가이드 없음 |
| `invariant_guide` | **미존재** | 핵심 유지 요소 없음 |
| `variable_guide` | **미존재** | 변주 가능 요소 없음 |

---

## 2. 현재 해결 방식 (임시)

### invariant/variable → 런타임 유추
```python
# outliers.py _extract_invariant()
def _extract_invariant(analysis):
    # hook_genome.pattern → "🎣 훅 패턴: other"
    # hook_genome.delivery → "🎯 전달 방식: 시각적 개그"
    # viral_kicks[].mechanism → "✨ 핵심 메커니즘: 시각적 임팩트"
    # intent_layer.hook_trigger → "🧲 호기심 유발"
    ...
```
**문제**: DB에 저장되지 않음, 영상별 실제 분석이 아닌 일반적 유추

### shotlist → viral_kicks로 대체
```python
# viral_kicks를 shotlist 형태로 변환
"[0-5s] Kick 1: 빠르게 전환되는 로고들을..."
```
**문제**: 실제 씬 분할이 아닌 킥 포인트 기반

---

## 3. 컨설팅 요청 범위

### Priority 1: VDG 파이프라인 scenes 생성
- LLM 프롬프트에서 `scenes` 생성 강제
- 또는 CV Pass에서 씬 분할 수행
- `SceneLLM` 스키마 활용 (이미 정의됨)

### Priority 2: Director Pack 테이블 설계 및 저장
```sql
CREATE TABLE director_packs (
  id UUID PRIMARY KEY,
  node_id UUID REFERENCES remix_nodes(id),
  invariant JSONB,     -- 핵심 유지
  variable JSONB,      -- 변주 가능
  checkpoints JSONB,   -- 촬영 체크포인트
  created_at TIMESTAMP
);
```

### Priority 3: capsule_brief 필드 채우기
- `shotlist`: 실제 씬 기반 샷 설명
- `do_not`: 위험 요소 / 피해야 할 것
- `hook_script`: 훅 스크립트

---

## 4. 첨부 파일

| 파일 | 설명 |
|------|------|
| `goodworkmb_gemini_analysis_FULL.json` | DB 원본 전체 |
| `goodworkmb_api_response.json` | API 응답 |

---

## 5. 연락처

- 프로젝트 오너: Ted
- 이메일: [추가 필요]
