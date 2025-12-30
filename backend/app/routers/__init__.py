"""
API Routers package (PEGL v1.0)
"""
from fastapi import APIRouter

# Main API router
api_router = APIRouter(prefix="/api/v1")

# Import and include sub-routers
from app.routers.remix import router as remix_router
from app.routers.auth import router as auth_router
from app.routers.o2o import router as o2o_router
from app.routers.royalty import router as royalty_router
from app.routers.gamification import router as gamification_router
from app.routers.notebook_library import router as notebook_library_router
from app.routers.template_seeds import router as template_seeds_router
from app.routers.calibration import router as calibration_router
from app.routers.outliers import router as outliers_router
from app.routers.crawlers import router as crawlers_router
from app.routers.boards import router as boards_router
from app.routers.knowledge import router as knowledge_router
from app.routers.patterns import router as patterns_router
from app.routers.analytics import router as analytics_router
from app.routers.ingest import router as ingest_router
from app.routers.events import router as events_router
from app.routers.template_customization import router as template_customization_router
from app.routers.ops import router as ops_router  # PEGL v1.0 P0-7
from app.routers.monitoring import router as monitoring_router  # PEGL v1.0
from app.routers.creator import router as creator_router  # P2 Feedback Loop
from app.routers.usage import router as usage_router  # Week 2: Creator Usage Tracking
from app.routers.for_you import router as for_you_router  # For You API (MCP Ready)
from app.routers.coaching import router as coaching_router  # Audio Coach API
from app.routers.clusters import router as clusters_router  # P2 Cluster Management
from app.routers.distill import router as distill_router  # P3 DistillRun Automation

api_router.include_router(remix_router, prefix="/remix", tags=["Remix"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(o2o_router, prefix="/o2o", tags=["O2O"])
api_router.include_router(royalty_router, tags=["Royalty"])
api_router.include_router(gamification_router, prefix="/gamification", tags=["Gamification"])
api_router.include_router(notebook_library_router, tags=["NotebookLibrary"])
api_router.include_router(template_seeds_router, tags=["TemplateSeeds"])
api_router.include_router(calibration_router, tags=["Calibration"])
api_router.include_router(outliers_router, tags=["Outliers"])
api_router.include_router(crawlers_router, tags=["Crawlers"])
api_router.include_router(boards_router, tags=["Evidence Boards"])
api_router.include_router(knowledge_router, tags=["Knowledge Center"])
api_router.include_router(patterns_router, tags=["Patterns"])
api_router.include_router(analytics_router, tags=["Analytics"])
api_router.include_router(ingest_router, tags=["Ingest"])
api_router.include_router(events_router, tags=["Events"])
api_router.include_router(template_customization_router, tags=["Templates"])
api_router.include_router(ops_router, tags=["Ops Console"])  # PEGL v1.0 P0-7
api_router.include_router(monitoring_router, tags=["Monitoring"])  # PEGL v1.0
api_router.include_router(creator_router, tags=["Creator"])  # P2 Feedback Loop
api_router.include_router(usage_router, tags=["Usage Tracking"])  # Week 2
api_router.include_router(for_you_router, tags=["For You"])  # MCP Ready
api_router.include_router(coaching_router, tags=["Coaching"])  # Audio Coach API
api_router.include_router(clusters_router, tags=["Clusters"])  # P2 Cluster Management
api_router.include_router(distill_router, tags=["Distill"])  # P3 DistillRun Automation

