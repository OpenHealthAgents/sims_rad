"""
Core Domain Exceptions for the SIMS Radiology Platform.
Strictly decoupled from external framework and infrastructure concerns.
"""


class DomainException(Exception):
    """Base exception for all domain-specific errors in SIMS Radiology Platform."""
    pass


class InvalidStateTransitionError(DomainException):
    """
    Raised when an attempted state transition violates the deterministic
    state machine rules or lifecycle flow.
    """
    def __init__(self, from_state: str, to_state: str, reason: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        msg = f"Invalid state transition from '{from_state}' to '{to_state}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


class PatientMismatchError(DomainException):
    """
    Raised when patient reconciliation fails or violates RULE-01
    (Never match solely on name/DOB; must match against authoritative identifier namespace/MRN).
    """
    pass


class UnauthorizedSignoffError(DomainException):
    """
    Raised when an unauthorized actor attempts to sign, release, or amend a radiology report.
    """
    pass


class ImmutableReportOverrideError(DomainException):
    """
    Raised when an attempt is made to mutate or override an immutable ReportVersion
    or an already signed/released report without proper version amendment.
    """
    pass


class ClinicalWritebackBlockedError(DomainException):
    """
    Raised when clinical writeback is attempted while the study/work item
    is in `reconciliation_required` state.
    """
    pass


class ConcurrencyVersionError(DomainException):
    """
    Raised when optimistic locking check fails due to concurrent work item modifications.
    """
    pass


class StudyNotFoundError(DomainException):
    """Raised when an imaging study cannot be found."""
    pass


class InvalidDICOMMetadataError(DomainException):
    """Raised when required DICOM tags or header fields are invalid or missing."""
    pass


class GuardrailViolationError(DomainException):
    """Raised when NeMo safety guardrails detect an unsafe finding or output."""
    pass


class TriagePolicyViolationError(DomainException):
    """Raised when study priority or reporting breaches hospital clinical SLA."""
    pass
