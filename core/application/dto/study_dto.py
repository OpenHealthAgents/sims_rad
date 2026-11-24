"""
Application Layer DTOs: Study & Ingestion contracts (Pydantic v2).
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from core.domain.values.triage_priority import Modality, TriagePriority
from core.domain.entities.study import StudyLifecycleState


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ImagingSeriesDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    series_uid: str
    series_number: int
    modality: Modality
    description: str
    number_of_instances: int = 1


class StudyCreateRequestDTO(BaseModel):
    study_uid: str = Field(..., description="DICOM StudyInstanceUID (1-64 chars)")
    accession_number: str = Field(..., description="Hospital Accession Number")
    patient_id: str = Field(..., description="De-identified Patient ID")
    modality: Modality = Modality.CT
    description: str = Field(default="Head CT without contrast")
    priority: TriagePriority = TriagePriority.ROUTINE
    series: List[ImagingSeriesDTO] = Field(default_factory=list)


class StudyResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_uid: str
    accession_number: str
    patient_id: str
    modality: Modality
    study_date: datetime
    description: str
    priority: TriagePriority
    state: StudyLifecycleState
    series_count: int
    created_at: datetime = Field(default_factory=get_utc_now)
