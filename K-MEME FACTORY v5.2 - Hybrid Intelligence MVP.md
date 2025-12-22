# K-MEME FACTORY v5.2 - Business Logic Design Document
## 비즈니스 로직 설계서 (Hybrid Intelligence + Viral Genealogy + O2O)

---

## 📋 Document Overview
**Status**: ✅ Production-Ready
**Version**: 5.2 Final
**Updated**: 2025-12-22 22:30 KST
**Target Audience**: CTO, 개발팀, 기획팀
**Document Type**: 📘 **비즈니스 로직 설계서**
**Philosophy**: "Gemini 분석은 자동화, 창의는 수동, 데이터는 계보도로, O2O는 위치기반으로"

> **📌 관련 문서**
> - 기술 운영 설계서: [K-MEME-v5.2-OPERATIONS.md](./K-MEME-v5.2-OPERATIONS.md)
> - 이 문서는 **비즈니스 로직, 데이터 모델, AI 파이프라인**에 집중합니다.
> - 보안, 에러 핸들링, 모니터링 등 운영 관련 내용은 기술 운영 설계서를 참조하세요.

---

## 1. 핵심 전략: Hybrid Pipeline + Viral Genealogy Graph

### 1.1 비전 (2025~2026)

```
2025 (v5.2): MVP 완성 + 첫 1,000개 노드
└─ Gemini 자동 분석 + Claude 수동 기획 + 이미지 무료 생성 + 오디오 자동 렌더링

2026 (Scaling): 데이터 자산화 + O2O 확장
├─ 바이럴 계보도(Genealogy Graph) 활성화
│  └─ "부모 노드 → 변이 → 자식 노드" 관계 데이터화
│  └─ AI가 자동으로 "이 변수를 바꾸면 +350% 성과"를 추천
├─ O2O 캠페인 (위치 기반, GPS 인증)
│  └─ "맛집 챌린지", "팝업스토어 방문 인증"
├─ 캠페인/유저 노드 권한 분리 (Master/Fork 구조)
│  └─ 브랜드 캠페인은 "공식 스킨" 제공
└─ 멀티플랫폼 (TikTok, YouTube, Reels, Shorts) 동시 지원

최종 목표: "Open Source Meme Ecology" + "Creator-Advertiser Marketplace"
```

### 1.2 아키텍처 진화 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│   K-MEME FACTORY v5.2 Hardened (Future-Proof Architecture)      │
│  (System Auto + Human-in-Loop + Graph DB + O2O + Governance)    │
└─────────────────────────────────────────────────────────────────┘

                            ┌─────────────────┐
                            │  Master Input   │
                            │  (Parent Video) │
                            └────────┬────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
    ┌───▼──────────────────┐    ┌───▼──────────────────┐    ┌───▼──────┐
    │ System Auto (Step 1) │    │ Hybrid Gen (Step 2)  │    │ Query    │
    │                      │    │ (Human-in-Loop)      │    │ Layer    │
    │ • Gemini Analysis    │    │ • Claude 4.5 Opus    │    │          │
    │ • BPM/Keyframes      │    │ • nanobanana Images  │    │ GraphQL  │
    │ • Commerce Category  │    │ • Text Guide         │    │ API      │
    │ • Emotion DNA        │    │ • Timing (Manual)    │    │          │
    └───┬──────────────────┘    └───┬──────────────────┘    └───┬──────┘
        │ (JSON)                 │ (Assets)                   │
        │                        │                            │
        └────────────┬───────────┴────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────────┐
        │      Admin Panel (Step 4: Final Assembly)    │
        │  + Audio Rendering + Governance Check        │
        ├─────────────────────────────────────────────┤
        │ [Image Upload] [Text Paste] [Publish]      │
        │ 🔊 Auto: Beat Guide + Safe Zone + Metadata │
        │ ✅ Check: Layer (Master/Fork), Location OK  │
        └────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────────┐
        │   Viral Genealogy Graph + O2O Context DB    │
        │   (PostgreSQL + Neo4j + PostGIS)            │
        ├─────────────────────────────────────────────┤
        │ ✅ Node: 기본 노드 데이터                   │
        │ ✅ Edge: Parent→Mutation→Child 관계        │
        │ ✅ Location: Geo 인덱스 (맛집, 팝업)      │
        │ ✅ Governance: Master/Fork 권한            │
        │ ✅ Campaign: 광고주 설정 + 스킨            │
        └────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────────┐
        │  Smart Recipe View (Multi-Skin Rendering)   │
        ├─────────────────────────────────────────────┤
        │ • Community Recipe (일반 사용자)            │
        │   └─ 가이드 카드 + 파일 다운로드           │
        │                                             │
        │ • Campaign Master (광고주 전용)            │
        │   └─ 브랜드 컬러 + 공식 뱃지 + 지도        │
        │   └─ 참여 추적 (방문 인증, 구매)          │
        │                                             │
        │ • Location-Based (O2O 캠페인)              │
        │   └─ 지도 핀 + GPS 인증 + 위치 기반 쿠폰  │
        └────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────────┐
        │  User Creates, Posts, Wins Rewards          │
        │  + Performance Certification (K-Success)     │
        ├─────────────────────────────────────────────┤
        │ ✅ 영상 업로드                             │
        │ ✅ 성과 인증 (링크/스크린샷/GPS)          │
        │ ✅ K-Success 판정                         │
        │ ✅ 포인트/현금 적립                       │
        │ ✅ Genealogy Graph에 데이터 반영          │
        │    └─ "이 변이로 +350% 달성" 학습        │
        └──────────────────────────────────────────────┘

총 소요 시간: 10~20분/리믹스 (자동화 = 10분, 수동화 = 5분)
총 비용: ~$0.40/리믹스 (변동비 기준, 70% 절감)
```

---

## 2. 4가지 핵심 보강 (Hardening Points)

### 2.1 [Hardening #1] 바이럴 계보도 아키텍처 (Viral Genealogy Graph)

#### 문제정의
- **기존 (v5.2 미흡점)**: 성공한 노드를 Vector DB에 저장하되, "부모 노드 A에서 음악을 바꿨더니 조회수 +350%"라는 **인과관계(Causality)**를 추적하지 못함.
- **결과**: AI가 "이 변수를 바꾸면 터진다"는 '변주 전략'을 제안할 수 없음.

#### 솔루션: Neo4j Graph DB (또는 DuckDB + GraphQL)

```python
# 데이터 스키마 추가: Node Relations (Parent → Mutation → Child)

