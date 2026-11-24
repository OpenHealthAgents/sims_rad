"""
Database Session and Engine Management (Async SQLAlchemy 2.0).
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from core.infrastructure.config import settings

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            str(settings.POSTGRES_DSN),
            echo=False,
            poolclass=NullPool,
        )
    return _engine


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            bind=get_async_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing transactional async database sessions."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
