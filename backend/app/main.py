import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal, get_db
from backend.app.api import api_router
from backend.app.services.aggregator import CloudDataAggregator
from backend.app.services.optimizer import CostOptimizationEngine
from backend.app.services.alerting import AlertEngine
from backend.app.metrics.prometheus import get_prometheus_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("devops_dashboard")

scheduler = AsyncIOScheduler()


async def scheduled_cloud_sync():
    """Periodic background job to sync cloud costs and evaluate alerts"""
    logger.info("Executing scheduled multi-cloud synchronization job...")
    db = SessionLocal()
    try:
        CloudDataAggregator.sync_all_clouds(db, days_back=30)
        CostOptimizationEngine.evaluate_optimizations(db)
        await AlertEngine.evaluate_rules(db)
        logger.info("Scheduled synchronization finished successfully.")
    except Exception as e:
        logger.error(f"Error during scheduled sync: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)

    # Initial data seeding if database is fresh
    db = SessionLocal()
    try:
        from backend.app.models import CostRecord
        if db.query(CostRecord).count() == 0:
            logger.info("Fresh database detected. Performing initial multi-cloud ingestion...")
            CloudDataAggregator.sync_all_clouds(db, days_back=30)
            CostOptimizationEngine.evaluate_optimizations(db)
            AlertEngine.initialize_default_rules(db)
            await AlertEngine.evaluate_rules(db)
    except Exception as e:
        logger.error(f"Error initializing initial data: {e}")
    finally:
        db.close()

    # Start background scheduler
    try:
        scheduler.add_job(
            scheduled_cloud_sync,
            "interval",
            hours=settings.SYNC_INTERVAL_HOURS,
            id="multi_cloud_sync_job"
        )
        scheduler.start()
        logger.info(f"Background scheduler started (interval: {settings.SYNC_INTERVAL_HOURS} hours)")
    except Exception as e:
        logger.warning(f"Could not start scheduler: {e}")

    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Centralized Multi-Cloud (AWS, Azure, GCP) DevOps Resource & Cost Monitoring Dashboard API",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


# Health check endpoint
@app.get("/healthz", tags=["System"])
def healthcheck(db: Session = Depends(get_db)):
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "mock_mode": settings.MOCK_CLOUD_MODE
    }


# Prometheus /metrics endpoint
@app.get("/metrics", tags=["System"])
def prometheus_metrics(db: Session = Depends(get_db)):
    metrics_data = get_prometheus_metrics(db)
    return Response(content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8")


# Static Frontend mount
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return HTMLResponse("<h1>DevOps Cost Dashboard Backend Running</h1><p>Visit <a href='/docs'>/docs</a> for API.</p>")
