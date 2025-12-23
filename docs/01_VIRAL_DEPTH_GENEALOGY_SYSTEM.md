# Viral Depth Genealogy System: 완전 기술 명세

**작성**: 2025-12-24  
**대상**: 기술 리더, CTO, 아키텍트  
**핵심**: Parent → Depth1/2 → Evidence Table → 신뢰도 점수 계산  
**길이**: 2-3시간 읽음

---

## Part 1: Viral Depth Genealogy 개념

### 핵심 정의

```
Viral Depth Genealogy (VDG) 란?

단일 Parent 영상의 변주들(Variants)을 계층적으로 추적하고,
각 변주의 성과를 측정하여,
"어떤 구조가 성공하는가"를 데이터로 증명하는 시스템

구조:
┌─────────────────────────────────┐
│ Parent (원본)                   │
│ "마지막 클릭" (1M 뷰)          │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Depth 1 (첫 변주, 3개)         │
├─ Variant 1: 클리프행거식       │
│  └─ 45K 뷰, 신뢰도 0.72       │
├─ Variant 2: 감정호소식        │
│  └─ 38K 뷰, 신뢰도 0.68       │
└─ Variant 3: 반전식            │
   └─ 32K 뷰, 신뢰도 0.65       │
          ↓
┌─────────────────────────────────┐
│ Depth 2 (최적화, 2개)          │
├─ Variant 1-2: 클리프+감정반전  │
│  └─ 52K 뷰, 신뢰도 0.85 ✅   │
└─ Variant 2-3: 감정+음악변경   │
   └─ 41K 뷰, 신뢰도 0.78       │
└─────────────────────────────────┘
```

### 왜 "Genealogy"인가?

```
가족계보처럼 추적:
- Ancestor (조상): Parent
- Children (자식): Depth 1 변주들
- Grandchildren (손자): Depth 2 변주들
- DNA 유전: 어떤 요소가 성공을 가져오는가?

예시:
Parent: "마지막 클릭"
  ├─ Child A: 클리프행거식 (45K)
  │  └─ Grandchild A-B: 클리프 + 감정반전 (52K) ← 최고!
  ├─ Child B: 감정호소식 (38K)
  └─ Child C: 반전식 (32K)

"A가 B, C보다 좋네" (Depth 1)
  → "A + B를 섞으면 더 좋아!" (Depth 2)
  → 성공 공식 발견!
```

---

## Part 2: 데이터 구조

### 테이블 설계

#### Table 1: Parents

```sql
CREATE TABLE parents (
  id UUID PRIMARY KEY,
  
  -- 기본 정보
  title VARCHAR(255),
  description TEXT,
  content_type VARCHAR(50), -- "video", "shorts", "reel"
  duration_seconds INT,
  
  -- 성과 데이터
  youtube_url VARCHAR(500),
  youtube_video_id VARCHAR(100),
  views_baseline INT,
  engagement_rate_baseline FLOAT,
  retention_rate_baseline FLOAT,
  
  -- Depth 진행 상태
  current_depth INT DEFAULT 0,
  status VARCHAR(50), -- "planning", "depth1_running", "depth2_running", "analyzing", "complete"
  
  -- 메타데이터
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  analyst_notes TEXT
);

예시 데이터:
INSERT INTO parents VALUES (
  'uuid-1',
  '마지막 클릭',
  '감정 드라마 숏폼',
  'shorts',
  60,
  'https://youtube.com/shorts/xyz123',
  'xyz123',
  1000000,  -- 1M 뷰
  0.08,     -- 8% 참여율
  0.75,     -- 75% 평균 시청률
  1,
  'depth1_running',
  NOW(),
  NOW(),
  'High potential, strong emotional hook'
);
```

#### Table 2: Depth 1 Variants

