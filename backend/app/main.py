"""
Komission FACTORY v5.2 Backend
Main FastAPI Application
"""
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings, validate_runtime_settings
from app.database import init_db
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import setup_rate_limiting
from app.middleware.logging import RequestLoggingMiddleware
from app.routers import api_router
from app.routers.pipelines import router as pipeline_router
from app.services.cache import cache
from app.services.graph_db import graph_db

# Initialize Sentry (only if DSN is configured)
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,  # 10% sampling for performance
        profiles_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events"""
    # Startup
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")

    # Validate runtime settings early
    validate_runtime_settings()
    
    # Initialize Database
    await init_db()
    print("✅ Database initialized")
    
    # Connect Redis Cache
    try:
        await cache.connect()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")

    # Connect Neo4j Graph
    try:
        await graph_db.connect()
        print("✅ Neo4j connected")
    except Exception as e:
        print(f"⚠️ Neo4j connection failed: {e}")

    yield

    # Shutdown
    print("👋 Shutting down...")
    await cache.disconnect()
    await graph_db.close()


app = FastAPI(
    title="Komission FACTORY API",
    description="""
## 🚀 Komission - 바이럴 콘텐츠 인텔리전스 플랫폼

### 주요 기능
- **Outlier 수집**: 바이럴 영상 발굴 및 분석
- **VDG 파이프라인**: Gemini 기반 영상 해체 분석
- **Evidence Loop**: 증거 기반 의사결정
- **O2O 캠페인**: 제품 체험단 운영
- **Canvas**: 노드 기반 템플릿 시스템

### 인증
대부분의 엔드포인트는 Firebase JWT 토큰이 필요합니다.
`Authorization: Bearer <token>` 헤더를 사용하세요.
    """,
    version="5.2.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    redirect_slashes=False,
    openapi_tags=[
        {"name": "Auth", "description": "인증 관련 API"},
        {"name": "Outliers", "description": "아웃라이어 영상 관리"},
        {"name": "Remix", "description": "리믹스 노드 및 분석"},
        {"name": "Canvas", "description": "캔버스 템플릿"},
        {"name": "O2O", "description": "제품 체험단 캠페인"},
        {"name": "Analytics", "description": "분석 및 KPI"},
        {"name": "Pipelines", "description": "VDG 파이프라인"},
        {"name": "WebSocket", "description": "실시간 메트릭"},
    ],
)

# Middlewares (order matters: last added = first executed)
# 1. Rate Limiting
setup_rate_limiting(app)

# 2. Request Logging
app.add_middleware(RequestLoggingMiddleware)

# 3. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. CORS (configured from environment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)
app.include_router(pipeline_router, prefix="/api/v1/pipelines", tags=["Pipelines"])

# Note: Outliers router is already included via api_router in __init__.py
# Removed duplicate registration to avoid duplicated endpoints

# Register WebSocket routes (Expert Recommendation: Real-time Metrics)
from app.routers.websocket import router as websocket_router
app.include_router(websocket_router, tags=["WebSocket"])

# Register Agent routes (Chat-based Creator Interface)
from app.routers.agent import router as agent_router
app.include_router(agent_router, tags=["Agent"])

# Register Coaching routes (Audio Coach Sessions)
from app.routers.coaching import router as coaching_router
app.include_router(coaching_router, tags=["Coaching"])


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    redis_status = "connected" if cache._client else "disconnected"
    neo4j_status = "connected" if graph_db._driver else "disconnected"
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "redis": redis_status,
            "neo4j": neo4j_status,
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "disabled",
    }
