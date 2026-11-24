"""
Health Check and Subsystem Diagnostics Presentation Layer.
"""
from typing import Any, Dict
from fastapi import APIRouter, status
from core.infrastructure.config import settings
from core.infrastructure.kestra.client import kestra_client
from core.infrastructure.langfuse.client import langfuse_service

router = APIRouter(tags=["Health & Status"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Scaffold Liveness & Readiness Probe",
    response_description="Returns 200 OK with clean configuration loading and subsystem readiness status",
)
async def get_health() -> Dict[str, Any]:
    """
    Scaffold health endpoint confirming that the SIMS Radiology platform
    is initialized and configuration variables have loaded cleanly.
    """
    return {
        "status": "healthy",
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "api_version": "v1",
        "config_loaded": True,
        "subsystems": {
            "postgres": {
                "server": settings.POSTGRES_SERVER,
                "database": settings.POSTGRES_DB,
                "status": "configured",
            },
            "redis_celery": {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "status": "configured",
            },
            "langfuse": {
                "host": settings.LANGFUSE_HOST,
                "enabled": settings.LANGFUSE_ENABLED,
                "status": "configured",
            },
            "kestra": {
                "host": settings.KESTRA_API_HOST,
                "namespace": settings.KESTRA_NAMESPACE,
                "status": "configured",
            },
            "guardrails": {
                "framework": "NVIDIA NeMo Guardrails",
                "status": "initialized",
            },
            "agentic_framework": {
                "framework": "Deep Agents & LangGraph",
                "status": "initialized",
            },
        },
    }
