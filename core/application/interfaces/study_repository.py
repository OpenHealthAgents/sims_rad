"""
Application Interface (Port) for Study Persistence.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.entities.study import RadiologyStudy


class StudyRepositoryInterface(ABC):
    @abstractmethod
    async def get_by_uid(self, uid: str) -> Optional[RadiologyStudy]:
        """Retrieve a study by its unique DICOM StudyInstanceUID."""
        pass

    @abstractmethod
    async def save(self, study: RadiologyStudy) -> RadiologyStudy:
        """Persist or update a radiology study."""
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 50) -> List[RadiologyStudy]:
        """List recently ingested or prioritized studies."""
        pass
