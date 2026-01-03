# Data Sources + O2O 운영 구조 (최신)

**작성**: 2026-01-07

---

## 1) Outlier 수집 (외부 구독 사이트)

### 입력 방식
- 관리자 **수동 링크 입력** + 외부 구독 플랫폼 **주기적 크롤링**
- **우선순위 플랫폼**: TikTok, Instagram
- 수집 필드(최소): URL, 업로드일, 조회수, 플랫폼, 카테고리

### 표준화
- `outlier_items` 테이블에 저장
- Parent 후보 필터링: 조회수/성장률/카테고리 기준
- 시트 연동: `VDG_Outlier_Raw`에 동기화 (수동 검토 가능)

### 파이프라인 단계
1. **수집**: 관리자 수동 입력 또는 외부 소스에서 원본 데이터 로드
2. **정규화**: 플랫폼/카테고리/시간대 표준화
3. **중복 제거**: URL, 작성자, 업로드일 기준
4. **우선순위 스코어링**: 성장률/조회수/최근성
5. **영상 해석(코드)**: 구조/패턴 스키마 → **NotebookLM(Pattern Engine)** 저장
6. **Parent 후보 등록**: 후보 리스트 확정
7. **Pattern 합성(기본)**: NotebookLM Pattern Engine으로 불변 규칙 + 변주 포인트 합성 (DB-wrapped)
8. **Opal 템플릿 시드(선택)**: Node/Template 시드 생성 → DB 래핑

### 주기
- 1일 1회 (초기)
- 필요 시 6시간 주기까지 확대

### 주의
- 크롤링 정책/약관 준수
- 개인정보/저작권 이슈 최소화
- 불확실한 항목은 **수동 CSV 입력**으로 보완

### CSV 수동 입력 (스크립트)
외부 구독 사이트에서 CSV를 내려받는 경우, 아래 스크립트로 즉시 적재합니다.

```bash
python backend/scripts/ingest_outlier_csv_db.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_outlier_csv.py --csv /path/to/outliers.csv --source-name "ProviderName"
```

필수/권장 컬럼(헤더명은 유사어 허용):
- `source_url`, `title`는 필수
- `platform`, `category`, `views`, `growth_rate`, `author`, `posted_at`는 선택

`ingest_outlier_csv_db.py`는 DB(SoR)에 적재하며, 필요 시 `sync_outliers_to_sheet.py`로 `VDG_Outlier_Raw`에 동기화합니다.  
`ingest_outlier_csv.py`는 **시트 직접 입력**(운영 보조) 용도로만 사용합니다.

### CSV 자동 수집 (옵션)
구독 사이트에서 CSV 다운로드 URL이 제공되는 경우:
```bash
python backend/scripts/pull_provider_csv.py --config backend/provider_sources.json
```
`backend/provider_sources.sample.json`을 참고해 `provider_sources.json`을 구성합니다.
로컬 테스트는 `local_path`로 CSV 파일 경로를 지정할 수 있습니다.

### 관리자 수동 입력 (API)
관리자가 직접 링크를 입력하는 경우:
```
POST /api/v1/outliers/items/manual
```
수동 입력 후 **Parent 승격**을 거쳐 RemixNode를 생성하고, 영상 해석을 실행합니다.

### DB → Sheet 동기화 (수동 입력 연동)
API로 등록된 `outlier_items`를 Evidence Loop 시트에 반영:
```bash
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
```
기본 매핑: `pending → new`, `selected → candidate`, `rejected → ignored`, `promoted → promoted`.

### 영상 해석 단계 (옵션)
- Parent 승격 이후 `/api/v1/remix/{node_id}/analyze` 호출 (Admin only)
- 분석 결과는 Pattern 합성/클러스터링 입력으로 사용 (Gemini 3.0 Pro 기반 코드 분석 우선)
  - Admin 범위: `role=admin` 또는 `SUPER_ADMIN_EMAILS` 환경변수에 포함된 이메일

### Outlier 클러스터링 (기본)
분석 스키마 기반 유사도 클러스터링으로 **패턴 묶음**을 만듭니다.
NotebookLM은 **Pattern Engine 기본**으로 사용하며, 결과는 반드시 **DB(Notebook Library)**에 저장된 후 활용합니다.
패턴 경계(cluster_id)는 **VDG/DB 기준선**으로 고정합니다.
최종 후보 확정은 **DB/규칙 기반 스코어링**으로 진행합니다.

### 수집 필드 권장(상세)
| 필드 | 설명 |
| --- | --- |
| source_name | 구독 플랫폼 이름 |
| source_url | 원본 링크 |
| collected_at | 수집 시각 |
| platform | tiktok / instagram |
| category | beauty / meme 등 |
| title | 제목 |
| views | 조회수 |
| growth_rate | 성장률(가능 시) |
| author | 크리에이터 |
| posted_at | 업로드 시각 |
---

### Progress CSV 수동 입력 (성과 추적)
성과 데이터를 CSV로 확보한 경우, 아래 스크립트로 `VDG_Progress`에 적재합니다.

```bash
python backend/scripts/ingest_progress_csv.py --csv /path/to/progress.csv
```

필수/권장 컬럼(헤더명은 유사어 허용):
- `variant_id`는 필수
- `parent_id`, `variant_name`, `date`, `views`, `engagement_rate`, `retention_rate`, `confidence_score`, `status`는 선택

`parent_id`가 없으면 `variant_id`에서 `parent_xxx` 패턴을 추출해 자동 매핑합니다.

## 2) O2O 캠페인 타입 (Phase 2+)
> MVP는 **타입 게이팅(UI/표시)**까지만 제공하며, 모집/선정/배송/방문 운영은 Phase 2+에서 활성화됩니다.

### 즉시형 (instant)
- 브랜드 가이드 기반 즉시 촬영
- 승인 후 리워드 지급

### 방문형 (onsite)
- GPS 인증 필수
- 위치 인증 후 촬영

### 배송형 (shipment)
- 신청 → 선정 → 배송 → 촬영
- 단계별 상태 관리 필요

---

## 3) O2O 운영 데이터 흐름 (Phase 2+)
```
캠페인 등록 → O2O Sheet 갱신 → Earn/Shoot UI 게이팅
→ 신청/상태 변화 → O2O Applications Sheet 반영
```

---

## 4) Outlier → O2O 캠페인 연동 [NEW 2024-12-30]

### campaign_eligible 필드
아웃라이어 승격 시 O2O 캠페인 후보로 등록할 수 있습니다.

**DB 스키마**
```sql
outlier_items.campaign_eligible  -- boolean, default=False
```

**승격 옵션**
| 버튼 | campaign_eligible | 용도 |
|------|-------------------|------|
| `[승격]` | `False` | 일반 RemixNode 생성 (VDG 분석용) |
| `[체험단 선정]` | `True` | RemixNode + O2O 캠페인 후보군 등록 |

**API**
```
POST /api/v1/outliers/items/{item_id}/promote
Body: { "campaign_eligible": true }
```

**활용 (Phase 2+)**
- `campaign_eligible=True`인 아이템 목록 조회
- O2O 캠페인 생성 시 후보군으로 자동 포함
- 체험단 모집/선정 워크플로우 연계

---

## 5) Evidence Loop와 결합
- VDG 결과가 **O2O 추천 조건**으로 사용됨
- Evidence Table 기준 상위 구조에 캠페인 매칭
- O2O 성과는 다음 Depth 실험에 피드백
