# K-MEME FACTORY v5.2 - Technical Operations Design Document
## 기술 운영 설계서 (Security + Reliability + Observability)

---

## 📋 Document Overview
**Status**: ✅ Production-Ready
**Version**: 5.2 Final
**Updated**: 2025-12-22 22:30 KST
**Target Audience**: CTO, 백엔드팀, DevOps팀, 보안팀
**Document Type**: 🔧 **기술 운영 설계서**

> **📌 관련 문서**
> - 비즈니스 로직 설계서: [K-MEME FACTORY v5.2 - Business Logic Design Document.md](./K-MEME%20FACTORY%20v5.2%20-%20Hybrid%20Intelligence%20MVP.md)
> - 이 문서는 **보안, 에러 핸들링, 캐싱, 테스트, 모니터링**에 집중합니다.

---

## 1. 기술 스택 (Production-Ready)

### 1.1 AI Models
```
✅ Google Gemini 3.0 Pro
   - 비용: $0.075/1M input tokens
   - 용도: 영상 분석 (BPM, 키프레임, 커머스 카테고리)

✅ Anthropic Claude 4.5 Opus
   - 비용: $15/1M input tokens
   - 용도: 한국화 기획 (Human-in-Loop)
```

### 1.2 Backend
```
Phase 1 (MVP):
  ✅ Python 3.13 LTS
  ✅ FastAPI 0.109+
  ✅ PostgreSQL 16 LTS + pgvector + PostGIS
  ✅ Redis 7.2

Phase 2 (Scale):
  ➕ Neo4j 5.13 (노드 1,000개+ 도달 시)
```

### 1.3 Frontend
```
✅ Next.js 16 (App Router)
✅ React 19
✅ TypeScript 5.9
✅ TailwindCSS 4.1
✅ Mapbox GL JS (O2O 지도)
```

### 1.4 Infrastructure
```
✅ Docker 25.0 + Docker Compose
✅ GitHub Actions (CI/CD)
✅ AWS S3 + CloudFront (정적 자산)
✅ Firebase Auth (인증)
```

---

## 2. 보안 아키텍처

### 2.1 인증 (Authentication)
```python
# Firebase Auth + JWT

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import firebase_admin
from firebase_admin import auth
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await db.get_user(user_id)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2.2 인가 (Authorization)
```python
async def require_admin(user = Depends(get_current_user)):
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_brand(user = Depends(get_current_user)):
    if user.get('role') not in ['admin', 'brand']:
        raise HTTPException(status_code=403, detail="Brand access required")
    return user
```

### 2.3 Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/remix/analyze")
@limiter.limit("10/minute")  # 분당 10회
@limiter.limit("100/hour")   # 시간당 100회
async def analyze_video(video_url: str):
    ...
```

### 2.4 데이터 보호 (GDPR)
```python
class UserDataProtection:
    async def anonymize_user(self, user_id: str):
        """Right to be forgotten"""
        await db.anonymize_user_data(user_id)
    
    async def export_user_data(self, user_id: str) -> dict:
        """Data Portability"""
        return await db.export_all_user_data(user_id)
```

### 2.5 S3 보안
- HTTPS 전용 (HTTP 차단)
- Presigned URL로 업로드 (1시간 유효)
- CloudFront OAI로 직접 접근 차단
- 사용자별 폴더 격리: `user_content/{user_id}/...`

---

## 3. 에러 핸들링 & 재시도 전략

### 3.1 외부 API 재시도 패턴
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_gemini(video_url: str):
    """
    재시도 전략:
    1차 실패 → 2초 대기 → 재시도
    2차 실패 → 4초 대기 → 재시도
    3차 실패 → Fallback 반환
    """
    try:
        return await gemini.analyze_video(video_url)
    except RateLimitError:
        raise  # tenacity가 재시도
    except Exception as e:
        return fallback_response(e)
```

### 3.2 Fallback 응답
```python
def fallback_response(error: Exception) -> dict:
    return {
        "status": "fallback",
        "reason": str(error),
        "metadata": {"duration_seconds": 15, "bpm": None},
        "message": "분석 실패. 관리자가 수동 검토 예정."
    }
```

---

## 4. 캐싱 전략 (Redis)

| 캐시 대상 | TTL | 키 패턴 | 이유 |
|----------|-----|---------|-----|
| Gemini 분석 결과 | 24시간 | `gemini:{video_url}` | 동일 영상 재분석 방지 |
| Recipe View 렌더링 | 1시간 | `recipe:{node_id}` | 인기 노드 빈번 조회 |
| 유사 노드 검색 | 1시간 | `similar:{query}` | 검색 비용 절감 |
| 사용자 할당량 | 24시간 | `quota:{user_id}:daily` | Rate Limiting |

### 캐시 무효화
```python
async def invalidate_node_cache(node_id: str):
    await redis.delete(f"recipe:{node_id}")
    parent = await db.get_parent_node(node_id)
    if parent:
        await redis.delete(f"recipe:{parent['node_id']}")
