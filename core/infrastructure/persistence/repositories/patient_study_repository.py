"""
Concrete PatientRepository and StudyRepository implementations.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.study import Modality, RadiologyStudy, StudyLifecycleState
from core.domain.values.identifiers import AccessionNumber, PatientIdentifier, StudyUID
from core.domain.values.triage_priority import TriagePriority
from core.infrastructure.persistence.models import PatientModel, StudyModel


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(m: PatientModel) -> Patient:
        return Patient(
            patient_id=m.id,
            mrn=m.mrn,
            identifier_namespace=m.identifier_namespace,
            reconciliation_status=ReconciliationStatus(m.reconciliation_status),
            family_name=m.family_name,
            given_name=m.given_name,
            birth_date=m.birth_date,
            gender=m.gender,
        )

    async def create(self, patient: Patient) -> Patient:
        model = PatientModel(
            id=patient.patient_id,
            mrn=patient.mrn,
            identifier_namespace=patient.identifier_namespace,
            reconciliation_status=patient.reconciliation_status.value,
            family_name=patient.family_name,
            given_name=patient.given_name,
            birth_date=patient.birth_date,
            gender=patient.gender,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        query = select(PatientModel).where(PatientModel.id == patient_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_mrn(self, mrn: str, namespace: Optional[str] = None) -> Optional[Patient]:
        query = select(PatientModel).where(PatientModel.mrn == mrn)
        if namespace:
            query = query.where(PatientModel.identifier_namespace == namespace)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None


class StudyPersistenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(m: StudyModel) -> RadiologyStudy:
        return RadiologyStudy(
            study_id=m.id,
            study_instance_uid=m.study_instance_uid,
            accession_number=m.accession_number,
            modality=Modality(m.modality),
            study_date=m.study_date,
            source_system=m.source_system,
            patient_id=m.patient_id,
            description=m.description,
            priority=TriagePriority(m.priority),
            state=StudyLifecycleState(m.state),
            storage_path=m.storage_path,
        )

    async def create(self, study: RadiologyStudy) -> RadiologyStudy:
        model = StudyModel(
            id=study.study_id,
            study_instance_uid=study.study_instance_uid,
            accession_number=study.accession_number,
            patient_id=str(study.patient_id),
            modality=study.modality.value,
            study_date=study.study_date,
            source_system=study.source_system,
            description=study.description,
            priority=study.priority.value,
            state=study.state.value,
            storage_path=study.storage_path,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def get_by_id(self, study_id: str) -> Optional[RadiologyStudy]:
        query = select(StudyModel).where(StudyModel.id == study_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_uid(self, uid: str) -> Optional[RadiologyStudy]:
        query = select(StudyModel).where(StudyModel.study_instance_uid == uid)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_study_instance_uid(self, uid: str) -> Optional[RadiologyStudy]:
        return await self.get_by_uid(uid)
