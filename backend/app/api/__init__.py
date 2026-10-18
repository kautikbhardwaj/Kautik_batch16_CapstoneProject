from fastapi import APIRouter
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.costs import router as costs_router
from backend.app.api.resources import router as resources_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.recommendations import router as recommendations_router
from backend.app.api.sync import router as sync_router

api_router = APIRouter(prefix="/api")
api_router.include_router(dashboard_router)
api_router.include_router(costs_router)
api_router.include_router(resources_router)
api_router.include_router(alerts_router)
api_router.include_router(recommendations_router)
api_router.include_router(sync_router)