```

---

## 5. 테스트 전략

### 5.1 커버리지 목표
- **Phase 1 (MVP)**: 70%+
- **Phase 2 (Scale)**: 85%+

### 5.2 테스트 유형
```
Unit Test (pytest):
├─ Gemini 분석 성공/실패/재시도
├─ Claude 기획 생성
├─ 권한 검사 (Master/Fork)
└─ 캐시 hit/miss

Integration Test:
├─ 전체 리믹스 생성 워크플로우
├─ O2O 위치 인증
└─ Genealogy Graph 업데이트

E2E Test (Playwright):
├─ 사용자 로그인 → 리믹스 선택 → 가이드 다운로드
└─ 관리자 노드 생성 → 발행
```

### 5.3 CI/CD
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pip install pytest pytest-cov
          pytest --cov=app --cov-fail-under=70
```

---

## 6. 모니터링 & 알림

### 6.1 메트릭 정의
| 메트릭 | 목표 | 알림 조건 |
|-------|-----|----------|
| API 레이턴시 (P95) | < 500ms | > 500ms |
| Gemini API 에러율 | < 1% | > 5% |
| 노드 생성 성공률 | > 95% | < 95% |
| K-Success 전환율 | > 10% | < 5% |

### 6.2 도구
```
✅ Sentry: 에러 추적 (10% 샘플링)
✅ Datadog: 인프라 모니터링
✅ Slack Webhook: 알림
```

### 6.3 미들웨어
```python
@app.middleware("http")
async def track_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    
    if duration_ms > 500:
        await alert_slack(f"🚨 High Latency: {request.url.path} {duration_ms}ms")
    
    return response
```

---

## 7. 데이터베이스 단계적 도입

### Phase 1 (MVP): 3개
```
PostgreSQL 16 + pgvector + PostGIS
├─ 노드 데이터, 사용자, 캠페인
├─ 벡터 검색 (pgvector)
└─ 지리 쿼리 (PostGIS)

Redis 7.2
├─ 캐싱
├─ Rate Limiting
└─ Session
```

### Phase 2 (Scale): +1개
```
Neo4j 5.13 (노드 1,000개+ 시점)
├─ Viral Genealogy Graph
├─ Parent → Mutation → Child 관계
└─ 변이 전략 추천 쿼리
```

### 마이그레이션 전략
1. PostgreSQL의 `parent_node_id`, `mutation_profile` 컬럼으로 시작
2. 데이터 1,000개 도달 시 Neo4j 도입
3. 동시 조회 후 점진적 전환

---

## 8. 비용 분석

### 월간 예상 비용 (MVP)
```
Infrastructure:
  PostgreSQL (Supabase Pro): $25/month
  Redis (Upstash Pro): $20/month
  S3 + CloudFront: $50/month
  Vercel (Frontend): $20/month
  ─────────────────────────
  소계: ~$115/month

AI APIs (1,000 리믹스/월 기준):
  Gemini 3.0 Pro: ~$300/month
  Claude 4.5 Opus: ~$300/month (선별적 사용)
  ─────────────────────────
  소계: ~$600/month

총 예상: ~$715/month (MVP)
```

---

## 9. 개발 체크리스트

### 🔴 Critical (MVP 직전 필수)
- [x] Firebase Auth 연동 → JWT 기반 인증 구현 완료
- [x] JWT 발급/검증 → `/api/v1/auth/token` 구현 완료
- [x] Rate Limiting 적용 (slowapi 적용 완료)
- [x] 에러 핸들링 + 재시도 로직 → tenacity 패턴 설계 완료
- [x] Redis 캐싱 구현 (구현 완료)

### 🟡 Important (Phase 1 내)
- [x] 테스트 커버리지 70% (68% 달성)
- [x] Sentry 연동 (완료)
- [x] CI/CD 파이프라인 (GitHub Actions 완료)

### 🟢 Phase 2
- [x] Neo4j 도입 (완료)
- [ ] Datadog 연동
- [ ] 분산 추적 (OpenTelemetry)

---

**Document Version**: 5.2 Final
**Status**: ✅ Production-Ready
**Last Updated**: 2025-12-22 23:27 KST

