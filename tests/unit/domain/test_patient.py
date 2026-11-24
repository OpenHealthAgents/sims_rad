"""
Unit Tests: Patient Domain Entity & RULE-01 Enforcement.
Validates authoritative identifier matching and FHIR R4 mappings.
"""
import pytest
from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.exceptions import PatientMismatchError


def test_patient_creation_success():
    patient = Patient(
        patient_id="pat-1001",
        mrn="MRN-884920",
        identifier_namespace="https://hospital.sims.org/patients",
        family_name="Doe",
        given_name="Jane",
        birth_date="1985-04-12",
        gender="female",
    )
    assert patient.patient_id == "pat-1001"
    assert patient.mrn == "MRN-884920"
    assert patient.identifier_namespace == "https://hospital.sims.org/patients"
    assert patient.reconciliation_status == ReconciliationStatus.PENDING


def test_patient_creation_empty_identifiers_fails():
    with pytest.raises(PatientMismatchError):
        Patient(patient_id="", mrn="123", identifier_namespace="https://sims.org")

    with pytest.raises(PatientMismatchError):
        Patient(patient_id="p1", mrn="", identifier_namespace="https://sims.org")

    with pytest.raises(PatientMismatchError):
        Patient(patient_id="p1", mrn="123", identifier_namespace="")


def test_rule_01_prohibits_matching_solely_on_name_dob():
    """RULE-01: Never match solely on name/DOB; must match against authoritative identifier."""
    patient = Patient(
        patient_id="pat-1001",
        mrn="MRN-884920",
        identifier_namespace="https://hospital.sims.org/patients",
        family_name="Smith",
        given_name="John",
        birth_date="1970-01-01",
    )

    # Attempting to match with name and DOB alone (without MRN/namespace) must be rejected
    with pytest.raises(PatientMismatchError, match="RULE-01 Violation"):
        patient.match_with(candidate_name="Smith", candidate_dob="1970-01-01")

    with pytest.raises(PatientMismatchError, match="RULE-01 Violation"):
        patient.match_with(candidate_mrn=None, candidate_namespace=None)


def test_matching_with_authoritative_identifiers_succeeds():
    patient = Patient(
        patient_id="pat-1001",
        mrn="MRN-884920",
        identifier_namespace="https://hospital.sims.org/patients",
        family_name="Smith",
        birth_date="1970-01-01",
    )

    is_matched = patient.match_with(
        candidate_mrn="MRN-884920",
        candidate_namespace="https://hospital.sims.org/patients",
        candidate_name="Smith",
        candidate_dob="1970-01-01",
    )
    assert is_matched is True


def test_matching_with_wrong_mrn_or_namespace_fails():
    patient = Patient(
        patient_id="pat-1001",
        mrn="MRN-884920",
        identifier_namespace="https://hospital.sims.org/patients",
    )

    with pytest.raises(PatientMismatchError, match="Patient identifier mismatch"):
        patient.match_with(
            candidate_mrn="WRONG-MRN",
            candidate_namespace="https://hospital.sims.org/patients",
        )

    with pytest.raises(PatientMismatchError, match="Patient identifier mismatch"):
        patient.match_with(
            candidate_mrn="MRN-884920",
            candidate_namespace="https://other-hospital.org",
        )


def test_matching_with_contradicting_dob_fails():
    patient = Patient(
        patient_id="pat-1001",
        mrn="MRN-884920",
        identifier_namespace="https://hospital.sims.org/patients",
        birth_date="1980-05-15",
    )

    with pytest.raises(PatientMismatchError, match="Demographic contradiction"):
        patient.match_with(
            candidate_mrn="MRN-884920",
            candidate_namespace="https://hospital.sims.org/patients",
            candidate_dob="1999-12-31",
        )


def test_patient_to_fhir_mapping():
    patient = Patient(
        patient_id="pat-99",
        mrn="MRN-9999",
        identifier_namespace="urn:oid:1.2.840.114350",
        family_name="Williams",
        given_name="Robert",
        birth_date="1965-08-20",
        gender="male",
    )
    fhir_res = patient.to_fhir()

    assert fhir_res["resourceType"] == "Patient"
    assert fhir_res["id"] == "pat-99"
    assert len(fhir_res["identifier"]) == 1
    assert fhir_res["identifier"][0]["system"] == "urn:oid:1.2.840.114350"
    assert fhir_res["identifier"][0]["value"] == "MRN-9999"
    assert fhir_res["name"][0]["family"] == "Williams"
    assert fhir_res["name"][0]["given"] == ["Robert"]
    assert fhir_res["birthDate"] == "1965-08-20"
    assert fhir_res["gender"] == "male"


def test_patient_from_fhir_mapping():
    fhir_data = {
        "resourceType": "Patient",
        "id": "fhir-patient-001",
        "identifier": [
            {
                "system": "http://sims-hospital.org/mrn",
                "value": "SIMS-MRN-456",
                "type": {
                    "coding": [{"code": "MR"}]
                }
            }
        ],
        "name": [{"family": "Curie", "given": ["Marie"]}],
        "birthDate": "1867-11-07",
        "gender": "female",
    }

    patient = Patient.from_fhir(fhir_data)
    assert patient.patient_id == "fhir-patient-001"
    assert patient.mrn == "SIMS-MRN-456"
    assert patient.identifier_namespace == "http://sims-hospital.org/mrn"
    assert patient.family_name == "Curie"
    assert patient.given_name == "Marie"
    assert patient.birth_date == "1867-11-07"
    assert patient.gender == "female"
    assert patient.reconciliation_status == ReconciliationStatus.RECONCILED


def test_patient_from_fhir_without_authoritative_identifier_fails():
    """Validates RULE-01: FHIR Patient without namespaced MRN must be rejected."""
    fhir_data_invalid = {
        "resourceType": "Patient",
        "id": "no-id-patient",
        "name": [{"family": "Anonymous"}],
    }

    with pytest.raises(PatientMismatchError, match="RULE-01 Violation"):
        Patient.from_fhir(fhir_data_invalid)
