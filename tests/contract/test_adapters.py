"""
Contract Tests: External System Adapters (PACS / DICOMweb, BackBone HMS, CharmHealth EHR).
Verifies:
- DICOM header metadata parsing via pydicom and strict pixel data exclusion invariants.
- QIDO-RS / WADO-RS interfaces and viewer URL generation.
- BackBone HMS order ingestion, missing accession validation, RULE-01 reconciliation, and out-of-order event resilience.
- CharmHealth EHR FHIR R4 DiagnosticReport mapping and runtime capability matrix.
- Safe fallback to Transactional Outbox on vendor outage or disabled capability without corrupting local study/report state.
"""
from datetime import datetime, timezone
import os
import pytest
import httpx
from unittest.mock import patch

from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import Modality, RadiologyStudy
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import InvalidDICOMMetadataError
from core.infrastructure.adapters.backbone_adapter import BackBoneHMSAdapter
from core.infrastructure.adapters.charmhealth_adapter import (
    CapabilityMatrix,
    CharmHealthEHRAdapter,
)
from core.infrastructure.adapters.exceptions import (
    BackBoneHMSConnectionError,
    CharmHealthConnectionError,
    MissingAccessionNumberError,
    PACSConnectionError,
    VendorCapabilityDisabledError,
)
from core.infrastructure.adapters.mock_harness import (
    MockVendorTransport,
    SyntheticDICOMBuilder,
)
from core.infrastructure.adapters.pacs_adapter import FORBIDDEN_PIXEL_TAGS, PACSAdapter
from core.infrastructure.db.session import AsyncSessionLocal
from core.infrastructure.persistence.models import OutboxEventModel


# =============================================================================
# 1. PACS / DICOM Adapter Contract Tests
# =============================================================================

def test_pacs_adapter_parses_dicom_metadata_and_excludes_pixel_data():
    """Verify that pydicom extracts DICOM header metadata while strictly stripping pixel data."""
    # Build synthetic DICOM with 64x64 pixel data
    dicom_bytes = SyntheticDICOMBuilder.create_dicom_bytes(
        modality="CT",
        patient_id="PAT-4200",
        patient_name="Skywalker^Luke",
        patient_birth_date="19800515",
        patient_sex="M",
        accession_number="ACC-CT-4200",
        study_description="CT Head Routine",
        include_pixel_data=True,
    )

    # Parse metadata using PACSAdapter
    meta = PACSAdapter.parse_dicom_bytes(dicom_bytes, stop_before_pixels=True)

    # Verify extracted header attributes
    assert meta.modality == "CT"
    assert meta.patient_id == "PAT-4200"
    assert "Skywalker" in meta.patient_name
    assert meta.patient_birth_date == "19800515"
    assert meta.patient_sex == "M"
    assert meta.accession_number == "ACC-CT-4200"
    assert meta.study_description == "CT Head Routine"
    assert meta.study_instance_uid is not None

    # INVARIANT CHECK: Pixel data must NEVER be present in metadata DTO or json
    assert "PixelData" not in meta.raw_metadata_json
    assert "Pixel Data" not in str(meta.raw_metadata_json)
    for forbidden in FORBIDDEN_PIXEL_TAGS:
        assert forbidden not in meta.raw_metadata_json

    # Test conversion to domain entities
    adapter = PACSAdapter()
    study, patient, series = adapter.to_domain_entities(meta)
    assert study.modality == Modality.CT
    assert study.accession_number == "ACC-CT-4200"
    assert patient.patient_id == "PAT-4200"
    assert patient.gender == "m"
    assert series.modality == Modality.CT

    # Verify domain entities contain zero pixel buffer attributes
    assert not hasattr(study, "pixel_data")
    assert not hasattr(study, "PixelData")
    assert not hasattr(patient, "pixel_data")


