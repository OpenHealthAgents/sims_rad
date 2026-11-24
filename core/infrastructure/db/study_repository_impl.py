"""
Study Repository Implementation (Clean Architecture Adapter).
Supports both PostgreSQL via SQLAlchemy and in-memory cache for standalone execution.
"""
from typing import Dict, List, Optional
from core.application.interfaces.study_repository import StudyRepositoryInterface
from core.domain.entities.study import ImagingSeries, RadiologyStudy, StudyLifecycleState
from core.domain.values.identifiers import AccessionNumber, PatientIdentifier, StudyUID
from core.domain.values.triage_priority import Modality, TriagePriority


class InMemoryStudyRepository(StudyRepositoryInterface):
    """In-memory implementation for isolated tests and scaffold startup."""

    def __init__(self) -> None:
        self._storage: Dict[str, RadiologyStudy] = {}

    async def get_by_uid(self, uid: str) -> Optional[RadiologyStudy]:
        return self._storage.get(uid)

    async def save(self, study: RadiologyStudy) -> RadiologyStudy:
        self._storage[study.uid.value] = study
        return study

    async def list_recent(self, limit: int = 50) -> List[RadiologyStudy]:
        studies = list(self._storage.values())
        return studies[-limit:]


# Default repository instance
study_repository: StudyRepositoryInterface = InMemoryStudyRepository()
