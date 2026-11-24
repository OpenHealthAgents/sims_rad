"""
Contract Test Suite: External System Adapters (TC-039 to TC-048).
Verifies:
- TC-039: PACS QIDO-RS metadata query contract.
- TC-040: PACS WADO-RS viewer URL generation contract.
- TC-041: DICOM header parsing without pixel data extraction invariant.
- TC-042: BackBone HMS order ingestion payload contract.
- TC-043: BackBone HMS missing accession number non-retriable error.
- TC-044: BackBone HMS patient RULE-01 authoritative reconciliation.
- TC-045: BackBone HMS out-of-order and duplicate event resilience.
- TC-046: CharmHealth EHR FHIR R4 DiagnosticReport resource mapping.
- TC-047: CharmHealth EHR runtime capability matrix enforcement.
- TC-048: CharmHealth EHR vendor outage graceful fallback to Transactional Outbox.
"""
from datetime import datetime, timezone
import pytest
from unittest.mock import patch
import httpx

from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import Modality, RadiologyStudy
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import PatientMismatchError
from core.infrastructure.adapters.backbone_adapter import BackBoneHMSAdapter
from core.infrastructure.adapters.charmhealth_adapter import (
    CapabilityMatrix,
    CharmHealthEHRAdapter,
)
from core.infrastructure.adapters.exceptions import (
    BackBoneHMSConnectionError,
    MissingAccessionNumberError,
    VendorCapabilityDisabledError,
)
from core.infrastructure.adapters.mock_harness import (
    MockVendorTransport,
    SyntheticDICOMBuilder,
)
from core.infrastructure.adapters.pacs_adapter import FORBIDDEN_PIXEL_TAGS, PACSAdapter
from core.infrastructure.db.session import AsyncSessionLocal


# =============================================================================
# TC-039 & TC-040: PACS QIDO-RS & WADO-RS Contracts
# =============================================================================
@pytest.mark.asyncio
async def test_tc_039_pacs_qido_query_contract():
    """TC-039: PACS QIDO-RS query metadata returns structured study summaries via mock transport."""
    transport = MockVendorTransport()
    adapter = PACSAdapter(base_url="http://mock-pacs/dicom-web")

    with patch.object(httpx.AsyncClient, "get", new=lambda self, url, **kwargs: transport.handle_async_request(
        httpx.Request("GET", url, params=kwargs.get("params"), headers=kwargs.get("headers"))
    )):
        results = await adapter.qido_search_studies(patient_id="PAT-4200", modality="CT")
        assert len(results) >= 1
        assert "0020000D" in results[0]


def test_tc_040_pacs_wado_viewer_link_contract():
    """TC-040: PACS WADO-RS viewer link generates conformant DICOMweb retrieve URL."""
    adapter = PACSAdapter(base_url="http://mock-pacs/dicom-web", viewer_base_url="http://mock-viewer")
    viewer_url = adapter.wado_get_viewer_url(
        study_instance_uid="1.2.840.113619.2.55.3.4200",
        series_instance_uid="1.2.840.113619.2.55.3.series4200",
    )
    assert "StudyInstanceUIDs=1.2.840.113619.2.55.3.4200" in viewer_url
    assert "SeriesInstanceUIDs=1.2.840.113619.2.55.3.series4200" in viewer_url


# =============================================================================
# TC-041: DICOM Header Parsing Without Pixel Data Extraction
# =============================================================================
def test_tc_041_pacs_dicom_metadata_excludes_pixel_data():
    """TC-041: PACS adapter extracts DICOM metadata while strictly stripping pixel data tags."""
    dicom_bytes = SyntheticDICOMBuilder.create_dicom_bytes(
        modality="CT",
        patient_id="PAT-4201",
        patient_name="Skywalker^Luke",
        patient_birth_date="19800515",
        patient_sex="M",
        accession_number="ACC-CT-4201",
        study_description="CT Head Routine",
        include_pixel_data=True,
    )
    metadata = PACSAdapter.parse_dicom_bytes(dicom_bytes, stop_before_pixels=True)
    assert metadata.modality == "CT"
    assert metadata.patient_id == "PAT-4201"
    assert metadata.accession_number == "ACC-CT-4201"

    # Strictly verify NO forbidden pixel data tags exist in metadata raw JSON
    assert "PixelData" not in metadata.raw_metadata_json
    assert "Pixel Data" not in str(metadata.raw_metadata_json)
    for forbidden_tag in FORBIDDEN_PIXEL_TAGS:
        assert forbidden_tag not in metadata.raw_metadata_json


