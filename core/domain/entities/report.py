"""
Domain Entities: Report, ReportVersion, and Findings (Clean Architecture).
Enforces immutability invariants and authorized sign-off policies.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from core.domain.exceptions import ImmutableReportOverrideError, UnauthorizedSignoffError


class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    SIGNED = "SIGNED"
    RELEASED = "RELEASED"
    AMENDED = "AMENDED"


@dataclass(frozen=True)
class ReportVersion:
    """
    Immutable representation of a specific diagnostic report iteration.
    Once created, this snapshot cannot be altered.
    """
    version_number: int
    structured_findings: Dict[str, Any]
    impression: str
    author_id: str
    signature_hash: Optional[str] = None
    signed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.version_number < 1:
            raise ValueError("version_number must be >= 1.")
        if not self.author_id or not self.author_id.strip():
            raise ValueError("author_id cannot be empty.")
        if not self.impression or not self.impression.strip():
            raise ValueError("impression cannot be empty.")


@dataclass
class Finding:
    """Represents a localized radiographic abnormality detected by AI or clinician."""
    id: str
    label: str
    confidence: float
    anatomical_location: str
    is_critical: bool
    shap_attribution_score: Optional[float] = None
    slice_index: Optional[int] = None


@dataclass
class Report:
    """
    Radiology diagnostic report aggregate root.
    Required attributes:
    - report_id
    - work_item_id
    - status (DRAFT, SUBMITTED, SIGNED, RELEASED, AMENDED)
    - current_version_id
    """
    report_id: str
    work_item_id: str
    status: ReportStatus = ReportStatus.DRAFT
    current_version_id: Optional[str] = None
    versions: Dict[int, ReportVersion] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_version(self, version: ReportVersion) -> str:
        """
        Add a new immutable report version.
        Guarantees that existing versions cannot be overridden.
        """
        if version.version_number in self.versions:
            raise ImmutableReportOverrideError(
                f"Version {version.version_number} already exists for report {self.report_id}. "
                "Report versions are strictly immutable and cannot be overwritten."
            )

        # Ensure monotonic version increment
        expected_ver = len(self.versions) + 1
        if version.version_number != expected_ver:
            raise ImmutableReportOverrideError(
                f"Invalid version increment: Expected version {expected_ver}, got {version.version_number}."
            )

        self.versions[version.version_number] = version
        version_id = f"{self.report_id}-v{version.version_number}"
        self.current_version_id = version_id
        self.updated_at = datetime.now(timezone.utc)
        return version_id

    def submit_for_review(self) -> None:
        """Move report from DRAFT to SUBMITTED."""
        if not self.versions:
            raise ValueError("Cannot submit report without at least one version.")
        if self.status in (ReportStatus.SIGNED, ReportStatus.RELEASED):
            raise ImmutableReportOverrideError(f"Cannot submit an already {self.status.value} report.")
        self.status = ReportStatus.SUBMITTED
        self.updated_at = datetime.now(timezone.utc)

    def sign_and_release(
        self,
        radiologist_id: str,
        signature_hash: str,
        authorized_radiologists: Optional[List[str]] = None,
    ) -> ReportVersion:
        """
        Sign and release the current report version.
        Requires valid signature hash and authorized credentials.
        """
        if not self.current_version_id or not self.versions:
            raise ValueError("Cannot sign report with no versions.")

        # Check authorization if an authorized list is supplied
        if authorized_radiologists is not None and radiologist_id not in authorized_radiologists:
            raise UnauthorizedSignoffError(
                f"Radiologist '{radiologist_id}' is not authorized to sign report {self.report_id}."
            )

        if not signature_hash or not signature_hash.strip():
            raise UnauthorizedSignoffError("Cryptographic signature_hash is mandatory for report sign-off.")

        curr_ver_num = len(self.versions)
        current_ver = self.versions[curr_ver_num]

        # Produce signed immutable version
        signed_ver = ReportVersion(
            version_number=current_ver.version_number,
            structured_findings=current_ver.structured_findings,
            impression=current_ver.impression,
            author_id=current_ver.author_id,
            signature_hash=signature_hash,
            signed_at=datetime.now(timezone.utc),
            created_at=current_ver.created_at,
        )

        # Replace dictionary entry with signed copy (only allowed at initial signoff)
        if current_ver.signature_hash is not None:
            raise ImmutableReportOverrideError("Version has already been signed.")

        self.versions[curr_ver_num] = signed_ver
        self.status = ReportStatus.SIGNED
        self.updated_at = datetime.now(timezone.utc)
        return signed_ver

    def release(self) -> None:
        """Release a signed report to external systems/EHR."""
        if self.status != ReportStatus.SIGNED and self.status != ReportStatus.AMENDED:
            raise InvalidStateTransitionError_fallback(
                f"Cannot release report in '{self.status.value}' status. Must be SIGNED or AMENDED."
            )
        self.status = ReportStatus.RELEASED
        self.updated_at = datetime.now(timezone.utc)

    def amend(self, amended_version: ReportVersion) -> str:
        """
        Create an amendment version for an already signed or released report.
        """
        if self.status not in (ReportStatus.SIGNED, ReportStatus.RELEASED, ReportStatus.AMENDED):
            raise ImmutableReportOverrideError(
                f"Cannot amend report in '{self.status.value}' status. Only SIGNED or RELEASED reports can be amended."
            )

        version_id = self.add_version(amended_version)
        self.status = ReportStatus.AMENDED
        return version_id


def InvalidStateTransitionError_fallback(msg: str) -> Exception:
    from core.domain.exceptions import InvalidStateTransitionError
    return InvalidStateTransitionError(from_state="REPORT", to_state="RELEASED", reason=msg)


# Maintain backward compatibility for previous RadiologyReport entity
@dataclass
class RadiologyReport:
    """Legacy compatibility entity for earlier tests."""
    id: str
    study_uid: str
    created_at: datetime
    clinical_history: str
    technique: str
    findings: List[Finding] = field(default_factory=list)
    impression: str = ""
    is_verified_by_guardrails: bool = False
    is_signed_off: bool = False
    radiologist_id: Optional[str] = None

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    @property
    def has_critical_findings(self) -> bool:
        return any(f.is_critical for f in self.findings)
