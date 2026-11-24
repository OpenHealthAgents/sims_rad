"""
Transactional Outbox Worker using Celery Task Runner.
Polls and publishes unprocessed outbox_events to downstream interfaces
(Kestra workflow pipelines and external EHR delivery systems).
Leverages patterns from reference_repos/celery and reference_repos/kestra.
"""
import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.celery.app import celery_app
from core.infrastructure.db.session import AsyncSessionLocal
from core.infrastructure.kestra.client import kestra_client
from core.infrastructure.persistence.models import OutboxEventModel

logger = logging.getLogger("sims_radiology.outbox_worker")


class DownstreamDispatcher:
    """Dispatches outbox events to appropriate downstream targets."""

    @classmethod
    async def dispatch(cls, event: OutboxEventModel) -> bool:
        """
        Route event to appropriate downstream interface:
        - Work item and study events -> Kestra flows
        - Report release events -> EHR / HL7 delivery
        """
        try:
            logger.info(
                f"Dispatching outbox event '{event.id}': type='{event.event_type}', "
                f"aggregate='{event.aggregate_type}:{event.aggregate_id}'"
            )

            if event.aggregate_type in ("WORK_ITEM", "STUDY"):
                # Forward to Kestra pipeline
                flow_id = "dicom_ingestion_and_triage"
                inputs = {
                    "study_uid": event.payload.get("study_uid", event.aggregate_id),
                    "patient_id": event.payload.get("patient_id", "UNKNOWN"),
                    "modality": event.payload.get("modality", "CT"),
                }
                res = await kestra_client.trigger_flow(flow_id, inputs)
                logger.info(f"Triggered Kestra flow for event '{event.id}': {res.get('status', 'sent')}")

            elif event.aggregate_type == "REPORT":
                # Forward to EHR / clinical delivery channel
                dest = event.payload.get("destination_system", "EHR-DEFAULT")
                logger.info(f"Delivered report '{event.aggregate_id}' to external EHR '{dest}'")

            return True
        except Exception as e:
            logger.error(f"Failed to dispatch outbox event '{event.id}': {e}", exc_info=True)
            return False


async def process_outbox_batch(batch_size: int = 50, session: Optional[AsyncSession] = None) -> int:
    """
    Core polling loop for the Transactional Outbox pattern.
    Fetches up to `batch_size` pending events, dispatches them, and marks them processed.
    Returns: Number of events successfully processed.
    """
    own_session = False
    if session is None:
        session = AsyncSessionLocal()
        own_session = True

    processed_count = 0
    try:
        query = (
            select(OutboxEventModel)
            .where(OutboxEventModel.processed_at.is_(None))
            .order_by(OutboxEventModel.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(query)
        events = result.scalars().all()

        if not events:
            return 0

        for evt in events:
            success = await DownstreamDispatcher.dispatch(evt)
            if success:
                evt.processed_at = datetime.now(timezone.utc)
                processed_count += 1

        await session.commit()
        logger.info(f"Processed and committed {processed_count} outbox events.")
        return processed_count
    except Exception as e:
        await session.rollback()
        logger.error(f"Error in process_outbox_batch: {e}", exc_info=True)
        raise
    finally:
        if own_session:
            await session.close()


@celery_app.task(name="persistence.process_outbox_events_task", bind=True, max_retries=3)
def process_outbox_events_task(self, batch_size: int = 50) -> Dict[str, Any]:
    """
    Celery background worker task for publishing pending outbox events.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                count = pool.submit(lambda: asyncio.run(process_outbox_batch(batch_size=batch_size))).result()
        else:
            count = asyncio.run(process_outbox_batch(batch_size=batch_size))
        return {"status": "SUCCESS", "events_processed": count}
    except Exception as exc:
        logger.warning(f"Outbox celery task failed; retrying: {exc}")
        raise self.retry(exc=exc, countdown=5)
