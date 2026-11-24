"""
Domain Identifiers and Value Objects (Zero dependencies).
"""
from dataclasses import dataclass
import re
from core.domain.exceptions import InvalidDICOMMetadataError


@dataclass(frozen=True)
class StudyUID:
    """DICOM Study Instance UID according to ISO DICOM PS 3.5 standard."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) > 64:
            raise InvalidDICOMMetadataError(
                f"Invalid DICOM Study Instance UID length ({len(self.value)}): UID must be 1-64 chars."
            )
        # Standard DICOM UID format (digits and dots)
        if not re.match(r"^[0-9]+(\.[0-9]+)*$", self.value):
            raise InvalidDICOMMetadataError(f"Malformed DICOM Study UID format: {self.value}")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StudyUID):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False


@dataclass(frozen=True)
class AccessionNumber:
    """Hospital RIS/PACS Accession Number identifier."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidDICOMMetadataError("Accession number cannot be empty.")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AccessionNumber):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False


@dataclass(frozen=True)
class PatientIdentifier:
    """De-identified or institutional patient identifier."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidDICOMMetadataError("Patient ID cannot be empty.")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PatientIdentifier):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False
