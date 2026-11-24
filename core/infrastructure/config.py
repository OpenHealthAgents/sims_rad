"""
Core Infrastructure Settings and Environment Validation Schema.
Configured via Pydantic Settings v2.
"""
from typing import List, Literal, Optional, Self
from pydantic import (
    Field,
    PostgresDsn,
    RedisDsn,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    SIMS Radiology AI Operating Platform Settings.
    Strictly validates all required environment variables for on-prem enterprise deployment.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # General & Project
    PROJECT_NAME: str = Field(default="SIMS Radiology AI Operating Agentic Platform")
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = Field(
        default="development"
    )
    API_V1_STR: str = Field(default="/api/v1")
    CORS_ORIGINS: List[str] = Field(default=["*"])

    # Security & Authentication
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="Cryptographic secret key for signing JWTs and session tokens",
    )
    SECURITY_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)  # 24 hours

    # Database Configuration (PostgreSQL 16)
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="sims_user")
    POSTGRES_PASSWORD: str = Field(default="sims_secret_password")
    POSTGRES_DB: str = Field(default="sims_radiology")
    POSTGRES_DSN: Optional[PostgresDsn] = Field(default=None)

    # Celery & Redis Configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    CELERY_BROKER_DSN: Optional[str] = Field(default=None)
    CELERY_RESULT_BACKEND_DSN: Optional[str] = Field(default=None)

    # Langfuse Observability & Evals
    LANGFUSE_HOST: str = Field(
        default="http://localhost:3000",
        description="Langfuse local server host URL",
    )
    LANGFUSE_PUBLIC_KEY: str = Field(
        default="pk-lf-sims-radiology-public-dev",
        description="Langfuse Public Key",
    )
    LANGFUSE_SECRET_KEY: str = Field(
        default="sk-lf-sims-radiology-secret-dev",
        description="Langfuse Secret Key",
    )
    LANGFUSE_ENABLED: bool = Field(default=True)

    # Kestra Orchestrator Host & Configuration
    KESTRA_API_HOST: str = Field(
        default="http://localhost:8080",
        description="Kestra standalone server host API endpoint",
    )
    KESTRA_NAMESPACE: str = Field(default="sims.radiology")
    KESTRA_TENANT_ID: Optional[str] = Field(default=None)

    # External Integration Adapters
    ORTHANC_DICOMWEB_URL: str = Field(
        default="http://localhost:8042/dicom-web",
        description="Orthanc PACS DICOMweb base endpoint",
    )
    BACKBONE_HMS_BASE_URL: str = Field(
        default="http://localhost:8081/api/v1",
        description="BackBone Hospital Management System endpoint",
    )
    CHARMHEALTH_BASE_URL: str = Field(
        default="http://localhost:8082/fhir/r4",
        description="CharmHealth EHR FHIR R4 endpoint",
    )

    @model_validator(mode="after")
    def assemble_dynamic_connections(self) -> Self:
        # Re-compute POSTGRES_DSN if server/db/user was provided or default
        if self.POSTGRES_DSN is None or self.POSTGRES_SERVER != "localhost":
            dsn_str = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            self.POSTGRES_DSN = PostgresDsn(dsn_str)

        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        if self.CELERY_BROKER_DSN is None or self.REDIS_HOST != "localhost":
            self.CELERY_BROKER_DSN = f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/0"

        if self.CELERY_RESULT_BACKEND_DSN is None or self.REDIS_HOST != "localhost":
            self.CELERY_RESULT_BACKEND_DSN = f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/1"

        return self


# Global settings instance singleton
settings = Settings()
