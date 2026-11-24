"""
Domain Entity: Patient (Clean Architecture).
Adheres to PRD/BRD specifications and RULE-01:
Never match solely on name/DOB; map against fhir-core standardized structures.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from core.domain.exceptions import PatientMismatchError


class ReconciliationStatus(str, Enum):
    RECONCILED = "reconciled"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    PENDING = "pending"


@dataclass
class Patient:
    """
    Patient domain entity representing a clinical subject.
    Enforces RULE-01: Authoritative matching must be verified via
    identifier namespace + MRN, never solely on demographic attributes (Name/DOB).
    """
    patient_id: str
    mrn: str
    identifier_namespace: str
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    birth_date: Optional[str] = None  # Format: YYYY-MM-DD
    gender: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.patient_id or not self.patient_id.strip():
            raise PatientMismatchError("patient_id cannot be empty.")
        if not self.mrn or not self.mrn.strip():
            raise PatientMismatchError("mrn cannot be empty for authoritative patient identification.")
        if not self.identifier_namespace or not self.identifier_namespace.strip():
            raise PatientMismatchError("identifier_namespace cannot be empty (RULE-01 requirement).")

    def match_with(
        self,
        candidate_mrn: Optional[str] = None,
        candidate_namespace: Optional[str] = None,
        candidate_name: Optional[str] = None,
        candidate_dob: Optional[str] = None,
    ) -> bool:
        """
        Enforce RULE-01:
        Matching must validate against authoritative identifier namespace + MRN.
        Attempts to match solely based on Name and/or DOB without matching MRN
        and namespace strictly raise PatientMismatchError.
        """
        # RULE-01 Check: If only demographic data (name/dob) is supplied without MRN/namespace:
        if not candidate_mrn or not candidate_namespace:
            raise PatientMismatchError(
                "RULE-01 Violation: Never match solely on name/DOB. "
                "Authoritative MRN and identifier_namespace are strictly mandatory."
            )

        # Check namespace and MRN exact equality
        if (
            self.identifier_namespace.strip() != candidate_namespace.strip()
            or self.mrn.strip() != candidate_mrn.strip()
        ):
            raise PatientMismatchError(
                f"Patient identifier mismatch: Expected {self.identifier_namespace}:{self.mrn}, "
                f"got {candidate_namespace}:{candidate_mrn}."
            )

        # If demographics provided, ensure they do not contradict
        if candidate_dob and self.birth_date and candidate_dob != self.birth_date:
            raise PatientMismatchError(
                f"Demographic contradiction during reconciliation: DOB {candidate_dob} != {self.birth_date}"
            )

        return True

    def mark_reconciled(self) -> None:
        """Mark patient identity as reconciled after authoritative validation."""
        self.reconciliation_status = ReconciliationStatus.RECONCILED

    def mark_reconciliation_required(self) -> None:
        """Flag patient identity as requiring clinical/HIM reconciliation."""
        self.reconciliation_status = ReconciliationStatus.RECONCILIATION_REQUIRED

    def to_fhir(self) -> Dict[str, Any]:
        """
        Map domain patient entity to standardized HL7 FHIR R4 Patient structure.
        Aligned with reference_repos/fhir-core schema.
        """
        fhir_patient: Dict[str, Any] = {
            "resourceType": "Patient",
            "id": self.patient_id,
            "identifier": [
                {
                    "use": "usual",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical Record Number",
                            }
                        ]
                    },
                    "system": self.identifier_namespace,
                    "value": self.mrn,
                }
            ],
            "active": True,
        }

        names: List[Dict[str, Any]] = []
        name_obj: Dict[str, Any] = {"use": "official"}
        if self.family_name:
            name_obj["family"] = self.family_name
        if self.given_name:
            name_obj["given"] = [self.given_name]
        if self.family_name or self.given_name:
            names.append(name_obj)
        if names:
            fhir_patient["name"] = names

        if self.gender:
            fhir_patient["gender"] = self.gender.lower()
        if self.birth_date:
            fhir_patient["birthDate"] = self.birth_date

        return fhir_patient

    @classmethod
    def from_fhir(cls, fhir_resource: Dict[str, Any]) -> "Patient":
        """
        Construct Patient entity from standardized FHIR R4 Patient resource.
        Enforces RULE-01: Must extract an authoritative MRN identifier with a namespace system.
        """
        if fhir_resource.get("resourceType") != "Patient":
            raise PatientMismatchError("Resource is not a valid FHIR Patient.")

        patient_id = fhir_resource.get("id") or ""
        identifiers = fhir_resource.get("identifier", [])

        # Search for valid MRN or primary identifier with system namespace
        mrn: Optional[str] = None
        namespace: Optional[str] = None

        for ident in identifiers:
            system = ident.get("system")
            val = ident.get("value")
            if system and val:
                # Prioritize MRN coding or take first valid namespaced identifier
                mrn = val
                namespace = system
                coding = ident.get("type", {}).get("coding", [])
                if any(c.get("code") == "MR" for c in coding):
                    break

        if not mrn or not namespace:
            raise PatientMismatchError(
                "RULE-01 Violation: FHIR Patient lacks authoritative namespaced identifier (MRN/system)."
            )

        # Extract demographics
        family_name = None
        given_name = None
        names = fhir_resource.get("name", [])
        if names and isinstance(names, list):
            primary_name = names[0]
            family_name = primary_name.get("family")
            given_list = primary_name.get("given", [])
            if given_list and isinstance(given_list, list):
                given_name = given_list[0]

        birth_date = fhir_resource.get("birthDate")
        gender = fhir_resource.get("gender")

        return cls(
            patient_id=patient_id or f"pat-{mrn}",
            mrn=mrn,
            identifier_namespace=namespace,
            reconciliation_status=ReconciliationStatus.RECONCILED,
            family_name=family_name,
            given_name=given_name,
            birth_date=birth_date,
            gender=gender,
        )