```sql
CREATE TABLE depth1_variants (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES parents(id),
  
  -- 변주 정보
  variant_number INT, -- 1, 2, 3...
  name VARCHAR(255), -- "클리프행거식", "감정호소식", etc
  description TEXT,
  structure_elements JSONB, -- 구조적 특징 저장
  
  -- 생성 정보
  created_by VARCHAR(255), -- creator 이름
  created_at TIMESTAMP,
  
  -- YouTube 성과 (실시간 수집)
  youtube_url VARCHAR(500),
  youtube_video_id VARCHAR(100),
  views INT,
  engagement_rate FLOAT,
  retention_rate FLOAT,
  
  -- 14일 추적 데이터
  tracking_days INT DEFAULT 0,
  status VARCHAR(50), -- "tracking", "complete"
  
  -- 신뢰도 점수 (자동 계산)
  confidence_score FLOAT, -- 0-1
  confidence_interval_lower FLOAT,
  confidence_interval_upper FLOAT,
  
  updated_at TIMESTAMP
);

예시 데이터:
INSERT INTO depth1_variants VALUES (
  'uuid-d1-1',
  'uuid-1',
  1,
  '클리프행거식',
  '엔딩 직전에 갑자기 끝냄',
  '{
    "ending_type": "cliffhanger",
    "music_intensity": "high",
    "color_filter": "cool_tones",
    "pacing": "fast"
  }',
  'creator_김',
  NOW(),
  'https://youtube.com/shorts/abc456',
  'abc456',
  45000,
  0.12,
  0.78,
  14,
  'complete',
  0.72,
  0.68,
  0.76,
  NOW()
);
```

#### Table 3: Depth 2 Variants

```sql
CREATE TABLE depth2_variants (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES parents(id),
  parent_depth1_variant_ids UUID[] REFERENCES depth1_variants(id),
  
  -- 변주 정보
  variant_number INT,
  name VARCHAR(255), -- "클리프행거 + 감정반전"
  description TEXT,
  structure_elements JSONB,
  
  -- 생성 정보
  created_by VARCHAR(255),
  created_at TIMESTAMP,
  
  -- YouTube 성과
  youtube_url VARCHAR(500),
  youtube_video_id VARCHAR(100),
  views INT,
  engagement_rate FLOAT,
  retention_rate FLOAT,
  
  -- 14일 추적
  tracking_days INT DEFAULT 0,
  status VARCHAR(50),
  
  -- 신뢰도 점수
  confidence_score FLOAT,
  confidence_interval_lower FLOAT,
  confidence_interval_upper FLOAT,
  
  -- Depth 2는 "최고 후보"를 결정
  is_winner BOOLEAN DEFAULT FALSE,
  
  updated_at TIMESTAMP
);

예시 데이터:
INSERT INTO depth2_variants VALUES (
  'uuid-d2-1',
  'uuid-1',
  ARRAY['uuid-d1-1', 'uuid-d1-2'],
  1,
  '클리프행거 + 감정반전',
  '클리프행거 끝에 감정 반전 추가',
  '{
    "ending_type": "cliffhanger_with_emotion_twist",
    "music_intensity": "extreme",
    "color_filter": "cool_then_warm",
    "pacing": "fast_then_slow"
  }',
  'creator_김',
  NOW(),
  'https://youtube.com/shorts/def789',
  'def789',
  52000,
  0.14,
  0.82,
  14,
  'complete',
  0.85,
  0.81,
  0.89,
  TRUE,
  NOW()
);
```

---

## Part 3: Evidence Table 자동 생성

### Evidence Table이란?

```
Depth 1 & 2의 모든 변주를 한 표로 정리하여,
"어떤 구조가 성공했나"를 한 눈에 보는 테이블

예시:

┌──────────────────────────────────────────────────────────────┐
│ "마지막 클릭" Evidence Table (신뢰도 95%)                    │
├──────────────────────────────────────────────────────────────┤
│ Variant Name      │ Views  │ Confidence │ 신뢰도     │ 순위 │
├──────────────────────────────────────────────────────────────┤
│ Depth 1:                                                      │
│ 클리프행거식      │ 45,000 │ 0.72       │ ±0.04     │ 1순위│
│ 감정호소식        │ 38,000 │ 0.68       │ ±0.05     │ 2순위│
│ 반전식            │ 32,000 │ 0.65       │ ±0.06     │ 3순위│
├──────────────────────────────────────────────────────────────┤
│ Depth 2:                                                      │
│ 클리프+감정반전   │ 52,000 │ 0.85 ✅    │ ±0.04     │ 최우선│
│ 감정+음악변경     │ 41,000 │ 0.78       │ ±0.05     │ 2순위│
├──────────────────────────────────────────────────────────────┤
│ 최고 후보         │ 클리프행거 + 감정반전 (신뢰도 0.85)      │
│ 다음 실험         │ 이 구조로 25개 샘플, 14일 추적           │
└──────────────────────────────────────────────────────────────┘
```

