"""
Concrete AuditRepository implementing transactional logging and transactional outbox.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.entities.audit_log import AuditLog
from core.infrastructure.persistence.models import AuditEventModel, OutboxEventModel


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(m: AuditEventModel) -> AuditLog:
        return AuditLog(
            actor_id=m.actor_id,
            action=m.action,
            resource_id=m.resource_id,
            timestamp=m.timestamp,
            correlation_id=m.correlation_id,
            details=m.details,
        )

    async def record(self, audit_log: AuditLog) -> AuditLog:
        """Persist an immutable audit log entry."""
        model = AuditEventModel(
            id=f"aud-{uuid.uuid4().hex[:16]}",
            actor_id=audit_log.actor_id,
            action=audit_log.action,
            resource_id=audit_log.resource_id,
            timestamp=audit_log.timestamp,
            correlation_id=audit_log.correlation_id,
            details=audit_log.details,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def record_with_outbox(
        self,
        audit_log: AuditLog,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> OutboxEventModel:
        """
        Atomically persist both an AuditLog and an OutboxEvent within the same transaction.
        Enforces the Transactional Outbox pattern.
        """
        # 1. Audit Event
        audit_model = AuditEventModel(
            id=f"aud-{uuid.uuid4().hex[:16]}",
            actor_id=audit_log.actor_id,
            action=audit_log.action,
            resource_id=audit_log.resource_id,
            timestamp=audit_log.timestamp,
            correlation_id=audit_log.correlation_id,
            details=audit_log.details,
        )
        self.session.add(audit_model)

        # 2. Outbox Event
        outbox_model = OutboxEventModel(
            id=f"evt-{uuid.uuid4().hex[:16]}",
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(timezone.utc),
            processed_at=None,
        )
        self.session.add(outbox_model)

        await self.session.flush()
        return outbox_model

    async def get_by_resource_id(self, resource_id: str) -> List[AuditLog]:
        query = (
            select(AuditEventModel)
            .where(AuditEventModel.resource_id == resource_id)
            .order_by(AuditEventModel.timestamp.asc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_by_correlation_id(self, correlation_id: str) -> List[AuditLog]:
        query = (
            select(AuditEventModel)
            .where(AuditEventModel.correlation_id == correlation_id)
            .order_by(AuditEventModel.timestamp.asc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_unprocessed_outbox_events(self, limit: int = 50) -> List[OutboxEventModel]:
        """Fetch pending outbox events ordered by creation time for sequential publishing."""
        query = (
            select(OutboxEventModel)
            .where(OutboxEventModel.processed_at.is_(None))
            .order_by(OutboxEventModel.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_outbox_processed(self, event_id: str) -> None:
        """Mark outbox event as successfully processed/published."""
        query = select(OutboxEventModel).where(OutboxEventModel.id == event_id)
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        if event:
            event.processed_at = datetime.now(timezone.utc)
            await self.session.flush()
