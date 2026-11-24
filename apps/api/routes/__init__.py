"""
API v1 Routes Package.
Exports all REST API routers for SIMS Radiology Platform.
"""
from fastapi import APIRouter

from apps.api.routes.agent_stream import router as agent_stream_router
from apps.api.routes.integrations_health import router as integrations_health_router
from apps.api.routes.metrics import router as metrics_router
from apps.api.routes.reports import router as reports_router
from apps.api.routes.work_items import router as work_items_router

api_router = APIRouter()

api_router.include_router(work_items_router)
api_router.include_router(reports_router)
api_router.include_router(metrics_router)
api_router.include_router(integrations_health_router)
api_router.include_router(agent_stream_router)

__all__ = [
    "api_router",
    "work_items_router",
    "reports_router",
    "metrics_router",
    "integrations_health_router",
    "agent_stream_router",
]
