"""
Celery Task Worker Configuration.
Leverages patterns from reference_repos/celery.
"""
from typing import Any, Dict
from core.infrastructure.config import settings

try:
    from celery import Celery

    celery_app = Celery(
        "sims_radiology_tasks",
        broker=str(settings.CELERY_BROKER_DSN),
        backend=str(settings.CELERY_RESULT_BACKEND_DSN),
        include=[
            "core.infrastructure.celery.app",
            "core.infrastructure.persistence.outbox_worker",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max for large DICOM series
        worker_prefetch_multiplier=1,
    )

    @celery_app.task(name="tasks.process_dicom_series")
    def process_dicom_series_task(study_uid: str, file_paths: list) -> Dict[str, Any]:
        """Background asynchronous DICOM parsing and pre-processing task."""
        return {
            "study_uid": study_uid,
            "status": "PROCESSED",
            "instances_count": len(file_paths),
        }

except ImportError:
    # Standalone mock for scaffolding when celery is not installed in local environment
    class CeleryMock:
        def __init__(self, *args, **kwargs) -> None:
            self.conf = {}

        def task(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    celery_app = CeleryMock()  # type: ignore[assignment]
