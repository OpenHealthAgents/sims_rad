"""
Database Engine & Async Session Management.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from core.infrastructure.config import settings

# Async PostgreSQL Engine with NullPool to prevent event loop / thread binding issues
engine = create_async_engine(
    str(settings.POSTGRES_DSN),
    echo=False,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