def test_pacs_adapter_file_parsing_and_error_handling(tmp_path):
    """Verify file-based DICOM reading and malformed stream handling."""
    file_path = SyntheticDICOMBuilder.create_dicom_file(
        directory=str(tmp_path),
        modality="MRI",
        accession_number="ACC-MR-900",
    )
    assert os.path.exists(file_path)

    meta = PACSAdapter.parse_dicom_file(file_path)
    assert meta.modality == "MRI"
    assert meta.accession_number == "ACC-MR-900"

    # Malformed DICOM bytes must raise InvalidDICOMMetadataError
    with pytest.raises(InvalidDICOMMetadataError):
        PACSAdapter.parse_dicom_bytes(b"CORRUPTED_NON_DICOM_STREAM")


@pytest.mark.asyncio
async def test_pacs_adapter_qido_wado_and_viewer_links():
    """Verify QIDO-RS search, WADO-RS metadata, and zero-footprint web viewer link generation."""
    transport = MockVendorTransport()
    adapter = PACSAdapter(base_url="http://mock-pacs/dicom-web", viewer_base_url="http://mock-viewer")

    with patch.object(httpx.AsyncClient, "get", new=lambda self, url, **kwargs: transport.handle_async_request(
        httpx.Request("GET", url, params=kwargs.get("params"), headers=kwargs.get("headers"))
    )):
        # 1. QIDO-RS Query
        studies = await adapter.qido_search_studies(patient_id="PAT-MOCK-001", modality="CT")
        assert len(studies) == 1
        assert "0020000D" in studies[0]

        # 2. WADO-RS Retrieve Metadata
        meta = await adapter.wado_retrieve_study_metadata(study_instance_uid="1.2.840.113619.2.55.3.mock")
        assert len(meta) >= 1

    # 3. Viewer Link (OHIF format)
    viewer_url = adapter.wado_get_viewer_url("1.2.840.113619.2.55.3.mock", "1.2.840.113619.2.55.3.series1")
    assert "StudyInstanceUIDs=1.2.840.113619.2.55.3.mock" in viewer_url
    assert "SeriesInstanceUIDs=1.2.840.113619.2.55.3.series1" in viewer_url
    assert "wadoURL=http://mock-pacs/dicom-web" in viewer_url


@pytest.mark.asyncio
async def test_pacs_adapter_vendor_outage_raises_retriable_error():
    """Verify that PACS 503 outage or timeout fails gracefully with retriable PACSConnectionError."""
    transport = MockVendorTransport()
    transport.simulate_outage = True
    transport.outage_status_code = 503
    adapter = PACSAdapter(base_url="http://mock-pacs/dicom-web")

    with patch.object(httpx.AsyncClient, "get", new=lambda self, url, **kwargs: transport.handle_async_request(
        httpx.Request("GET", url, params=kwargs.get("params"), headers=kwargs.get("headers"))
    )):
        with pytest.raises(PACSConnectionError) as exc_info:
            await adapter.qido_search_studies(accession_number="ACC-OUTAGE")
        assert exc_info.value.vendor == "PACS"
        assert exc_info.value.status_code == 503


# =============================================================================
# 2. BackBone HMS Adapter Contract Tests
# =============================================================================

def test_backbone_hms_order_ingestion_success():
    """Verify proper order parsing into domain entities."""
    adapter = BackBoneHMSAdapter()
    payload = {
        "accession_number": "ACC-ORD-101",
        "modality": "CT",
        "priority": "STAT",
        "exam_description": "CT Chest Angiogram",
        "patient": {
            "mrn": "MRN-101",
            "namespace": "urn:oid:sims:hospital:mrn",
            "first_name": "Leia",
            "last_name": "Organa",
            "dob": "1980-05-15",
            "gender": "female",
        },
    }

    study, work_item, patient = adapter.ingest_order(payload)
    assert study.accession_number == "ACC-ORD-101"
    assert study.modality == Modality.CT
    assert work_item.priority == Priority.STAT
    assert work_item.state == WorkItemState.READY
    assert patient.mrn == "MRN-101"
    assert patient.reconciliation_status == ReconciliationStatus.RECONCILED


def test_backbone_hms_missing_accession_raises_non_retriable_error():
    """Verify that missing accession raises NonRetriable MissingAccessionNumberError."""
    adapter = BackBoneHMSAdapter()
    payload = {
        "modality": "XRAY",
        "patient": {"mrn": "MRN-999"},
        # accession_number intentionally omitted
    }

    with pytest.raises(MissingAccessionNumberError):
        adapter.ingest_order(payload)


