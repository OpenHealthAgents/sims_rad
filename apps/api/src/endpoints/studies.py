"""
Radiology Studies API Endpoints.
"""
from typing import List
from fastapi import APIRouter, HTTPException, status
from core.application.dto.study_dto import StudyCreateRequestDTO, StudyResponseDTO
from core.application.use_cases.ingest_study import IngestStudyUseCase
from core.domain.exceptions import InvalidDICOMMetadataError
from core.infrastructure.db.study_repository_impl import study_repository

router = APIRouter(prefix="/studies", tags=["Radiology Studies"])
ingest_use_case = IngestStudyUseCase(repository=study_repository)


@router.post(
    "",
    response_model=StudyResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new DICOM Study",
)
async def ingest_study(dto: StudyCreateRequestDTO) -> StudyResponseDTO:
    try:
        return await ingest_use_case.execute(dto)
    except InvalidDICOMMetadataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Study ingestion failed: {e}",
        )


@router.get(
    "",
    response_model=List[StudyResponseDTO],
    summary="List recent radiology studies",
)
async def list_studies(limit: int = 50) -> List[StudyResponseDTO]:
    studies = await study_repository.list_recent(limit=limit)
    return [
        StudyResponseDTO(
            study_uid=s.uid.value,
            accession_number=s.accession.value,
            patient_id=s.patient_id.value,
            modality=s.modality,
            study_date=s.study_date,
            description=s.description,
            priority=s.priority,
            state=s.state,
            series_count=len(s.series),
        )
        for s in studies
    ]


@router.get(
    "/{study_uid}",
    response_model=StudyResponseDTO,
    summary="Get study details by UID",
)
async def get_study(study_uid: str) -> StudyResponseDTO:
    study = await study_repository.get_by_uid(study_uid)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study {study_uid} not found",
        )
    return StudyResponseDTO(
        study_uid=study.uid.value,
        accession_number=study.accession.value,
        patient_id=study.patient_id.value,
        modality=study.modality,
        study_date=study.study_date,
        description=study.description,
        priority=study.priority,
        state=study.state,
        series_count=len(study.series),
    )