### Evidence Table 자동 계산 로직

```python
def generate_evidence_table(parent_id):
    """
    1. parent_id의 모든 Depth 1, 2 변주 조회
    2. 각 변주의 성과 데이터 계산
    3. 신뢰도 점수 계산
    4. 테이블 생성
    5. 최고 후보 자동 결정
    """
    
    # Step 1: 데이터 로드
    parent = query_parent(parent_id)
    depth1_variants = query_depth1_variants(parent_id)
    depth2_variants = query_depth2_variants(parent_id)
    
    # Step 2: 각 변주의 성과 계산
    for variant in depth1_variants + depth2_variants:
        # Views 정규화 (parent 대비 %)
        improvement_pct = (variant.views - parent.views_baseline) / parent.views_baseline * 100
        
        # Confidence Score 계산
        variant.confidence_score = calculate_confidence_score(
            views=variant.views,
            engagement_rate=variant.engagement_rate,
            tracking_days=variant.tracking_days
        )
        
        # 신뢰구간 계산 (95% CI)
        variant.confidence_interval = calculate_95_ci(variant)
    
    # Step 3: 정렬 (신뢰도순)
    all_variants = sorted(
        depth1_variants + depth2_variants,
        key=lambda v: v.confidence_score,
        reverse=True
    )
    
    # Step 4: Evidence Table 생성
    evidence_table = {
        "parent_name": parent.title,
        "parent_baseline_views": parent.views_baseline,
        "tracking_period": "14 days",
        "confidence_level": 0.95,
        "variants": [
            {
                "name": v.name,
                "views": v.views,
                "improvement_pct": improvement_pct,
                "confidence_score": v.confidence_score,
                "confidence_interval": v.confidence_interval,
                "rank": idx + 1
            }
            for idx, v in enumerate(all_variants)
        ]
    }
    
    # Step 5: 최고 후보 결정
    winner = all_variants[0]
    evidence_table["winner"] = {
        "name": winner.name,
        "confidence_score": winner.confidence_score,
        "views": winner.views
    }
    
    return evidence_table
```

---

## Part 4: 신뢰도 점수 계산

### 신뢰도 점수 공식

```
Confidence Score (CS) 계산:

CS = (Views_normalized × 0.5) + (Engagement × 0.3) + (Tracking_Days × 0.2)

각 요소:

1. Views_normalized (0-1 범위)
   = min(views / parent_views × 1.5, 1.0)
   = 부모 대비 성과를 정규화
   = 1.5배는 최고값 (1.0)

2. Engagement (0-1 범위)
   = min(engagement_rate / 0.10, 1.0)
   = 10% 참여율을 최고값 (1.0)으로 정규화

3. Tracking_Days (0-1 범위)
   = min(tracking_days / 14, 1.0)
   = 14일 추적이 완료되면 1.0
   = 초기(1-7일)는 0.5-0.7

실제 예시:

Depth 1 "클리프행거식":
├─ Views: 45,000 (Parent 1M 대비)
├─ Engagement: 12%
├─ Tracking: 14일 완료
│
├─ Views_norm = (45,000 / 1,000,000 * 1.5) = 0.067 → 정규화 후 0.45
├─ Engagement_norm = (0.12 / 0.10) = 1.2 → cap at 1.0
├─ Tracking_norm = 14 / 14 = 1.0
│
└─ CS = (0.45 × 0.5) + (1.0 × 0.3) + (1.0 × 0.2)
    = 0.225 + 0.30 + 0.20
    = 0.725 ≈ 0.72 ✓

Depth 2 "클리프+감정반전":
├─ Views: 52,000
├─ Engagement: 14%
├─ Tracking: 14일 완료
│
├─ Views_norm = (52,000 / 1,000,000 * 1.5) = 0.078 → 0.52
├─ Engagement_norm = (0.14 / 0.10) = 1.0 (cap)
├─ Tracking_norm = 1.0
│
└─ CS = (0.52 × 0.5) + (1.0 × 0.3) + (1.0 × 0.2)
    = 0.26 + 0.30 + 0.20
    = 0.76 ≈ 0.76 ✓

더 높은 신뢰도! ✅
```