def test_backbone_hms_order_reconciliation_and_rule_01():
    """Verify order reconciliation enforcing RULE-01 authoritative patient matching."""
    adapter = BackBoneHMSAdapter()

    hms_patient = Patient(
        patient_id="PAT-H1",
        mrn="MRN-H1",
        identifier_namespace="urn:oid:sims:mrn",
        reconciliation_status=ReconciliationStatus.RECONCILED,
        family_name="Kenobi",
        birth_date="1960-01-01",
    )
    pacs_study = RadiologyStudy(
        study_id="STU-001",
        study_instance_uid="1.2.3.4.5",
        accession_number="ACC-100",
        modality=Modality.MRI,
    )

    # 1. Matching PACS patient with same authoritative MRN and namespace
    pacs_patient_matched = Patient(
        patient_id="PAT-P1",
        mrn="MRN-H1",
        identifier_namespace="urn:oid:sims:mrn",
        reconciliation_status=ReconciliationStatus.RECONCILED,
        family_name="Kenobi",
        birth_date="1960-01-01",
    )
    res_success = adapter.reconcile_order("ACC-100", hms_patient, pacs_study, pacs_patient_matched)
    assert res_success.is_reconciled is True
    assert res_success.status == ReconciliationStatus.RECONCILED

    # 2. Contradicting MRN (RULE-01 violation: name/DOB match is not sufficient!)
    pacs_patient_mismatched = Patient(
        patient_id="PAT-DIFF",
        mrn="MRN-DIFFERENT",
        identifier_namespace="urn:oid:sims:mrn",
        family_name="Kenobi",
        birth_date="1960-01-01",
    )
    res_fail = adapter.reconcile_order("ACC-100", hms_patient, pacs_study, pacs_patient_mismatched)
    assert res_fail.is_reconciled is False
    assert res_fail.status == ReconciliationStatus.RECONCILED.RECONCILIATION_REQUIRED
    assert len(res_fail.discrepancy_reasons) >= 1


def test_backbone_hms_out_of_order_events_handling():
    """Verify that out-of-order events do not corrupt internal study state."""
    adapter = BackBoneHMSAdapter()
    now = datetime.now(timezone.utc)

    # Create finalized work item
    wi = WorkItem(
        work_item_id="WI-FINAL-01",
        study_id="STU-01",
        state=WorkItemState.FINALIZED,
    )

    # Late cancellation arrives after study finalized
    res = adapter.handle_out_of_order_event(
        event_id="EVT-LATE-CANCEL-1",
        accession_number="ACC-01",
        event_type="ORDER_CANCELLED",
        event_timestamp=now,
        payload={"reason": "Patient discharged"},
        current_work_item=wi,
    )
    assert res["status"] == "BUFFERED_POST_FINALIZATION"
    assert wi.state == WorkItemState.FINALIZED  # Uncorrupted!

    # Duplicate event test
    res_dup = adapter.handle_out_of_order_event(
        event_id="EVT-LATE-CANCEL-1",
        accession_number="ACC-01",
        event_type="ORDER_CANCELLED",
        event_timestamp=now,
        payload={},
        current_work_item=wi,
    )
    assert res_dup["status"] == "SKIPPED_DUPLICATE"


@pytest.mark.asyncio
async def test_backbone_hms_vendor_outage_raises_retriable_error():
    """Verify that BackBone HMS 503 outage or timeout raises BackBoneHMSConnectionError."""
    transport = MockVendorTransport()
    transport.simulate_outage = True
    adapter = BackBoneHMSAdapter(base_url="http://mock-hms/api")

    with patch.object(httpx.AsyncClient, "get", new=lambda self, url, **kwargs: transport.handle_async_request(
        httpx.Request("GET", url)
    )):
        with pytest.raises(BackBoneHMSConnectionError) as exc_info:
            await adapter.fetch_order_details("ACC-OUTAGE")
        assert exc_info.value.vendor == "BackBone_HMS"
        assert exc_info.value.status_code == 503


