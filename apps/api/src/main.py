"""
SIMS Radiology AI Operating Agentic Platform - Presentation Layer.
FastAPI Main Application.
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.middleware.correlation import CorrelationIdMiddleware, register_error_handlers
from apps.api.routes import api_router
from apps.api.src.endpoints.health import router as health_router
from apps.api.src.endpoints.integrations import router as legacy_integrations_router
from apps.api.src.endpoints.studies import router as studies_router
from apps.api.src.endpoints.triage import router as triage_router
from core.infrastructure.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sims_radiology.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SIMS Radiology AI Platform subsystems...")
    logger.info(f"Loaded Configuration for Environment: {settings.ENVIRONMENT}")
    logger.info(f"PostgreSQL Target: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
    logger.info(f"Celery Broker: {settings.CELERY_BROKER_DSN}")
    logger.info(f"Langfuse Target: {settings.LANGFUSE_HOST}")
    logger.info(f"Kestra Target: {settings.KESTRA_API_HOST}")
    yield
    logger.info("Gracefully shutting down SIMS Radiology AI Platform.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Enterprise Radiology AI Agentic Operating Platform following Clean Architecture.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# 1. Register Middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Register Global Structured Error Handlers
register_error_handlers(app)

# 3. Mount Presentation & Domain Routers
# Mount core Clean Architecture API v1 routes (work-items, reports, metrics, integrations/health)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount baseline endpoints
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(health_router)  # Also mount /health at root for docker container health checks
app.include_router(studies_router, prefix=settings.API_V1_STR)
app.include_router(triage_router, prefix=settings.API_V1_STR)
app.include_router(legacy_integrations_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to SIMS Radiology AI Operating Agentic Platform",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