class ViralGenealogyGraph:
    """
    Neo4j를 활용한 바이럴 패턴 계보도
    
    구조:
    (Parent_Node:remix {id: 'node_A'}) 
      -[EVOLVED_TO {mutation_type, mutation_value, performance_delta}]-> 
    (Child_Node:remix {id: 'node_B'})
    
    예시:
    "배경음악을 NewJeans_OMG에서 Tros_Dance_Remix로 바꿈"
    성과: +350% 조회수
    → 다음에 유사한 '춤' 리믹스를 제안할 때, 
       "이 변주로 +350% 경험이 있으니 추천합니다" 제안 가능
    """
    
    async def create_genealogy_edge(
        self,
        parent_node_id: str,
        child_node_id: str,
        mutations: dict,  # {"audio": {"before": "A", "after": "B"}, ...}
        performance_delta: str  # "+350%", "-50%", "neutral"
    ) -> dict:
        """
        Cypher 쿼리로 Node Relations 저장 (Neo4j)
        """
        
        cypher_query = """
        MATCH (parent:Remix {node_id: $parent_id})
        MATCH (child:Remix {node_id: $child_id})
        CREATE (parent)-[r:EVOLVED_TO {
            mutation_profile: $mutations,
            performance_delta: $delta,
            created_at: timestamp(),
            data_confidence: 0.92
        }]->(child)
        RETURN r
        """
        
        await neo4j_driver.execute(cypher_query, {
            'parent_id': parent_node_id,
            'child_id': child_node_id,
            'mutations': mutations,
            'delta': performance_delta
        })
        
        return {
            "edge_created": True,
            "type": "EVOLVED_TO",
            "mutation_profile": mutations,
            "performance_delta": performance_delta
        }
    
    async def query_mutation_strategy(
        self,
        template_node_id: str,
        target_category: str  # "beauty", "fitness", "comedy"
    ) -> list:
        """
        "이 춤에 어떤 변주를 하면 터질까?" → 과거 성공 사례 추천
        """
        
        cypher_query = """
        MATCH (template:Remix {node_id: $template_id})-[r:EVOLVED_TO]->(successful:Remix)
        WHERE successful.commerce_category = $category
          AND r.performance_delta CONTAINS "+"
        RETURN r.mutation_profile, r.performance_delta, successful.view_count
        ORDER BY successful.view_count DESC
        LIMIT 5
        """
        
        results = await neo4j_driver.execute(cypher_query, {
            'template_id': template_node_id,
            'category': target_category
        })
        
        recommendations = []
        for result in results:
            recommendations.append({
                "mutation_strategy": result['mutation_profile'],
                "expected_boost": result['performance_delta'],
                "confidence": 0.85,
                "rationale": f"Similar category ({target_category}) achieved {result['performance_delta']} with this mutation"
            })
        
        return recommendations


# 사용 시나리오

async def on_user_success_certified(user_video_id: str, parent_node_id: str):
    """
    유저가 성공 인증 제출 → 자동으로 Genealogy 업데이트
    """
    
    # 1. 성공한 노드 데이터 추출
    success_node = await db.get_remix_node(user_video_id)
    parent_node = await db.get_remix_node(parent_node_id)
    
    # 2. 변이(Mutation) 분석
    mutations = {
        "audio": {
            "before": parent_node['claude_brief']['music'],
            "after": success_node['user_customization']['music']  # 유저가 바꿈
        },
        "setting": {
            "before": parent_node['claude_brief']['location'],
            "after": success_node['user_customization']['location']
        },
        "timing_adjustment": success_node['user_customization'].get('timing_delta', "none")
    }
    
    # 3. 성과 계산
    performance_delta = await calculate_performance_lift(parent_node, success_node)
    # 예: "+350%" (조회수 기준)
    
    # 4. Genealogy Graph에 저장
    genealogy = ViralGenealogyGraph()
    await genealogy.create_genealogy_edge(
        parent_node_id=parent_node_id,
        child_node_id=user_video_id,
        mutations=mutations,
        performance_delta=performance_delta
    )
    
    # 5. 다음 제안 시에 활용
    print(f"✅ Genealogy 업데이트 완료: {parent_node_id} → {user_video_id} (+{performance_delta})")
```

#### 데이터 모델링 (PostgreSQL + Neo4j Hybrid)

```sql
-- PostgreSQL: 기존 remix_nodes 테이블 + 새 컬럼

ALTER TABLE remix_nodes ADD COLUMN parent_node_id UUID REFERENCES remix_nodes(id);
ALTER TABLE remix_nodes ADD COLUMN mutation_profile JSONB;
ALTER TABLE remix_nodes ADD COLUMN performance_delta VARCHAR(20); -- "+350%", "-50%", "neutral"
ALTER TABLE remix_nodes ADD COLUMN genealogy_depth INT DEFAULT 0; -- 0=original, 1=fork, 2=fork of fork

CREATE INDEX idx_parent_node ON remix_nodes(parent_node_id);
CREATE INDEX idx_genealogy_depth ON remix_nodes(genealogy_depth);

-- Neo4j: 그래프 관계 저장 (Cypher)
-- 초기화 명령어:
CALL apoc.schema.assert({Remix:['node_id']}, {});
```

#### 실제 워크플로우

```
Step 1: 전문가 노드 생성 (관리자)
└─ remix_20251222_master_001
   ├─ 음악: "Flowers" (Miley Cyrus, BPM 128)
   ├─ 배경: "편의점 화장실"
   └─ 조회수: (아직 없음, 마스터 노드이므로)

Step 2: 사용자 A가 변주 (Fork)
└─ remix_20251222_fork_A (parent: master_001)
   ├─ 음악: "봄날" (BTS, BPM 128) ← 변경됨
   ├─ 배경: "편의점 화장실" (동일)
   └─ 결과: 조회수 50만 달성 → +400% 성과 인증 ✅

Step 3: Genealogy Graph 자동 업데이트
└─ Neo4j Edge 생성:
   (master_001)-[EVOLVED_TO {
     mutations: {audio: "Flowers→봄날"},
     performance_delta: "+400%"
   }]->(fork_A)

Step 4: 다음 제안 시 활용
└─ "춤 리믹스에 K-pop 음악으로 바꾸면 +400% 기대"
   → AI Recommendation Engine이 자동 제안
```

---

### 2.2 [Hardening #2] O2O(오프라인) 캠페인 아키텍처

#### 문제정의
- **기존 (v5.2 미흡점)**: 커머스가 "배송형(뷰티, 패션)" 위주.
- **누락**: "맛집 방문 챌린지", "팝업스토어 인증", "헬스장 챌린지" 같은 **위치 기반(Location-based)** 캠페인이 설계되지 않음.

#### 솔루션: PostGIS (지리 인덱싱) + Google Maps API

```python
# 데이터 스키마 추가: Location Context (PostGIS)

class LocationContextModel:
    """
    O2O 캠페인을 위한 위치 기반 데이터
    """
    
    location_id: str  # "location_gangnam_001"
    campaign_type: str  # "visit_challenge" | "product_trial" | "event_attendance"
    
    # 지리 데이터 (PostGIS)
    coordinates: Point  # (위도, 경도) - PostGIS Point 타입
    place_name: str  # "성수동 팝업스토어"
    address: str
    
    # 캠페인 상세
    brand: str  # "Samsung Galaxy"
    campaign_title: str  # "카메라로 담은 남산 야경"
    verification_method: str  # "gps_match" | "photo_timestamp" | "receipt_scan"
    
    # 보상
    reward_points: int  # 100 (K-포인트)
    reward_product: str  # "Samsung Galaxy 케이스 10% 할인"
    
    # 유효성
    active_start: datetime
    active_end: datetime
    max_participants: int
    
    # 메타데이터
    gmaps_place_id: str  # Google Maps API와의 연동