# =============================================================================
# 3. CharmHealth EHR Adapter Contract Tests
# =============================================================================

def test_charmhealth_adapter_fhir_mapping():
    """Verify mapping of Report, Patient, Study to FHIR R4 DiagnosticReport resource."""
    adapter = CharmHealthEHRAdapter()
    patient = Patient(
        patient_id="PAT-CH-01",
        mrn="MRN-CH-01",
        identifier_namespace="urn:oid:charmhealth:mrn",
        family_name="Solo",
        given_name="Han",
        birth_date="1975-07-13",
    )
    study = RadiologyStudy(
        study_id="STU-CH-01",
        study_instance_uid="1.2.840.113619.2.55.3.1111",
        accession_number="ACC-CH-01",
        modality=Modality.CT,
        description="CT Head Diagnostic Exam",
    )
    ver = ReportVersion(
        version_number=1,
        structured_findings={"hemorrhage": False},
        impression="Normal non-contrast head CT.",
        author_id="RAD-DOC-42",
        signature_hash="sha256_mock_hash",
        signed_at=datetime.now(timezone.utc),
    )
    report = Report(
        report_id="REP-CH-01",
        work_item_id="WI-CH-01",
        status=ReportStatus.SIGNED,
        current_version_id="REP-CH-01-v1",
        versions={1: ver},
    )

    fhir_doc = adapter.map_to_fhir_diagnostic_report(report, patient, study, ver)
    assert fhir_doc["resourceType"] == "DiagnosticReport"
    assert fhir_doc["id"] == "REP-CH-01"
    assert fhir_doc["status"] == "final"
    assert fhir_doc["category"][0]["coding"][0]["code"] == "RAD"
    assert fhir_doc["code"]["coding"][0]["code"] == "24627-2"  # CT Head LOINC
    assert fhir_doc["subject"]["identifier"]["value"] == "MRN-CH-01"
    assert fhir_doc["conclusion"] == "Normal non-contrast head CT."
    assert fhir_doc["performer"][0]["display"] == "RAD-DOC-42"


@pytest.mark.asyncio
async def test_charmhealth_capability_matrix_enforcement():
    """Verify runtime capability matrix enforcement and disabled capability exceptions."""
    caps = CapabilityMatrix(
        patient_lookup=True,
        encounter_lookup=False,  # Disabled
        prior_report_read=False,  # Disabled
        final_report_write=True,
    )
    adapter = CharmHealthEHRAdapter(capabilities=caps)

    # Encounter lookup is disabled -> raises VendorCapabilityDisabledError
    with pytest.raises(VendorCapabilityDisabledError) as exc_info:
        await adapter.encounter_lookup("ENC-01")
    assert exc_info.value.capability == "encounter_lookup"

    # Prior report read is disabled -> raises VendorCapabilityDisabledError
    with pytest.raises(VendorCapabilityDisabledError) as exc_info:
        await adapter.prior_report_read("PAT-01")
    assert exc_info.value.capability == "prior_report_read"


@pytest.mark.asyncio
async def test_charmhealth_safe_fallback_when_final_report_write_disabled():
    """
    CRITICAL INVARIANT TEST:
    When 'final_report_write' is False in capability matrix, transmission must safely
    fallback to Transactional Outbox without failing the local clinical sign-off state.
    """
    caps = CapabilityMatrix(final_report_write=False)
    adapter = CharmHealthEHRAdapter(capabilities=caps)

    patient = Patient(
        patient_id="PAT-FB-01",
        mrn="MRN-FB-01",
        identifier_namespace="urn:oid:mrn",
    )
    study = RadiologyStudy(
        study_id="STU-FB-01",
        study_instance_uid="1.2.3.4",
        accession_number="ACC-FB-01",
        modality=Modality.XRAY,
    )
    ver = ReportVersion(
        version_number=1,
        structured_findings={},
        impression="Normal chest radiograph.",
        author_id="RAD-DOC-1",
    )
    report = Report(
        report_id="REP-FB-01",
        work_item_id="WI-FB-01",
        status=ReportStatus.SIGNED,  # Signed locally
        versions={1: ver},
    )

    async with AsyncSessionLocal() as session:
        async with session.begin():
            delivery_result = await adapter.transmit_final_report(
                report=report,
                patient=patient,
                study=study,
                version=ver,
                db_session=session,
            )

        # Invariant checks:
        assert delivery_result.status == "QUEUED_OUTBOX"
        assert delivery_result.delivered is False
        assert delivery_result.fallback_to_outbox is True
        assert delivery_result.outbox_event_id is not None
        # Local report remains signed
        assert report.status == ReportStatus.SIGNED


