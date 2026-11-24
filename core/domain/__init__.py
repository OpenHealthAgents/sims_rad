"""SIMS Radiology Domain Layer"""
from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.study import RadiologyStudy, ImagingSeries, Modality, StudyLifecycleState
from core.domain.entities.work_item import WorkItem, WorkItemState, Priority
from core.domain.entities.report import (
    Report,
    ReportVersion,
    ReportStatus,
    RadiologyReport,
    Finding,
)
from core.domain.entities.audit_log import AuditLog
from core.domain.values.identifiers import StudyUID, AccessionNumber, PatientIdentifier
from core.domain.values.triage_priority import TriagePriority
from core.domain.state_machine import RadiologyStateMachine, ALLOWED_TRANSITIONS
from core.domain.exceptions import (
    DomainException,
    InvalidStateTransitionError,
    PatientMismatchError,
    UnauthorizedSignoffError,
    ImmutableReportOverrideError,
    ClinicalWritebackBlockedError,
    ConcurrencyVersionError,
    StudyNotFoundError,
    InvalidDICOMMetadataError,
    GuardrailViolationError,
    TriagePolicyViolationError,
)

__all__ = [
    # Entities & Value Objects
    "Patient",
    "ReconciliationStatus",
    "RadiologyStudy",
    "ImagingSeries",
    "Modality",
    "StudyLifecycleState",
    "WorkItem",
    "WorkItemState",
    "Priority",
    "Report",
    "ReportVersion",
    "ReportStatus",
    "RadiologyReport",
    "Finding",
    "AuditLog",
    "StudyUID",
    "AccessionNumber",
    "PatientIdentifier",
    "TriagePriority",
    # State Machine
    "RadiologyStateMachine",
    "ALLOWED_TRANSITIONS",
    # Exceptions
    "DomainException",
    "InvalidStateTransitionError",
    "PatientMismatchError",
    "UnauthorizedSignoffError",
    "ImmutableReportOverrideError",
    "ClinicalWritebackBlockedError",
    "ConcurrencyVersionError",
    "StudyNotFoundError",
    "InvalidDICOMMetadataError",
    "GuardrailViolationError",
    "TriagePolicyViolationError",
]
