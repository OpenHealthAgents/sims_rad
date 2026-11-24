"""
Unit Tests: Pydantic Settings & Environment Validation Schema.
"""
from core.infrastructure.config import Settings


def test_settings_validation():
    s = Settings(
        POSTGRES_SERVER="db.hospital.internal",
        POSTGRES_PORT=5432,
        POSTGRES_USER="rad_user",
        POSTGRES_PASSWORD="rad_password",
        POSTGRES_DB="radiology_prod",
        REDIS_HOST="redis.hospital.internal",
        REDIS_PORT=6379,
        LANGFUSE_HOST="http://langfuse.hospital.internal:3000",
        KESTRA_API_HOST="http://kestra.hospital.internal:8080",
    )

    assert "postgresql+asyncpg://rad_user:rad_password@db.hospital.internal:5432/radiology_prod" in str(s.POSTGRES_DSN)
    assert "redis://redis.hospital.internal:6379/0" in str(s.CELERY_BROKER_DSN)
    assert s.LANGFUSE_HOST == "http://langfuse.hospital.internal:3000"
    assert s.KESTRA_API_HOST == "http://kestra.hospital.internal:8080"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 1440
