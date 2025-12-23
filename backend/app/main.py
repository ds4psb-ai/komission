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
    title="Komission FACTORY v5.2 API",
    description="Hybrid Intelligence MVP Backend",
    version="5.2.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
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

# Register WebSocket routes (Expert Recommendation: Real-time Metrics)
from app.routers.websocket import router as websocket_router
app.include_router(websocket_router, tags=["WebSocket"])


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