# =============================================================================
# TC-042 to TC-045: BackBone HMS Adapter Contracts
# =============================================================================
def test_tc_042_backbone_hms_order_ingestion_contract():
    """TC-042: Ingest clinical order from BackBone HMS and construct domain entities."""
    adapter = BackBoneHMSAdapter()
    order_payload = {
        "accession_number": "ACC-ORD-42",
        "patient": {
            "id": "PAT-42",
            "mrn": "MRN-42",
            "namespace": "urn:oid:sims.hospital.patients",
            "family_name": "Kenobi",
            "given_name": "Obi-Wan",
            "birth_date": "1960-04-02",
            "gender": "male",
        },
        "modality": "MRI",
        "priority": "STAT",
        "exam_description": "MRI Brain with Contrast",
    }
    study, work_item, patient = adapter.ingest_order(order_payload)
    assert study.accession_number == "ACC-ORD-42"
    assert study.modality == Modality.MRI
    assert work_item.priority == Priority.STAT
    assert patient.mrn == "MRN-42"
    assert patient.reconciliation_status == ReconciliationStatus.RECONCILED


def test_tc_043_backbone_hms_missing_accession_non_retriable_error():
    """TC-043: Order ingestion missing accession number raises MissingAccessionNumberError."""
    adapter = BackBoneHMSAdapter()
    with pytest.raises(MissingAccessionNumberError, match="Accession Number is required"):
        adapter.ingest_order({
            "patient": {"mrn": "MRN-NO-ACC"},
            "modality": "CT",
        })


def test_tc_044_backbone_hms_rule_01_reconciliation():
    """TC-044: Order reconciliation enforces RULE-01 namespace + MRN matching."""
    adapter = BackBoneHMSAdapter()
    hms_pat = Patient(
        patient_id="PAT-1",
        mrn="MRN-AUTH-001",
        identifier_namespace="urn:oid:sims.mrn",
        family_name="Organa",
        given_name="Leia",
        reconciliation_status=ReconciliationStatus.RECONCILED,
    )
    study = RadiologyStudy(
        study_id="STU-01",
        study_instance_uid="1.2.3.4.5",
        accession_number="ACC-RECON-01",
        modality=Modality.CT,
    )
    # Ambiguous candidate with different MRN
    pacs_pat_ambiguous = Patient(
        patient_id="PAT-2",
        mrn="MRN-CONFLICT-999",
        identifier_namespace="urn:oid:sims.mrn",
        family_name="Organa",
        given_name="Leia",
    )
    recon_res = adapter.reconcile_order(
        accession_number="ACC-RECON-01",
        hms_patient=hms_pat,
        pacs_study=study,
        pacs_patient=pacs_pat_ambiguous,
    )
    assert recon_res.is_reconciled is False
    assert recon_res.status == ReconciliationStatus.RECONCILIATION_REQUIRED
    assert len(recon_res.discrepancy_reasons) >= 1


def test_tc_045_backbone_hms_out_of_order_and_duplicate_resilience():
    """TC-045: Out-of-order and duplicate event handling idempotency."""
    adapter = BackBoneHMSAdapter()
    event_id = "EVT-ORD-101"
    timestamp = datetime.now(timezone.utc)

    # First delivery -> APPLIED
    res1 = adapter.handle_out_of_order_event(
        event_id=event_id,
        accession_number="ACC-101",
        event_type="ORDER_UPDATED",
        event_timestamp=timestamp,
        payload={},
    )
    assert res1["status"] == "APPLIED"

    # Duplicate delivery -> SKIPPED_DUPLICATE
    res2 = adapter.handle_out_of_order_event(
        event_id=event_id,
        accession_number="ACC-101",
        event_type="ORDER_UPDATED",
        event_timestamp=timestamp,
        payload={},
    )
    assert res2["status"] == "SKIPPED_DUPLICATE"