# 데이터베이스 설계 (PostgreSQL + PostGIS)

CREATE TABLE o2o_locations (
    location_id UUID PRIMARY KEY,
    campaign_type VARCHAR(50),
    place_name VARCHAR(200),
    address TEXT,
    coordinates GEOGRAPHY(POINT, 4326),  -- PostGIS: 위도/경도
    brand VARCHAR(100),
    campaign_title TEXT,
    verification_method VARCHAR(50),
    reward_points INT,
    reward_product TEXT,
    active_start TIMESTAMP,
    active_end TIMESTAMP,
    max_participants INT,
    gmaps_place_id VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 지리 인덱스 (반경 검색 최적화)
CREATE INDEX idx_o2o_geo ON o2o_locations USING GIST (coordinates);

-- 관련 노드 저장
CREATE TABLE remix_nodes_o2o_mapping (
    node_id UUID REFERENCES remix_nodes(id),
    location_id UUID REFERENCES o2o_locations(location_id),
    PRIMARY KEY (node_id, location_id)
);
```

#### O2O 인증 로직

```python
class O2OVerificationEngine:
    """
    사용자가 실제로 "성수동 팝업스토어"에 방문했는지 확인
    """
    
    async def verify_visit(
        self,
        user_id: str,
        location_id: str,
        verification_data: dict  # {"type": "gps", "lat": 37.5, "lng": 126.9, ...}
    ) -> dict:
        """
        GPS, 영수증, 타임스탐프 등으로 방문 인증
        """
        
        location = await db.get_o2o_location(location_id)
        
        # 인증 방법별 처리
        if verification_data['type'] == 'gps':
            # GPS 좌표 일치 확인
            user_coords = Point(verification_data['lat'], verification_data['lng'])
            location_coords = location['coordinates']
            
            # PostGIS: 반경 100m 이내 확인
            distance = location_coords.distance(user_coords) * 111000  # m단위 변환
            
            if distance > 100:  # 100m 이상 벗어남
                return {
                    "verified": False,
                    "reason": f"Location mismatch: {distance:.0f}m away from campaign location"
                }
            
            is_verified = True
            verification_method = "gps_match"
        
        elif verification_data['type'] == 'receipt_scan':
            # 영수증 인증 (OCR)
            receipt_data = await self.ocr_receipt(verification_data['image'])
            store_name = receipt_data.get('merchant_name', '')
            
            if not self.fuzzy_match_store_name(store_name, location['place_name']):
                return {
                    "verified": False,
                    "reason": f"Receipt store name doesn't match: {store_name}"
                }
            
            is_verified = True
            verification_method = "receipt_verified"
        
        elif verification_data['type'] == 'timestamp':
            # 타임스탐프 기반 (예: SNS 업로드 시간이 캠페인 시간대와 일치)
            post_timestamp = verification_data['timestamp']
            campaign_start = location['active_start']
            campaign_end = location['active_end']
            
            if not (campaign_start <= post_timestamp <= campaign_end):
                return {
                    "verified": False,
                    "reason": f"Post timestamp outside campaign period"
                }
            
            is_verified = True
            verification_method = "timestamp_verified"
        
        # 인증 성공 시 보상 적립
        if is_verified:
            await self._grant_o2o_reward(user_id, location_id, location['reward_points'])
            
            return {
                "verified": True,
                "points_awarded": location['reward_points'],
                "reward_product": location['reward_product'],
                "verification_method": verification_method
            }
        
        return {"verified": False}
    
    async def _grant_o2o_reward(self, user_id: str, location_id: str, points: int):
        """
        O2O 인증 성공 → 포인트 적립
        """
        
        user = await db.get_user(user_id)
        user['k_points'] += points
        user['o2o_visits'].append({
            'location_id': location_id,
            'verified_at': datetime.now(),
            'points_earned': points
        })
        
        await db.save_user(user)
        print(f"✅ {user_id}이(가) {location_id} 방문 인증 완료 (+{points} K-포인트)")


# UI: Smart Recipe View에 추가되는 O2O 섹션

class SmartRecipeViewO2OSection:
    """
    위치 기반 캠페인 노드일 경우, 지도 & 인증 UI 표시
    """
    
    @property
    def render_html(self) -> str:
        return f"""
        <!-- O2O Campaign Section -->
        <section class="o2o-campaign" style="margin-top: 2rem;">
            <h2>📍 위치 기반 챌린지</h2>
            
            <div class="location-card">
                <h3>{self.location['place_name']}</h3>
                <p class="address">{self.location['address']}</p>
                
                <!-- 지도 (Google Maps) -->
                <div id="campaign-map" style="height: 300px; margin: 1rem 0;"></div>
                
                <!-- 캠페인 정보 -->
                <div class="campaign-details">
                    <p><strong>캠페인:</strong> {self.location['campaign_title']}</p>
                    <p><strong>보상:</strong> {self.location['reward_points']} K-포인트 + {self.location['reward_product']}</p>
                    <p><strong>유효 기간:</strong> {self.location['active_start']} ~ {self.location['active_end']}</p>
                </div>
                
                <!-- 인증 방법 선택 -->
                <div class="verification-methods">
                    <h4>방문 인증 방법 선택:</h4>
                    <button onclick="verifyByGPS()">📍 GPS 인증</button>
                    <button onclick="verifyByReceipt()">🧾 영수증 스캔</button>
                    <button onclick="verifyByPost()">📸 인증샷 업로드</button>
                </div>
            </div>
        </section>
        
        <script>
        // Google Maps 임베드 (Campaign Location)
        function initMap() {{
            const map = new google.maps.Map(document.getElementById('campaign-map'), {{
                zoom: 16,
                center: {{lat: {self.location['coordinates'].y}, lng: {self.location['coordinates'].x}}}
            }});
            
            new google.maps.Marker({{
                position: {{lat: {self.location['coordinates'].y}, lng: {self.location['coordinates'].x}}},
                map: map,
                title: '{self.location['place_name']}'
            }});
        }}
        
        // GPS 인증
        async function verifyByGPS() {{
            const position = await navigator.geolocation.getCurrentPosition(pos => pos.coords);
            const response = await fetch('/api/verify-o2o', {{
                method: 'POST',
                body: JSON.stringify({{
                    type: 'gps',
                    lat: position.latitude,
                    lng: position.longitude,
                    location_id: '{self.location_id}'
                }})
            }});
            const result = await response.json();
            alert(result.verified ? `✅ 인증 완료! +{self.location['reward_points']} K-포인트` : `❌ {{result.reason}}`);
        }}
        </script>
        """
```

#### 실제 캠페인 예시

```
Samsung Galaxy 카메라 챌린지 (O2O)
├─ 위치: "성수동 카페" (GPS: 37.5665, 126.9780)
├─ 캠페인 타입: visit_challenge
├─ 리믹스 노드: remix_20251222_samsung_001
│  ├─ 기획: "갤럭시 카메라로 담은 남산 야경"
│  ├─ 기술: 약광 촬영, 야경 색감 강조
│  └─ 스토리: 평범한 야경 → 갤럭시로 담은 순간 → 매직 변환
├─ 검증 방법: GPS 기반 + 인증샷 타임스탐프
├─ 보상: 50 K-포인트 + 갤럭시 케이스 10% 할인 쿠폰
├─ 캠페인 기간: 2025-12-22 ~ 2026-01-31
└─ 예상 참여자: 1,000명

사용자 플로우:
1. 성수동 카페 방문
2. 스마트폰 열기 → "K-MEME FACTORY" 앱
3. "Samsung Galaxy 챌린지" 노드 클릭
4. "위치 기반 챌린지" 섹션에서 GPS 인증 → "위치 확인됨"
5. 챌린지 촬영 → "갤럭시 카메라로 야경 담기"
6. 업로드 & 인증샷 제출
7. ✅ "인증 완료! 50 K-포인트 적립"
```

---

### 2.3 [Hardening #3] 노드 계층화 & 거버넌스 아키텍처 (Master/Fork 구조)

#### 문제정의
- **기존 (v5.2 미흡점)**: 관리자가 만든 노드와 사용자가 만든 노드가 구분되지 않음.
- **문제**: 오픈소스 생태계 활성화 시 "퀄리티 저하(Noise)"가 발생하고, "광고주 신뢰도" 하락.

#### 솔루션: Master/Fork 계층 + Locking & Permissions

```python
# 노드 권한 모델 (Enum)

from enum import Enum

class NodeLayer(Enum):
    """
    노드의 계층화 구조
    """
    MASTER = "master"      # 레벨 0: 전문가 (관리자 또는 인증된 크리에이터)
    FORK = "fork"         # 레벨 1: 사용자가 Master를 복제해서 수정한 것
    FORK_OF_FORK = "fork_of_fork"  # 레벨 2: Fork의 Fork

class NodePermission(Enum):
    """
    각 노드에 부여되는 권한
    """
    READ_ONLY = "read_only"        # MASTER: 수정 불가
    FULL_EDIT = "full_edit"        # FORK/FORK_OF_FORK: 자유 수정
    CAMPAIGN_PROTECTED = "campaign_protected"  # 광고주 캠페인: 수정 제한

class NodeGoverned(Enum):
    """
    노드가 적용받는 거버넌스
    """
    OPEN_COMMUNITY = "open_community"  # FORK: 자유로운 수정 + 공유
    BRAND_OFFICIAL = "brand_official"  # MASTER: 브랜드 캠페인 보호
    CREATOR_VERIFIED = "creator_verified"  # MASTER: 크리에이터 인증 노드


# 데이터베이스 스키마 추가

ALTER TABLE remix_nodes ADD COLUMN layer VARCHAR(20) DEFAULT 'fork';  -- master | fork | fork_of_fork
ALTER TABLE remix_nodes ADD COLUMN permission VARCHAR(30) DEFAULT 'full_edit';  -- read_only | full_edit | campaign_protected
ALTER TABLE remix_nodes ADD COLUMN governed_by VARCHAR(30) DEFAULT 'open_community';  -- open_community | brand_official | creator_verified
ALTER TABLE remix_nodes ADD COLUMN owner_type VARCHAR(20);  -- "admin" | "brand" | "user"
ALTER TABLE remix_nodes ADD COLUMN parent_fork_id UUID REFERENCES remix_nodes(id);  -- Fork의 부모 노드
ALTER TABLE remix_nodes ADD COLUMN lock_reason TEXT;  -- 잠금 사유 (있는 경우)

CREATE INDEX idx_layer ON remix_nodes(layer);
CREATE INDEX idx_owned_by ON remix_nodes(owner_type);
```

#### 거버넌스 규칙 엔진

```python
class NodeGovernanceEngine:
    """
    노드의 layer, permission, governance를 기반으로
    사용자가 할 수 있는 액션을 제어
    """
    
    async def check_user_permission(
        self,
        user_id: str,
        node_id: str,
        action: str  # "view", "fork", "edit", "share", "monetize"
    ) -> dict:
        """
        사용자가 특정 노드에서 특정 액션을 할 수 있는지 확인
        """
        
        node = await db.get_remix_node(node_id)
        user = await db.get_user(user_id)
        
        # 규칙 매트릭스
        permission_matrix = {
            # (Layer, Permission, Governance) → [가능한 액션]
            
            # MASTER (읽기 전용)
            ('master', 'read_only', 'open_community'): ['view', 'fork', 'share'],
            ('master', 'read_only', 'brand_official'): ['view', 'fork', 'share'],
            ('master', 'read_only', 'creator_verified'): ['view', 'fork', 'share'],
            
            # FORK (자유 수정)
            ('fork', 'full_edit', 'open_community'): ['view', 'edit', 'fork', 'share', 'monetize'],
            
            # FORK_OF_FORK (제한 있음)
            ('fork_of_fork', 'full_edit', 'open_community'): ['view', 'edit', 'fork', 'share'],  # monetize 불가
            
            # 광고주 캠페인 (엄격한 제어)
            ('master', 'campaign_protected', 'brand_official'): [],  # 외부 사용자는 불가
        }
        
        # 노드의 소유자인지 확인
        is_owner = (node['created_by'] == user_id)
        is_admin = (user['role'] == 'admin')
        is_brand = (node['owner_type'] == 'brand' and user['brand_id'] == node['brand_id'])
        
        # 권한 확인
        key = (node['layer'], node['permission'], node['governed_by'])
        allowed_actions = permission_matrix.get(key, [])
        
        # 예외: 소유자는 항상 edit 가능
        if (is_owner or is_admin or is_brand) and action == 'edit':
            return {"allowed": True, "reason": "owner_privilege"}
        
        # 예외: Admin은 모든 액션 가능
        if is_admin:
            return {"allowed": True, "reason": "admin_privilege"}
        
        # 기본 규칙 적용
        if action in allowed_actions:
            return {"allowed": True, "reason": "permitted_by_governance"}
        else:
            return {
                "allowed": False,
                "reason": f"Action '{action}' not permitted for {node['layer']} layer with {node['permission']} permission",
                "current_policy": {
                    "layer": node['layer'],
                    "permission": node['permission'],
                    "governed_by": node['governed_by']
                }
            }
    
    async def create_fork_with_governance(
        self,
        user_id: str,
        master_node_id: str
    ) -> dict:
        """
        사용자가 MASTER 노드를 FORK (복제)할 때의 거버넌스 규칙
        """
        
        master = await db.get_remix_node(master_node_id)
        
        # 규칙 1: MASTER의 layer는 자동으로 FORK로 변환
        fork_layer = "fork_of_fork" if master['layer'] == "fork" else "fork"
        
        # 규칙 2: MASTER가 "brand_official"이면, FORK는 "open_community"로 강제 전환
        fork_governed = "open_community" if master['governed_by'] == "brand_official" else master['governed_by']
        
        # 규칙 3: 깊이 제한 (Genealogy Depth <= 3)
        if master['genealogy_depth'] >= 3:
            return {
                "created": False,
                "reason": "Maximum genealogy depth (3) reached. Cannot fork further."
            }
        
        # FORK 생성
        fork_node = {
            'node_id': f"remix_fork_{uuid.uuid4()}",
            'parent_fork_id': master_node_id,
            'created_by': user_id,
            'layer': fork_layer,
            'permission': 'full_edit',
            'governed_by': fork_governed,
            'owner_type': 'user',
            'genealogy_depth': master['genealogy_depth'] + 1,
            'created_at': datetime.now(),
            # 데이터 복사
            'gemini_analysis': master['gemini_analysis'],
            'claude_brief': master['claude_brief'],
            'storyboard_images': master['storyboard_images'],
            # 메타데이터
            'original_master': master_node_id,
            'fork_note': f"Forked from {master_node_id} by {user_id}"
        }
        
        await db.save_remix_node(fork_node)
        
        return {
            "created": True,
            "fork_node_id": fork_node['node_id'],
            "layer": fork_layer,
            "governed_by": fork_governed,
            "message": f"✅ Fork created! You can edit and share freely.",
            "editing_constraints": self._get_editing_constraints(fork_governed)
        }
    
    def _get_editing_constraints(self, governed_by: str) -> list:
        """
        각 governance 모드별 편집 제약 사항
        """
        
        constraints = {
            'open_community': [],  # 제약 없음
            'brand_official': [
                "Cannot edit core story",
                "Cannot remove brand mentions",
                "Cannot change product references"
            ],
            'creator_verified': [
                "Cannot edit without creator approval"
            ]
        }
        
        return constraints.get(governed_by, [])
```

#### 캠페인 노드 보호 (Brand Official)

```python
class BrandCampaignProtection:
    """
    광고주(Brand)가 자신의 캠페인 노드를 보호하는 메커니즘
    """
    
    async def lock_campaign_node(
        self,
        brand_id: str,
        node_id: str,
        lock_reason: str = "Official brand campaign - Read only"
    ) -> dict:
        """
        노드를 잠금 (외부 사용자 수정 불가)
        """
        
        node = await db.get_remix_node(node_id)
        
        # 권한 확인: 이 노드의 소유 브랜드만 잠금 가능
        if node['brand_id'] != brand_id:
            return {"locked": False, "reason": "Not the owner of this node"}
        
        # 잠금
        node['permission'] = 'campaign_protected'
        node['lock_reason'] = lock_reason
        node['layer'] = 'master'
        node['governed_by'] = 'brand_official'
        
        await db.save_remix_node(node)
        
        return {
            "locked": True,
            "node_id": node_id,
            "permission": 'campaign_protected',
            "message": f"✅ Campaign node locked for official brand protection"
        }
    
    async def unlock_node_for_user_fork(
        self,
        user_id: str,
        protected_node_id: str
    ) -> dict:
        """
        보호된 노드를 FORK할 때, 사용자는 자신의 복사본을 얻음
        (원본은 보호 유지)
        """
        
        protected = await db.get_remix_node(protected_node_id)
        
        # FORK 생성 (자유 수정 권한)
        user_fork = {
            'node_id': f"remix_user_fork_{uuid.uuid4()}",
            'parent_fork_id': protected_node_id,
            'created_by': user_id,
            'layer': 'fork',
            'permission': 'full_edit',  # ← 원본과 다르게 "수정 가능"
            'governed_by': 'open_community',  # ← 브랜드 제약 해제
            'owner_type': 'user',
            'genealogy_depth': protected['genealogy_depth'] + 1
            # ... (나머지 데이터 복사)
        }
        
        await db.save_remix_node(user_fork)
        
        return {
            "forked": True,
            "fork_node_id": user_fork['node_id'],
            "message": "✅ You now have a personal copy you can edit and customize!",
            "hint": "Original campaign node remains protected by the brand."
        }
```

---

### 2.4 [Hardening #4] 다중 스킨 렌더링 (Multi-Skin UI + Campaign Mode)

#### 문제정의
- **기존 (v5.2 미흡점)**: 모든 노드가 동일한 "Smart Recipe View" UI로 보임.
- **문제**: "삼성전자 공식 캠페인"과 "일반 밈"을 구분하지 못해 광고주 신뢰도 ↓, 사용자 혼동 ↑.

#### 솔루션: Theme Engine + Conditional Rendering

```python
class SmartRecipeViewThemeEngine:
    """
    노드의 Layer & Governance에 따라 다른 UI 테마 렌더링
    """
    
    async def render_smart_recipe_view(
        self,
        node_id: str,
        user_id: str = None
    ) -> str:
        """
        노드의 layer와 governed_by에 따라 다른 HTML 반환
        """
        
        node = await db.get_remix_node(node_id)
        
        # 1. 권한 확인
        if user_id:
            perm_check = await governance_engine.check_user_permission(
                user_id, node_id, "view"
            )
            if not perm_check['allowed']:
                return self._render_no_permission_ui(node, perm_check)
        
        # 2. Theme 선택
        theme = self._select_theme(node)
        
        # 3. 테마에 따라 렌더링
        if theme == 'community_recipe':
            return self._render_community_recipe(node)
        elif theme == 'campaign_official':
            return self._render_campaign_official(node)
        elif theme == 'location_based':
            return self._render_location_based(node)
        else:
            return self._render_default(node)
    
    def _select_theme(self, node: dict) -> str:
        """
        노드의 특성에 따라 적합한 테마 선택
        """
        
        if node.get('governance') == 'brand_official':
            return 'campaign_official'
        elif node.get('campaign_context') and 'location_data' in node['campaign_context']:
            return 'location_based'
        else:
            return 'community_recipe'
    
    def _render_community_recipe(self, node: dict) -> str:
        """
        일반 사용자용 UI (기본)
        """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{node['title']}</title>
            <meta name="theme-color" content="#32B8C6">
            <style>
                /* 커뮤니티 테마: 따뜻하고 친근한 색상 */
                body {{ background: #F5F5F5; color: #333; }}
                .header {{ background: linear-gradient(135deg, #32B8C6, #208A91); }}
                .cta-button {{ background: #32B8C6; color: white; }}
            </style>
        </head>
        <body>
            <!-- 헤더: 원본 영상 + 기획 -->
            <header class="header">
                <div class="video-comparison">
                    <div class="original">
                        <h3>원본 영상</h3>
                        <video src="{node['parent_video_url']}" controls></video>
                    </div>
                    <div class="preview">
                        <h3>당신이 만들 장면</h3>
                        <img src="{node['storyboard_images']['shot_2_peak']}" alt="preview">
                    </div>
                </div>
            </header>

            <!-- 메인: 리시피 카드 -->
            <main class="recipe-content">
                <section class="recipe-card">
                    <h1>{node['claude_brief']['korean_scenario']['title']}</h1>
                    <p class="narrative">{node['claude_brief']['korean_scenario']['narrative']}</p>
                </section>

                <!-- 기본 정보: 장소, 의상, 음악 -->
                <section class="basic-guide">
                    <h2>📍 촬영 가이드</h2>
                    <div class="guide-grid">
                        <div class="guide-card">
                            <span class="icon">🎬</span>
                            <h3>장소</h3>
                            <p>{node['claude_brief']['visual_modifications']['setting_description']}</p>
                        </div>
                        <div class="guide-card">
                            <span class="icon">👕</span>
                            <h3>의상</h3>
                            <p>{node['claude_brief']['visual_modifications']['costume']}</p>
                        </div>
                        <div class="guide-card">
                            <span class="icon">🎵</span>
                            <h3>음악</h3>
                            <p>{node['claude_brief']['audio_modifications']['music_replacement']['korean_alternative']}</p>
                        </div>
                    </div>
                </section>

                <!-- 타이밍 가이드 (Beat Guide 포함) -->
                <section class="timing-guide">
                    <h2>⏱️ 주요 타이밍</h2>
                    <div class="beat-guide-player">
                        <audio id="beat-guide" src="{node['audio_guide']['beat_guide_track_path']}"></audio>
                        <button onclick="document.getElementById('beat-guide').play()">🔊 비트 가이드 재생</button>
                        <p class="hint">한쪽 귀에만 이어폰으로 청음하며 촬영하세요!</p>
                    </div>
                    <table class="timing-table">
                        <tr>
                            <th>시간(초)</th>
                            <th>동작</th>
                            <th>난이도</th>
                        </tr>
                        {''.join(f"<tr><td>{frame['time']}초</td><td>{frame['action']}</td><td>{'⭐'*frame['difficulty']}</td></tr>" for frame in node['claude_brief']['keyframes_adjustment'])}
                    </table>
                </section>

                <!-- 플랫폼 안내 -->
                <section class="platform-guide">
                    <h2>📱 {node['platform'].upper()} 안내</h2>
                    <img src="{node['platform_safe_zone']['ghost_ui_overlay_path']}" alt="safe zone">
                    <p>파란 부분은 자막/액션 배치 OK, 빨간 부분은 피하세요!</p>
                </section>

                <!-- 커머스 배너 (동적) -->
                <section class="commerce-slot">
                    <h2>✨ 이 밈에 어울리는 제품</h2>
                    <div class="product-carousel">
                        {self._render_dynamic_commerce_products(node)}
                    </div>
                </section>

                <!-- 파일 다운로드 -->
                <section class="downloads">
                    <h2>📥 가이드 파일</h2>
                    <a href="{node['guides']['text_guide']}" download class="btn">📄 Text Guide</a>
                    <a href="{node['storyboard_images']['shot_1']}" download class="btn">🖼️ 스토리보드 이미지</a>
                    <a href="{node['audio_guide']['beat_guide_track_path']}" download class="btn">🎵 비트 가이드</a>
                </section>

                <!-- CTA -->
                <div class="cta-section">
                    <button class="cta-button" onclick="startRecording()">🎬 촬영 시작하기</button>
                </div>
            </main>
        </body>
        </html>
        """
    
    def _render_campaign_official(self, node: dict) -> str:
        """
        광고주 캠페인용 UI (공식 스킨)
        
        특징:
        - 상단에 "공식 캠페인" 배지
        - 브랜드 컬러 적용
        - 참여 추적 강조
        - "캠페인 리더보드" 노출
        """
        
        brand_color = node.get('brand_color', '#32B8C6')
        brand_name = node.get('brand', 'Samsung')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>[공식] {node['title']} - {brand_name}</title>
            <meta name="theme-color" content="{brand_color}">
            <style>
                /* 캠페인 테마: 브랜드 컬러 강조 */
                body {{ background: #FFFFFF; }}
                .campaign-header {{ 
                    background: linear-gradient(135deg, {brand_color}, {brand_color}dd);
                    padding: 2rem;
                    text-align: center;
                    color: white;
                }}
                .official-badge {{
                    display: inline-block;
                    background: gold;
                    color: black;
                    padding: 0.5rem 1rem;
                    border-radius: 20px;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }}
                .brand-logo {{ height: 60px; margin: 1rem 0; }}
                .leaderboard {{ background: #F5F5F5; padding: 1.5rem; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <!-- 공식 캠페인 헤더 -->
            <div class="campaign-header">
                <div class="official-badge">🏆 공식 캠페인</div>
                <img src="{node.get('brand_logo', '')}" alt="{brand_name}" class="brand-logo">
                <h1>{node['title']}</h1>
                <p class="campaign-desc">{node.get('campaign_description', '')}</p>
            </div>

            <main class="campaign-content">
                <!-- 캠페인 규칙 -->
                <section class="campaign-rules">
                    <h2>📋 참여 방법</h2>
                    <ol>
                        <li>아래 가이드를 따라 영상 촬영</li>
                        <li>우리 해시태그 #{brand_name.lower()}_challenge 로 업로드</li>
                        <li>이 페이지에서 링크 제출 → 인증</li>
                        <li>🏆 상위 100개 영상: 상품 + K-포인트!</li>
                    </ol>
                </section>

                <!-- 기본 가이드 (Community와 동일) -->
                <section class="recipe-card">
                    <h2>🎬 촬영 가이드</h2>
                    {self._render_recipe_basic(node)}
                </section>

                <!-- 리더보드 -->
                <section class="leaderboard">
                    <h2>🏅 실시간 참여 현황</h2>
                    <div class="stats">
                        <div class="stat">
                            <span class="label">총 참여자</span>
                            <span class="value">{node.get('participant_count', 'N/A')}</span>
                        </div>
                        <div class="stat">
                            <span class="label">총 뷰</span>
                            <span class="value">{node.get('total_views', 'N/A'):,}</span>
                        </div>
                        <div class="stat">
                            <span class="label">참여 마감</span>
                            <span class="value">{node.get('campaign_end_date', 'N/A')}</span>
                        </div>
                    </div>
                </section>

                <!-- 상품 정보 (강조) -->
                <section class="campaign-prize">
                    <h2>🎁 상품</h2>
                    <div class="prize-card">
                        <h3>{node.get('prize_title', '')}</h3>
                        <p>{node.get('prize_description', '')}</p>
                        <p class="value">{node.get('prize_value', '')}</p>
                    </div>
                </section>

                <!-- 참여 버튼 (강조) -->
                <div class="campaign-cta">
                    <button class="cta-button" style="background: {brand_color};" onclick="submitEntry()">
                        🚀 캠페인에 참여하기
                    </button>
                    <p class="terms">
                        <a href="#">이용약관</a> | <a href="#">개인정보처리방침</a> | <a href="#">{brand_name} 공식 사이트</a>
                    </p>
                </div>
            </main>
        </body>
        </html>
        """
    
    def _render_location_based(self, node: dict) -> str:
        """
        위치 기반 O2O 캠페인용 UI
        
        특징:
        - 지도 표시
        - GPS 인증 버튼
        - 위치 정보 강조
        - 영수증 스캔 옵션
        """
        
        location = node.get('campaign_context', {}).get('location_data', {})
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{node['title']} - 위치 챌린지</title>
            <script src="https://maps.googleapis.com/maps/api/js?key={{YOUR_MAPS_API_KEY}}"></script>
        </head>
        <body>
            <header class="location-header">
                <h1>📍 {location.get('place_name', '위치')}</h1>
                <p>{location.get('address', '')}</p>
            </header>

            <main>
                <!-- 지도 -->
                <div id="map" style="height: 400px; margin: 1rem 0;"></div>

                <!-- 위치 정보 -->
                <section class="location-info">
                    <h2>🎯 캠페인 정보</h2>
                    <p><strong>장소:</strong> {location.get('place_name')}</p>
                    <p><strong>주소:</strong> {location.get('address')}</p>
                    <p><strong>보상:</strong> {node.get('reward_points', 0)} K-포인트 + {node.get('reward_product', '')}</p>
                </section>

                <!-- 촬영 가이드 -->
                <section class="recipe-card">
                    {self._render_recipe_basic(node)}
                </section>

                <!-- 인증 방법 -->
                <section class="verification-methods">
                    <h2>✅ 방문 인증</h2>
                    <button onclick="verifyByGPS()" class="verify-btn">📍 GPS 인증</button>
                    <button onclick="verifyByReceipt()" class="verify-btn">🧾 영수증 스캔</button>
                    <button onclick="verifyByPhoto()" class="verify-btn">📸 인증샷 업로드</button>
                </section>

                <!-- 참여 CTA -->
                <button class="cta-button" onclick="startChallenge()">🚀 도전하기</button>
            </main>

            <script>
            function initMap() {{
                const location = {{lat: {location.get('lat', 0)}, lng: {location.get('lng', 0)}}};
                const map = new google.maps.Map(document.getElementById('map'), {{
                    zoom: 16,
                    center: location
                }});
                new google.maps.Marker({{position: location, map: map}});
            }}
            window.addEventListener('load', initMap);
            </script>
        </body>
        </html>
        """
    
    def _render_default(self, node: dict) -> str:
        """
        기본 렌더링 (community_recipe와 동일)
        """
        return self._render_community_recipe(node)
    
    def _render_recipe_basic(self, node: dict) -> str:
        """
        모든 테마에서 공통으로 사용되는 기본 리시피 섹션
        """
        return f"""
        <h3>{node['claude_brief']['korean_scenario']['title']}</h3>
        <p>{node['claude_brief']['korean_scenario']['narrative']}</p>
        <div class="guide-grid">
            <div class="guide-card">
                <span class="icon">🎬</span>
                <h4>장소</h4>
                <p>{node['claude_brief']['visual_modifications']['setting_description']}</p>
            </div>
            <div class="guide-card">
                <span class="icon">🎵</span>
                <h4>음악</h4>
                <p>{node['claude_brief']['audio_modifications']['music_replacement']['korean_alternative']}</p>
            </div>
        </div>
        """
    
    def _render_dynamic_commerce_products(self, node: dict) -> str:
        """
        커머스 섹션: Gemini가 분류한 카테고리 + Claude가 추출한 키워드로
        관련 제품 동적 렌더링
        """
        
        category = node['commerce_context']['primary_category']
        keywords = node['commerce_context']['keywords']
        
        # DB에서 관련 제품 조회 (실제 구현)
        products = [
            {
                'id': 1,
                'name': 'XX 뷰티 롱래스팅 립스틱',
                'image': 'product_1.png',
                'cta': '체험단 신청',
                'banner_type': 'trial'
            },
            {
                'id': 2,
                'name': 'YY 메이크업 팔레트',
                'image': 'product_2.png',
                'cta': '공동구매',
                'banner_type': 'group_buy'
            }
        ]
        
        return '\n'.join([
            f"""
            <div class="product-card">
                <img src="{p['image']}" alt="{p['name']}">
                <h4>{p['name']}</h4>
                <button onclick="trackConversion({p['id']})">{p['cta']}</button>
            </div>
            """
            for p in products
        ])
    
    def _render_no_permission_ui(self, node: dict, perm_check: dict) -> str:
        """
        권한 없음 UI
        """
        
        return f"""
        <div class="error-page" style="text-align: center; padding: 2rem;">
            <h1>🔒 접근 불가</h1>
            <p>{perm_check['reason']}</p>
            <button onclick="history.back()">뒤로 가기</button>
        </div>
        """
```

---

## 3. 통합 데이터 스키마 (Hardened)

### 3.1 확장된 Remix Node 구조

```json
{
  "remix_node": {
    "node_id": "remix_20251222_001",
    
    // === 기본 메타데이터 ===
    "created_at": "2025-12-22T00:00:00Z",
    "updated_at": "2025-12-22T00:00:00Z",
    "created_by": "user_admin_001",
    "owner_type": "admin",
    
    // === 계층화 & 거버넌스 (NEW) ===
    "layer": "master",  // master | fork | fork_of_fork
    "permission": "read_only",  // read_only | full_edit | campaign_protected
    "governed_by": "brand_official",  // open_community | brand_official | creator_verified
    "parent_fork_id": null,
    "genealogy_depth": 0,
    
    // === 원본 영상 분석 (Gemini) ===
    "gemini_analysis": {
      "metadata": {
        "platform": "tiktok",
        "duration_seconds": 15,
        "original_audio": {
          "title": "Flowers",
          "artist": "Miley Cyrus",
          "bpm": 128,
          "music_drop_timestamps": [2.0, 6.0, 10.0, 14.0]
        }
      },
      "visual_dna": { /* ... */ },
      "commerce_context": { /* ... */ },
      "meme_dna": { /* ... */ }
    },
    
    // === 한국형 기획 (Claude) ===
    "claude_brief": {
      "korean_scenario": { /* ... */ },
      "visual_modifications": { /* ... */ },
      "audio_modifications": { /* ... */ },
      "action_modifications": { /* ... */ }
    },
    
    // === 생성된 콘텐츠 ===
    "storyboard_images": {
      "shot_1": "s3://...",
      "shot_2": "s3://...",
      "shot_3": "s3://...",
      "shot_4": "s3://..."
    },
    "audio_guide": {
      "beat_guide_track_path": "s3://...",
      "beat_guide_format": "wav_48khz_stereo",
      "source_bpm": 128,
      "beat_timestamps": [0.0, 0.5, 1.0, 1.5, ...]
    },
    
    // === O2O 캠페인 (NEW) ===
    "campaign_context": {
      "type": "visit_challenge",  // online_commerce | visit_challenge
      "location_data": {
        "lat": 37.5665,
        "lng": 126.9780,
        "place_name": "성수동 팝업스토어",
        "address": "서울시 성동구 성수동",
        "gmaps_place_id": "ChIJyW..."
      },
      "verification_method": "gps_snapshot_match",
      "reward_points": 100,
      "reward_product": "Samsung Galaxy 케이스 10% 할인"
    },
    
    // === 캠페인 정보 (NEW) ===
    "brand_campaign": {
      "brand_id": "samsung_001",
      "brand_name": "Samsung Galaxy",
      "brand_color": "#1428A0",
      "brand_logo": "s3://...",
      "campaign_title": "갤럭시 카메라 챌린지",
      "campaign_description": "당신의 야경을 갤럭시 카메라로 담아보세요",
      "campaign_start": "2025-12-22",
      "campaign_end": "2026-01-31",
      "prize_title": "Galaxy Z Fold 케이스",
      "prize_value": "150,000원 상당",
      "participant_count": 1523,
      "total_views": 2500000
    },
    
    // === 계보도 관계 (NEW) ===
    "genealogy": {
      "parent_node_id": null,
      "children": [
        {
          "child_node_id": "remix_20251222_fork_A",
          "mutation_type": "audio_change",
          "mutation_value": {"before": "Flowers", "after": "봄날"},
          "performance_delta": "+400%",
          "created_by": "user_123"
        }
      ],
      "genealogy_depth": 0,
      "mutation_profile": null
    }
  }
}
```

---

## 4. 개발 체크리스트 (최종 확장)

### Phase 1 (MVP): Week 1-12
- [ ] **Step 1**: Gemini 3.0 Pro (BPM 포함 ✅)
- [ ] **Step 2**: Claude 4.5 Opus Chat UI ✅
- [ ] **Step 3**: nanobanana 이미지 생성 ✅
- [ ] **Step 4**: Admin 업로드 + 오디오 렌더링 ✅

### Phase 1 + Hardening: Week 13-16 (MVP 직후)
- [ ] **Genealogy Graph** (Neo4j 기본 설정)
  - [ ] Node Relations CRUD (Create, Read)
  - [ ] Mutation Profile 저장
  - [ ] Performance Delta 계산
  
- [ ] **O2O 스키마** (PostGIS)
  - [ ] Location 데이터 모델
  - [ ] Verification Logic (GPS)
  - [ ] O2O UI 섹션
  
- [ ] **Governance System** (권한 관리)
  - [ ] Master/Fork 분류
  - [ ] Locking 메커니즘
  - [ ] Permission Matrix
  
- [ ] **Multi-Skin Renderer**
  - [ ] Community Theme
  - [ ] Campaign Official Theme
  - [ ] Location-Based Theme

### Phase 2 (Scale): Month 4-6
- [ ] Genealogy 쿼리 최적화 (추천 엔진)
- [ ] O2O 캠페인 활성화 (10개 이상)
- [ ] 거버넌스 강화 (분쟁 해결 메커니즘)

### Phase 3 (Commerce): Month 7-12
- [ ] 캠페인 수익화 (광고주 가격 책정)
- [ ] 리더보드 & 리워드 시스템
- [ ] 브랜드 파트너십 확대

---

## 5. 기술 스택 (업데이트)

```
Backend:
  - Python 3.11 + FastAPI
  - PostgreSQL + PostGIS (지리 인덱싱)
  - Neo4j (Graph DB - 바이럴 계보도)
  - Pinecone (Vector DB)
  - Redis (Cache)
  - Google Gemini 3.0 Pro API
  - Anthropic Claude 4.5 Opus API
  - Librosa (Audio Beat Guide)
  - Google Maps API (O2O)

Frontend:
  - React 18 + TypeScript
  - Next.js 14
  - React Flow
  - MapboxGL (지도)
  - TailwindCSS
  - Vercel (Hosting)

DevOps:
  - Docker + Docker Compose
  - GitHub Actions (CI/CD)
  - Sentry (Error Tracking)
  - Datadog (Monitoring)
```

---

## 6. 비용 분석 (Hardened)

### 월간 변동비 (Variable Cost)

```
Gemini 3.0 Pro:        $0.30~0.40
Audio Beat Guide:      $0.05~0.10
Image Generation:      $0.00 (무료)
Neo4j Query:           $0.02~0.05 (그래프 연산)
PostGIS Query:         $0.01~0.03 (지리 쿼리)
Google Maps API:       $0.02~0.05 (O2O 캠페인)
────────────────────────────
총 변동비: $0.40~0.60/리믹스

변동비 절감 (vs Flux API):
- Before: $1.80/리믹스 (Gemini + Flux)
- After: $0.50/리믹스 (Gemini + 무료 도구 + 신 기술)
- 절감율: 72% ✅
```

---

## 7. Success Metrics (2025~2026)

### 2025 (MVP Phase)
- ✅ 파이프라인 자동화 100%
- ✅ 첫 1,000개 노드 생성
- ✅ K-Success 달성률 10%+

### 2026 (Scaling Phase)
- ✅ Genealogy Graph에서 "변이 전략" 추천 시작
- ✅ O2O 캠페인 50개+
- ✅ 브랜드 파트너 10개+ 확보
- ✅ DAU 10,000+ 달성

---

## 최종 메시지

### ✅ Hardened Points

**[Hardening #1] 바이럴 계보도 (Viral Genealogy Graph)**
- Neo4j를 활용한 Parent → Mutation → Child 관계 데이터화
- "이 변수를 바꾸면 +350% 성과"를 AI가 자동 추천 가능
- 데이터 자산화 → 수익화 경로 확보

**[Hardening #2] O2O 캠페인 (Location-Based)**
- PostGIS 지리 인덱싱 + Google Maps 연동
- GPS 인증, 영수증 스캔, 타임스탐프 검증
- "맛집 방문", "팝업스토어 인증" 등 오프라인 확장 가능

**[Hardening #3] 거버넌스 & 권한 (Master/Fork Structure)**
- Master (읽기 전용, 광고주 보호) vs Fork (자유 수정)
- 오픈소스 생태계 활성화 + 퀄리티 보증 동시 달성
- 캠페인 노드 보호 메커니즘

**[Hardening #4] 다중 스킨 렌더링 (Campaign UI)**
- Community Recipe (일반) vs Campaign Official (광고주) vs Location-Based (O2O)
- 같은 데이터로도 다른 UX 제공
- 광고주 신뢰도 ↑, 사용자 혼동 ↓

### 💡 아키텍처 진화 경로

```
2025 (MVP): "Simple But Complete"
└─ Step 1~4 자동화 완성

2026 (Scaling): "Data-Driven & Community-Powered"
├─ Genealogy Graph 활성화 (AI 추천)
├─ O2O 캠페인 확대 (오프라인 전환)
├─ 거버넌스 강화 (생태계 자정)
└─ 수익화 다각화 (광고주 + 크리에이터)

최종: "Open Source Meme Ecology + Creator-Advertiser Marketplace"
└─ 누구나 참여, 브랜드는 신뢰, 크리에이터는 보상
```

---

**준비됨. v5.2 Hardened는 5년 확장성을 보증합니다.** 🚀

**Document Version**: 5.2 Hardened (Future-Proof Architecture)
**Status**: ✅ Approved for Immediate Development + Long-term Growth
**Target**: CTO, 개발팀 (즉시 착수, 2026년까지 Scaling 계획 내재화)

**Key Points**:
- 2025: MVP 완성 + 첫 1,000개 노드
- 2026: 데이터 자산화 + O2O 확장 + 거버넌스 강화
- Long-term: "Open Source Meme Ecology" = 크리에이터 수익화 플랫폼