@pytest.mark.asyncio
async def test_charmhealth_safe_fallback_on_vendor_outage():
    """
    CRITICAL INVARIANT TEST:
    When CharmHealth server suffers an outage (500/503/timeout), report transmission
    must fallback gracefully to a retriable outbox task WITHOUT failing or rolling back
    the local clinical sign-off.
    """
    transport = MockVendorTransport()
    transport.simulate_outage = True
    transport.outage_status_code = 503

    adapter = CharmHealthEHRAdapter(
        base_url="http://mock-ehr/fhir/r4",
        capabilities=CapabilityMatrix(final_report_write=True),
    )

    patient = Patient(
        patient_id="PAT-OUT-01",
        mrn="MRN-OUT-01",
        identifier_namespace="urn:oid:mrn",
    )
    study = RadiologyStudy(
        study_id="STU-OUT-01",
        study_instance_uid="1.2.3.4.5",
        accession_number="ACC-OUT-01",
        modality=Modality.MRI,
    )
    ver = ReportVersion(
        version_number=1,
        structured_findings={},
        impression="Mild degenerative changes.",
        author_id="RAD-DOC-2",
    )
    report = Report(
        report_id="REP-OUT-01",
        work_item_id="WI-OUT-01",
        status=ReportStatus.SIGNED,
        versions={1: ver},
    )

    with patch.object(httpx.AsyncClient, "post", new=lambda self, url, **kwargs: transport.handle_async_request(
        httpx.Request("POST", url, json=kwargs.get("json"))
    )):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                delivery_result = await adapter.transmit_final_report(
                    report=report,
                    patient=patient,
                    study=study,
                    version=ver,
                    db_session=session,
                )

        # Invariant checks:
        assert delivery_result.status == "QUEUED_OUTBOX"
        assert delivery_result.delivered is False
        assert delivery_result.fallback_to_outbox is True
        assert "Vendor outage" in delivery_result.reason
        # Local clinical state remains uncorrupted
        assert report.status == ReportStatus.SIGNED


@pytest.mark.asyncio
async def test_charmhealth_successful_report_delivery():
    """Verify successful transmission when CharmHealth is online and final_report_write is enabled."""
    transport = MockVendorTransport()
    transport.simulate_outage = False

    adapter = CharmHealthEHRAdapter(
        base_url="http://mock-ehr/fhir/r4",
        capabilities=CapabilityMatrix(final_report_write=True),
    )

    patient = Patient(
        patient_id="PAT-OK-01",
        mrn="MRN-OK-01",
        identifier_namespace="urn:oid:mrn",
    )
    study = RadiologyStudy(
        study_id="STU-OK-01",
        study_instance_uid="1.2.3.4.6",
        accession_number="ACC-OK-01",
        modality=Modality.CT,
    )
    ver = ReportVersion(
        version_number=1,
        structured_findings={},
        impression="Clear scan.",
        author_id="RAD-DOC-3",
    )
    report = Report(
        report_id="REP-OK-01",
        work_item_id="WI-OK-01",
        status=ReportStatus.RELEASED,
        versions={1: ver},
    )

    with patch.object(httpx.AsyncClient, "post", new=lambda self, url, **kwargs: transport.handle_async_request(
        httpx.Request("POST", url, json=kwargs.get("json"))
    )):
        delivery_result = await adapter.transmit_final_report(
            report=report,
            patient=patient,
            study=study,
            version=ver,
        )

        assert delivery_result.status == "DELIVERED"
        assert delivery_result.delivered is True
        assert delivery_result.fallback_to_outbox is False
        assert delivery_result.fhir_resource_id is not None
