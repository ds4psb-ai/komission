"""
Health Check & Monitoring Utilities (PEGL v1.0)

운영 모니터링:
- 서비스 상태 체크
- 에러 알림
- 성능 메트릭
"""
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging

from app.services.cache import cache
from app.services.graph_db import graph_db
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class HealthChecker:
    """서비스 헬스 체크"""

    @staticmethod
    async def check_database() -> dict:
        """PostgreSQL 연결 확인"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute("SELECT 1")
                return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    async def check_redis() -> dict:
        """Redis 연결 확인"""
        try:
            if cache._client:
                start = datetime.now()
                await cache._client.ping()
                latency = (datetime.now() - start).total_seconds() * 1000
                return {"status": "healthy", "latency_ms": round(latency, 2)}
            return {"status": "disconnected"}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    async def check_neo4j() -> dict:
        """Neo4j 연결 확인"""
        try:
            if graph_db._driver:
                start = datetime.now()
                async with graph_db._driver.session() as session:
                    await session.run("RETURN 1")
                latency = (datetime.now() - start).total_seconds() * 1000
                return {"status": "healthy", "latency_ms": round(latency, 2)}
            return {"status": "disconnected"}
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    @classmethod
    async def check_all(cls) -> dict:
        """모든 서비스 상태 확인"""
        results = await asyncio.gather(
            cls.check_database(),
            cls.check_redis(),
            cls.check_neo4j(),
            return_exceptions=True
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": results[0] if not isinstance(results[0], Exception) else {"status": "error"},
                "redis": results[1] if not isinstance(results[1], Exception) else {"status": "error"},
                "neo4j": results[2] if not isinstance(results[2], Exception) else {"status": "error"},
            },
            "overall": "healthy" if all(
                r.get("status") == "healthy" for r in results if isinstance(r, dict)
            ) else "degraded"
        }


class MetricsCollector:
    """성능 메트릭 수집"""

    def __init__(self):
        self._request_count = 0
        self._error_count = 0
        self._latencies: list[float] = []
        self._start_time = datetime.now()

    def record_request(self, latency_ms: float, is_error: bool = False):
        """요청 기록"""
        self._request_count += 1
        self._latencies.append(latency_ms)
        if is_error:
            self._error_count += 1

        # 최근 1000개만 유지
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-1000:]

    def get_metrics(self) -> dict:
        """메트릭 반환"""
        uptime = datetime.now() - self._start_time
        avg_latency = sum(self._latencies) / len(self._latencies) if self._latencies else 0
        p95_latency = sorted(self._latencies)[int(len(self._latencies) * 0.95)] if len(self._latencies) > 20 else avg_latency

        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "error_rate": round(self._error_count / max(self._request_count, 1) * 100, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
        }


# 싱글톤 인스턴스
health_checker = HealthChecker()
metrics_collector = MetricsCollector()


async def send_alert(title: str, message: str, severity: str = "warning"):
    """
    알림 전송 (확장 가능)
    
    TODO: Slack, Discord, Email 등 연동
    """
    log_level = logging.ERROR if severity == "critical" else logging.WARNING
    logger.log(log_level, f"[ALERT] {title}: {message}")

    # 추후 Slack 등 연동
    # await slack_client.send(channel="#alerts", text=f"*{title}*\n{message}")
