FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for imaging, postgres client, and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies for API, persistence, Celery outbox, and AI agents
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    asyncpg \
    "psycopg[binary]" \
    alembic \
    celery \
    redis \
    httpx \
    python-multipart \
    pydicom \
    numpy

# Copy active application code layers
COPY core/ core/
COPY agents/ agents/
COPY apps/ apps/
COPY kestra/ kestra/
COPY .env* ./

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.api.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