# =============================================================================
# TC-046 to TC-048: CharmHealth EHR Adapter Contracts
# =============================================================================
def test_tc_046_charmhealth_fhir_r4_diagnostic_report_mapping():
    """TC-046: Map domain Report, Patient, and Study to FHIR R4 DiagnosticReport resource."""
    adapter = CharmHealthEHRAdapter()
    patient = Patient(
        patient_id="PAT-FHIR-01",
        mrn="MRN-FHIR-01",
        identifier_namespace="urn:oid:sims.mrn",
        family_name="Windu",
        given_name="Mace",
        birth_date="1970-01-01",
    )
    study = RadiologyStudy(
        study_id="STU-FHIR-01",
        study_instance_uid="1.2.840.113619.2.55.3.8888",
        accession_number="ACC-FHIR-01",
        modality=Modality.MRI,
        description="MRI Brain",
    )
    ver = ReportVersion(
        version_number=1,
        structured_findings={"finding": "Normal"},
        impression="No intracranial abnormality.",
        author_id="RAD-DOC-88",
        signature_hash="sha256:mock_hash",
        signed_at=datetime.now(timezone.utc),
    )
    report = Report(
        report_id="REP-FHIR-01",
        work_item_id="WI-FHIR-01",
        status=ReportStatus.SIGNED,
        current_version_id="REP-FHIR-01-v1",
        versions={1: ver},
    )
    fhir_doc = adapter.map_to_fhir_diagnostic_report(report, patient, study, ver)
    assert fhir_doc["resourceType"] == "DiagnosticReport"
    assert fhir_doc["status"] == "final"
    assert fhir_doc["id"] == "REP-FHIR-01"
    assert fhir_doc["conclusion"] == "No intracranial abnormality."


@pytest.mark.asyncio
async def test_tc_047_charmhealth_runtime_capability_matrix():
    """TC-047: Runtime capability matrix checks raise VendorCapabilityDisabledError when disabled."""
    caps = CapabilityMatrix(
        patient_lookup=True,
        encounter_lookup=False,
        prior_report_read=False,
        final_report_write=True,
    )
    adapter = CharmHealthEHRAdapter(capabilities=caps)

    with pytest.raises(VendorCapabilityDisabledError) as exc_info:
        await adapter.encounter_lookup("ENC-99")
    assert exc_info.value.capability == "encounter_lookup"


@pytest.mark.asyncio
async def test_tc_048_charmhealth_outage_fallback_to_outbox():
    """
    TC-048: When CharmHealth server suffers an outage (503), report transmission
    gracefully falls back to Transactional Outbox without failing local clinical report state.
    """
    transport = MockVendorTransport()
    transport.simulate_outage = True
    transport.outage_status_code = 503

    adapter = CharmHealthEHRAdapter(
        base_url="http://mock-ehr/fhir/r4",
        capabilities=CapabilityMatrix(final_report_write=True),
    )
    patient = Patient(patient_id="PAT-OUT-48", mrn="MRN-OUT-48", identifier_namespace="urn:oid:mrn")
    study = RadiologyStudy(study_id="STU-OUT-48", study_instance_uid="1.2.3.48", accession_number="ACC-48", modality=Modality.CT)
    ver = ReportVersion(version_number=1, structured_findings={}, impression="Normal CT.", author_id="RAD-1")
    report = Report(report_id="REP-OUT-48", work_item_id="WI-48", status=ReportStatus.SIGNED, versions={1: ver})

    with patch.object(httpx.AsyncClient, "post", new=lambda self, url, **kwargs: transport.handle_async_request(
        httpx.Request("POST", url, json=kwargs.get("json"))
    )):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                delivery = await adapter.transmit_final_report(
                    report=report,
                    patient=patient,
                    study=study,
                    version=ver,
                    db_session=session,
                )
        assert delivery.status == "QUEUED_OUTBOX"
        assert delivery.fallback_to_outbox is True
        assert report.status == ReportStatus.SIGNED  # Local state uncorrupted
