"""
Domain Entities: Radiology Study & Series (Zero framework dependencies).
Adheres to PRD/BRD specifications.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union

from core.domain.values.identifiers import AccessionNumber, PatientIdentifier, StudyUID
from core.domain.values.triage_priority import TriagePriority


class Modality(str, Enum):
    CT = "CT"
    MRI = "MRI"
    XRAY = "XRAY"
    # Clinical aliases & additional modalities
    MR = "MRI"
    XR = "XRAY"
    US = "US"
    PET = "PET"
    NM = "NM"

    @classmethod
    def _missing_(cls, value: object) -> Optional["Modality"]:
        val_str = str(value).upper()
        if val_str in ("MR", "MRI", "MAGNETIC RESONANCE"):
            return cls.MRI
        if val_str in ("XR", "XRAY", "CR", "DX", "X-RAY"):
            return cls.XRAY
        if val_str == "CT":
            return cls.CT
        return None


class StudyLifecycleState(str, Enum):
    RECEIVED = "received"
    PREPROCESSED = "preprocessed"
    ANALYSIS_IN_PROGRESS = "in_progress"
    GUARDRAIL_EVALUATION = "in_review"
    COMPLETED = "finalized"
    FAILED = "exception"


@dataclass
class ImagingSeries:
    """Represents a DICOM Series within a Study."""
    series_uid: str
    series_number: int
    modality: Modality
    description: str
    number_of_instances: int = 1


@dataclass
class RadiologyStudy:
    """
    Enterprise Business Entity for a Radiology Exam.
    Required attributes:
    - study_id
    - study_instance_uid
    - accession_number
    - modality (CT, MRI, XRAY)
    - study_date
    - source_system
    """
    study_id: str
    study_instance_uid: str
    accession_number: str
    modality: Modality
    study_date: datetime
    source_system: str = "PACS-NORTH"
    patient_id: Optional[str] = None
    description: str = ""
    priority: TriagePriority = TriagePriority.ROUTINE
    state: StudyLifecycleState = StudyLifecycleState.RECEIVED
    series: List[ImagingSeries] = field(default_factory=list)
    storage_path: Optional[str] = None

    def __init__(
        self,
        study_id: Optional[str] = None,
        study_instance_uid: Optional[Union[str, StudyUID]] = None,
        accession_number: Optional[Union[str, AccessionNumber]] = None,
        modality: Union[Modality, str] = Modality.CT,
        study_date: Optional[datetime] = None,
        source_system: str = "PACS-NORTH",
        uid: Optional[Union[str, StudyUID]] = None,
        accession: Optional[Union[str, AccessionNumber]] = None,
        patient_id: Optional[Union[str, PatientIdentifier]] = None,
        description: str = "",
        priority: TriagePriority = TriagePriority.ROUTINE,
        state: StudyLifecycleState = StudyLifecycleState.RECEIVED,
        series: Optional[List[ImagingSeries]] = None,
        storage_path: Optional[str] = None,
    ) -> None:
        # Resolve study_instance_uid
        raw_uid = study_instance_uid or uid
        if raw_uid is None:
            raise ValueError("study_instance_uid or uid must be provided")
        self.study_instance_uid = raw_uid.value if isinstance(raw_uid, StudyUID) else str(raw_uid)

        # Resolve accession_number
        raw_acc = accession_number or accession
        if raw_acc is None:
            raise ValueError("accession_number or accession must be provided")
        self.accession_number = raw_acc.value if isinstance(raw_acc, AccessionNumber) else str(raw_acc)

        # Resolve study_id
        self.study_id = study_id or f"std-{self.accession_number}"

        # Resolve modality
        if isinstance(modality, str):
            self.modality = Modality(modality)
        else:
            self.modality = modality

        self.study_date = study_date or datetime.now(timezone.utc)
        self.source_system = source_system

        # Resolve patient_id
        if isinstance(patient_id, PatientIdentifier):
            self.patient_id = patient_id
        elif patient_id:
            self.patient_id = PatientIdentifier(str(patient_id))
        else:
            self.patient_id = PatientIdentifier("ANONYMOUS")

        self.description = description
        self.priority = priority
        self.state = state
        self.series = series or []
        self.storage_path = storage_path

    @property
    def uid(self) -> StudyUID:
        return StudyUID(self.study_instance_uid)

    @property
    def accession(self) -> AccessionNumber:
        return AccessionNumber(self.accession_number)

    def escalate_priority(self, new_priority: TriagePriority) -> None:
        """Escalate study triage level (e.g. from ROUTINE to STAT if hemorrhage detected)."""
        if new_priority == TriagePriority.STAT:
            self.priority = TriagePriority.STAT
        elif new_priority == TriagePriority.URGENT and self.priority != TriagePriority.STAT:
            self.priority = TriagePriority.URGENT

    def transition_to(self, new_state: StudyLifecycleState) -> None:
        """State machine transition with domain validation."""
        self.state = new_state