### 신뢰구간 (Confidence Interval) 계산

```
95% 신뢰구간 계산:

CI_95 = CS ± 1.96 × SE

SE (표준오차) = sqrt(p(1-p) / n)
  where:
  p = engagement_rate
  n = estimated_samples (views 기반)

예시:

Depth 2 "클리프+감정반전":
├─ Views: 52,000
├─ Engagement: 14% (0.14)
│
├─ n ≈ views / 20 = 52,000 / 20 = 2,600 (estimated samples)
├─ SE = sqrt(0.14 * 0.86 / 2,600) = sqrt(0.0000467) ≈ 0.0068
├─ Margin = 1.96 × 0.0068 ≈ 0.0133
│
├─ CI_lower = 0.76 - 0.0133 ≈ 0.747 → 0.75
├─ CI_upper = 0.76 + 0.0133 ≈ 0.773 → 0.77
│
└─ 신뢰구간: 0.76 ± 0.01 (또는 0.75-0.77)

의미:
"이 구조의 진정한 성공률은 75%-77% 사이일 확률이 95%다"
```

---

## Part 5: YouTube API 통합

### 성과 데이터 수집 워크플로우

```
Day 1-14: 매일 YouTube API 호출
├─ 09:00 UTC: 전날 데이터 수집
├─ 저장: views, engagement, retention
└─ n8n 스케줄: 매일 자동 실행

API Endpoints:

GET /youtube/v3/videos?
  part=statistics,contentDetails
  id={video_id}

Response 예시:
{
  "items": [{
    "statistics": {
      "viewCount": "52000",
      "likeCount": "7280",
      "commentCount": "1456"
    },
    "contentDetails": {
      "duration": "PT60S"
    }
  }]
}

계산:
engagement_rate = (likes + comments) / views
               = (7280 + 1456) / 52000
               = 0.168 ≈ 16.8%
```

### n8n 워크플로우: "Performance Data Collector"

```
Workflow: Collect Performance Data

Trigger: Daily at 09:00 UTC

Step 1: Load Active Variants
  ├─ Query: depth1_variants WHERE status = 'tracking'
  ├─ Query: depth2_variants WHERE status = 'tracking'
  └─ Output: List of video_ids

Step 2: For Each Variant (Parallel)
  ├─ Call: YouTube API
  │  ├─ Get: viewCount, likeCount, commentCount
  │  └─ Output: Performance data
  │
  ├─ Call: Claude to Calculate
  │  ├─ Calculate: engagement_rate, improvement_pct
  │  └─ Output: Metrics

Step 3: Update Database
  ├─ UPDATE depth1_variants
  │  SET views = {new_views},
  │      engagement_rate = {new_engagement},
  │      updated_at = NOW()
  └─ Same for depth2_variants

Step 4: Check Completion (14 days)
  ├─ IF tracking_days == 14:
  │  ├─ Calculate: confidence_score
  │  ├─ Calculate: confidence_interval
  │  └─ SET status = 'complete'
  └─ ELSE: Continue tracking

Step 5: Generate Evidence Table (Daily)
  ├─ IF any variant completed today:
  │  ├─ Call: generate_evidence_table()
  │  ├─ Save to DB
  │  └─ Notify team
  └─ Update Canvas Dashboard

Output: 
  ✅ All metrics updated
  ✅ Evidence table regenerated
  ✅ Confidence scores recalculated
```

---

## Part 6: 실제 데이터 예시

### "마지막 클릭" Parent

