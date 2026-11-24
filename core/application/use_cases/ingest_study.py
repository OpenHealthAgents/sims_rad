"""
Use Case: Ingest and Validate New Radiology Study.
"""
from datetime import datetime, timezone
from core.application.dto.study_dto import StudyCreateRequestDTO, StudyResponseDTO
from core.application.interfaces.study_repository import StudyRepositoryInterface
from core.domain.entities.study import ImagingSeries, RadiologyStudy, StudyLifecycleState
from core.domain.values.identifiers import AccessionNumber, PatientIdentifier, StudyUID


class IngestStudyUseCase:
    def __init__(self, repository: StudyRepositoryInterface) -> None:
        self.repository = repository

    async def execute(self, dto: StudyCreateRequestDTO) -> StudyResponseDTO:
        study = RadiologyStudy(
            uid=StudyUID(dto.study_uid),
            accession=AccessionNumber(dto.accession_number),
            patient_id=PatientIdentifier(dto.patient_id),
            modality=dto.modality,
            study_date=datetime.now(timezone.utc),
            description=dto.description,
            priority=dto.priority,
            state=StudyLifecycleState.RECEIVED,
            series=[
                ImagingSeries(
                    series_uid=s.series_uid,
                    series_number=s.series_number,
                    modality=s.modality,
                    description=s.description,
                    number_of_instances=s.number_of_instances,
                )
                for s in dto.series
            ],
        )

        saved = await self.repository.save(study)
        return StudyResponseDTO(
            study_uid=saved.uid.value,
            accession_number=saved.accession.value,
            patient_id=saved.patient_id.value,
            modality=saved.modality,
            study_date=saved.study_date,
            description=saved.description,
            priority=saved.priority,
            state=saved.state,
            series_count=len(saved.series),
        )