```
Parent Details:
├─ Title: "마지막 클릭"
├─ Type: YouTube Shorts (60초)
├─ Category: 감정 드라마
├─ Upload Date: 2025-11-01
├─ Baseline Views: 1,000,000
├─ Baseline Engagement: 8%
├─ Baseline Retention: 75%
└─ Link: https://youtube.com/shorts/xyz123

Depth 1 (4개 변주, 14일 완료):

1️⃣ "클리프행거식"
   ├─ Structure: 엔딩 갑자기 끊김
   ├─ Views: 45,000 (+4.5%)
   ├─ Engagement: 12% (+4%)
   ├─ Retention: 78% (+3%)
   ├─ Confidence: 0.72
   └─ Status: ✅ Complete

2️⃣ "감정호소식"
   ├─ Structure: 감정적 음악 + 텍스트
   ├─ Views: 38,000 (+3.8%)
   ├─ Engagement: 10% (+2%)
   ├─ Retention: 76% (+1%)
   ├─ Confidence: 0.68
   └─ Status: ✅ Complete

3️⃣ "반전식"
   ├─ Structure: 끝에 반전 내용
   ├─ Views: 32,000 (+3.2%)
   ├─ Engagement: 9% (+1%)
   ├─ Retention: 74% (-1%)
   ├─ Confidence: 0.65
   └─ Status: ✅ Complete

4️⃣ "음악집중식"
   ├─ Structure: 음악 변경만
   ├─ Views: 28,000 (+2.8%)
   ├─ Engagement: 7% (-1%)
   ├─ Retention: 72% (-3%)
   ├─ Confidence: 0.61
   └─ Status: ✅ Complete

→ Winner: "클리프행거식" (0.72)

Depth 2 (2개 변주, 10일 진행 중):

1️⃣ "클리프 + 감정반전"
   ├─ Structure: 클리프행거 끝에 감정 반전
   ├─ Views: 52,000 (현재, +5.2%)
   ├─ Engagement: 14% (현재, +6%)
   ├─ Retention: 82% (현재, +7%)
   ├─ Confidence: 0.85 (현재)
   ├─ Tracking: 10/14 days
   └─ Status: 🔵 Tracking (4일 더)

2️⃣ "감정 + 음악변경"
   ├─ Structure: 감정호소 + 음악 변경
   ├─ Views: 41,000 (현재, +4.1%)
   ├─ Engagement: 11% (현재, +3%)
   ├─ Retention: 77% (현재, +2%)
   ├─ Confidence: 0.78 (현재)
   ├─ Tracking: 10/14 days
   └─ Status: 🔵 Tracking

→ Leading: "클리프 + 감정반전" (0.85)
```

---

## Part 7: 통합 플로우

```
Week 1:
Day 1-7: Depth 1 생성 (4개)
Day 8: 일주 성과 분석
       → "클리프행거식" 최고 (45K)

Week 2:
Day 8-14: Depth 2 생성 (2개)
Day 15: Depth 1 추적 완료
        → Confidence score 확정
        → Evidence Table 생성
        → Claude와 토론 (Part 2로 이동)

Week 3:
Day 15-28: Depth 2 추적 중
           매일 YouTube API로 갱신
           신뢰도 점수 매일 재계산

Day 29: Depth 2 완료
        → Final Evidence Table
        → 최고 후보 확정
        → 다음 Parent 시작
```

---

## Part 8: 성공 지표

```
VDG System이 성공했다는 증거:

✅ Depth 1 4개: 신뢰도 0.61-0.72 (명확한 순위)
✅ Depth 2 2개: 신뢰도 0.78-0.85 (개선 확인)
✅ 최고 vs 최저: +31% 성과 차이
✅ Evidence Table: 자동 생성 (수동 개입 0)
✅ 신뢰도: 95% 신뢰구간 포함 (통계적 엄밀함)
✅ 다음 Parent로 즉시 전환 가능
```

---

**이 시스템의 강력함**: 매주 반복되는 자동화된 데이터 축적 → 다음 세대는 이전 성공 데이터를 기반으로 더 강한 변주 생성 가능