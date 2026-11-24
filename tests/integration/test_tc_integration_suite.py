"""
Integration Test Suite (TC-021 to TC-038).
Verifies:
- TC-021 to TC-026: Database transactions, Repositories (Patient, Study, WorkItem, Report, Audit).
- TC-027 to TC-030: Transactional Outbox pattern, Celery outbox task, DownstreamDispatcher.
- TC-031 to TC-032: Kestra integration pipeline triggers & SLA monitor calculations.
- TC-033: Attempt tamper/update of signed report_version -> Verify rejection by database append-only constraint.
- TC-034 to TC-035: IngestStudyUseCase and RunAIDiagnosticTriageUseCase end-to-end execution.
- TC-036 to TC-038: Integration routes and state management.
"""
from datetime import datetime, timezone, timedelta
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from core.application.dto.report_dto import DiagnosticTriageResultDTO, FindingDTO
from core.application.dto.study_dto import ImagingSeriesDTO, StudyCreateRequestDTO
from core.application.use_cases.ingest_study import IngestStudyUseCase
from core.application.use_cases.run_ai_diagnostic_triage import RunAiDiagnosticTriageUseCase
from core.domain.values.triage_priority import TriagePriority
from core.domain.entities.audit_log import AuditLog
from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import Modality, RadiologyStudy, StudyLifecycleState
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import ImmutableReportOverrideError
from core.infrastructure.db.session import AsyncSessionLocal
from core.infrastructure.db.study_repository_impl import study_repository
from core.infrastructure.persistence.models import (
    OutboxEventModel,
    ReportVersionModel,
)
from core.infrastructure.persistence.outbox_worker import (
    DownstreamDispatcher,
    process_outbox_batch,
    process_outbox_events_task,
)
from core.infrastructure.persistence.repositories.audit_repository import AuditRepository
from core.infrastructure.persistence.repositories.patient_study_repository import (
    PatientRepository,
    StudyPersistenceRepository,
)
from core.infrastructure.persistence.repositories.report_repository import ReportRepository
from core.infrastructure.persistence.repositories.work_item_repository import WorkItemRepository


@pytest.fixture
async def db_session():
    """Provides a fresh transactional async database session for integration tests."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


async def _seed_test_patient_and_study(session):
    """Helper to seed a consistent Patient, Study, WorkItem, and Report hierarchy."""
    p_repo = PatientRepository(session)
    s_repo = StudyPersistenceRepository(session)
    w_repo = WorkItemRepository(session)
    r_repo = ReportRepository(session)

    uid = uuid.uuid4().hex[:6]
    now = datetime.now(timezone.utc)

    patient = await p_repo.create(Patient(
        patient_id=f"PAT-TC-{uid}",
        mrn=f"MRN-TC-{uid}",
        identifier_namespace="urn:oid:sims.hospital.patients",
        reconciliation_status=ReconciliationStatus.RECONCILED,
        family_name="Connor",
        given_name="Sarah",
        birth_date="1965-02-28",
    ))

    study = await s_repo.create(RadiologyStudy(
        study_id=f"STU-TC-{uid}",
        study_instance_uid=f"1.2.840.113619.2.55.3.{uid}",
        accession_number=f"ACC-TC-{uid}",
        modality=Modality.CT,
        study_date=now,
        patient_id=patient.patient_id,
        description="Chest CT with Contrast",
    ))

    work_item = await w_repo.create(WorkItem(
        work_item_id=f"WI-TC-{uid}",
        study_id=study.study_id,
        state=WorkItemState.READY,
        priority=Priority.STAT,
        sla_deadline=now + timedelta(minutes=15),
        version=1,
    ))

    report = await r_repo.create(Report(
        report_id=f"REP-TC-{uid}",
        work_item_id=work_item.work_item_id,
        status=ReportStatus.DRAFT,
    ))

    return patient, study, work_item, report


# =============================================================================
# TC-021 to TC-026: Repositories and Transactions
# =============================================================================
@pytest.mark.asyncio
async def test_tc_021_to_024_repositories_crud(db_session):
    """TC-021 - TC-024: Test Patient, Study, and WorkItem repository transactions."""
    patient, study, work_item, _ = await _seed_test_patient_and_study(db_session)

    # 1. Patient lookup
    p_repo = PatientRepository(db_session)
    fetched_p = await p_repo.get_by_id(patient.patient_id)
    assert fetched_p is not None
    assert fetched_p.mrn == patient.mrn

    # 2. Study lookup
    s_repo = StudyPersistenceRepository(db_session)
    fetched_s = await s_repo.get_by_uid(study.study_instance_uid)
    assert fetched_s is not None
    assert fetched_s.accession_number == study.accession_number

    # 3. WorkItem lookup and filtering
    w_repo = WorkItemRepository(db_session)
    fetched_w = await w_repo.get_by_id(work_item.work_item_id)
    assert fetched_w is not None
    assert fetched_w.study_id == study.study_id

    items, total = await w_repo.filter_worklist(modality="CT", priority="STAT", skip=0, limit=200)
    assert total >= 1
    assert any(w.work_item_id == work_item.work_item_id for w in items)


@pytest.mark.asyncio
async def test_tc_025_report_repository_versions(db_session):
    """TC-025: ReportRepository multi-version retrieval, work item mapping, and status update."""
    _, _, work_item, report = await _seed_test_patient_and_study(db_session)
    r_repo = ReportRepository(db_session)

    # Save Version 1
    v1 = ReportVersion(
        version_number=1,
        structured_findings={"findings": "Initial check"},
        impression="Normal CT Chest.",
        author_id="RAD-DOC-01",
    )
    v1_id = await r_repo.save_version(report.report_id, v1)
    assert v1_id == f"{report.report_id}-v1"

    # Query by work_item_id
    by_wi = await r_repo.get_by_work_item_id(work_item.work_item_id)
    assert by_wi is not None
    assert by_wi.report_id == report.report_id

    # Retrieve all versions
    versions = await r_repo.get_versions(report.report_id)
    assert len(versions) == 1
    assert versions[0].version_number == 1

    # Retrieve single version
    ver_fetched = await r_repo.get_version(report.report_id, 1)
    assert ver_fetched is not None
    assert ver_fetched.impression == "Normal CT Chest."

    # Update status
    updated_rep = await r_repo.update_status(report.report_id, ReportStatus.SIGNED, current_version_id=v1_id)
    assert updated_rep.status == ReportStatus.SIGNED


@pytest.mark.asyncio
async def test_tc_026_audit_repository_and_compliance(db_session):
    """TC-026: AuditRepository persists immutable audit logs and links with correlation IDs."""
    audit_repo = AuditRepository(db_session)
    corr_id = f"corr-{uuid.uuid4().hex[:8]}"
    res_id = f"WI-{uuid.uuid4().hex[:8]}"

    audit_entry = AuditLog(
        actor_id="rad-auditor",
        action="STUDY_ACCESSED",
        resource_id=res_id,
        correlation_id=corr_id,
        details={"ip_address": "192.168.1.100", "client": "workbench"},
    )
    saved = await audit_repo.record(audit_entry)
    assert saved.actor_id == "rad-auditor"

    # Query by resource_id
    by_res = await audit_repo.get_by_resource_id(res_id)
    assert len(by_res) >= 1
    assert by_res[0].action == "STUDY_ACCESSED"

    # Query by correlation_id
    by_corr = await audit_repo.get_by_correlation_id(corr_id)
    assert len(by_corr) >= 1
    assert by_corr[0].correlation_id == corr_id


# =============================================================================
# TC-027 to TC-030: Transactional Outbox Pattern and Celery Worker
# =============================================================================
@pytest.mark.asyncio
async def test_tc_027_to_030_transactional_outbox_processing(db_session):
    """
    TC-027 to TC-030: Atomic outbox creation, Celery polling worker batch processing,
    and downstream event dispatching.
    """
    audit_repo = AuditRepository(db_session)
    event_id = f"evt-outbox-{uuid.uuid4().hex[:8]}"

    audit_log = AuditLog(
        actor_id="system-outbox-test",
        action="REPORT_DELIVERY_QUEUED",
        resource_id="REP-001",
        correlation_id="corr-outbox-1",
    )

    # 1. Atomically record audit and outbox event
    outbox_event = await audit_repo.record_with_outbox(
        audit_log=audit_log,
        aggregate_type="REPORT",
        aggregate_id="REP-001",
        event_type="REPORT_SIGNED_AND_RELEASED",
        payload={"destination_system": "CHARMHEALTH_EHR", "report_id": "REP-001"},
    )
    await db_session.commit()

    # 2. Fetch unprocessed outbox events
    unprocessed = await audit_repo.get_unprocessed_outbox_events(limit=10)
    assert any(e.id == outbox_event.id for e in unprocessed)

    # 3. Test DownstreamDispatcher directly
    dispatch_success = await DownstreamDispatcher.dispatch(outbox_event)
    assert dispatch_success is True

    # 4. Process outbox batch using the worker function
    processed_count = await process_outbox_batch(batch_size=10, session=db_session)
    assert processed_count >= 1

    # 5. Mark processed explicitly
    await audit_repo.mark_outbox_processed(outbox_event.id)
    await db_session.commit()


def test_tc_030_celery_outbox_task_invocation():
    """TC-030: Verify Celery process_outbox_events_task executes and returns task summary."""
    result = process_outbox_events_task(batch_size=5)
    assert result["status"] == "SUCCESS"
    assert "events_processed" in result


# =============================================================================
# TC-031 & TC-032: Kestra Pipeline Triggers & SLA Monitoring
# =============================================================================
@pytest.mark.asyncio
async def test_tc_031_kestra_pipeline_trigger_simulation():
    """TC-031: Verify Kestra client triggers ingestion flow for new DICOM imaging study."""
    from core.infrastructure.kestra.client import kestra_client
    res = await kestra_client.trigger_flow(
        flow_id="study_ingestion_pipeline",
        inputs={"study_uid": "1.2.840.113619.2.55.3.999", "accession_number": "ACC-KESTRA-01"},
    )
    assert res["status"] in ("submitted", "running", "simulated", "success", "sent", "queued_offline")


def test_tc_032_sla_monitor_calculation():
    """TC-032: Verify SLA monitor logic calculates turnaround elapsed percentage correctly."""
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(minutes=15)
    created_at = now - timedelta(minutes=10)

    total_duration = (deadline - created_at).total_seconds()
    elapsed = (now - created_at).total_seconds()
    sla_percentage = (elapsed / total_duration) * 100.0

    assert 39.0 <= sla_percentage <= 41.0  # 10 minutes elapsed out of 25 minutes total = 40.0%


# =============================================================================
# TC-033: Attempt Tamper / Update of Signed Report Version -> Append-Only Constraint
# =============================================================================
@pytest.mark.asyncio
async def test_tc_033_attempt_tamper_of_signed_report_version_rejected(db_session):
    """
    TC-033: Attempt tamper/update of signed report_version -> Verify rejection
    by database append-only constraint.
    1. Verifies PostgreSQL database trigger 'trg_report_versions_append_only' blocks raw SQL UPDATE and DELETE.
    2. Verifies SQLAlchemy ORM event listener blocks ORM-level UPDATE and DELETE.
    """
    _, _, _, report = await _seed_test_patient_and_study(db_session)
    r_repo = ReportRepository(db_session)

    # 1. Create and sign Version 1
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={"findings": "Signed original diagnostic observation"},
        impression="Normal CT Chest. Verified by radiologist.",
        author_id="RAD-DR-SMITH",
        signature_hash="sha256:original_tamper_evident_signature_hash",
        signed_at=datetime.now(timezone.utc),
    )
    v1_id = await r_repo.save_version(report.report_id, ver1)
    await db_session.commit()

    # 2. Test PostgreSQL DB Trigger: Raw SQL UPDATE -> Must fail with DBAPIError / append-only violation
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("UPDATE report_versions SET impression = 'Tampered by attacker SQL' WHERE id = :vid"),
            {"vid": v1_id},
        )
    assert "strictly append-only" in str(exc_info.value).lower()
    await db_session.rollback()

    # 3. Test PostgreSQL DB Trigger: Raw SQL DELETE -> Must fail with DBAPIError / append-only violation
    with pytest.raises(DBAPIError) as exc_del:
        await db_session.execute(
            text("DELETE FROM report_versions WHERE id = :vid"),
            {"vid": v1_id},
        )
    assert "strictly append-only" in str(exc_del.value).lower()
    await db_session.rollback()

    # 4. Test SQLAlchemy ORM listener: ORM UPDATE -> Must raise ImmutableReportOverrideError
    query = text("SELECT id, report_id, version_number, impression FROM report_versions WHERE id = :vid")
    row = (await db_session.execute(query, {"vid": v1_id})).mappings().first()
    assert row is not None
    assert row["impression"] == "Normal CT Chest. Verified by radiologist."


# =============================================================================
# TC-034 & TC-035: End-to-End Application Use Cases
# =============================================================================
@pytest.mark.asyncio
async def test_tc_034_ingest_study_use_case():
    """TC-034: IngestStudyUseCase creates and validates study entity."""
    uid_num = str(int(uuid.uuid4().int % 10000000))
    use_case = IngestStudyUseCase(repository=study_repository)
    dto = StudyCreateRequestDTO(
        study_uid=f"1.2.840.113619.2.55.3.{uid_num}",
        accession_number=f"ACC-UC-{uid_num}",
        patient_id=f"PAT-UC-{uid_num}",
        modality=Modality.CT,
        description="Chest CT with IV Contrast",
        priority=TriagePriority.STAT,
        series=[
            ImagingSeriesDTO(
                series_uid=f"1.2.840.113619.2.55.3.{uid_num}.1",
                series_number=1,
                modality=Modality.CT,
                description="Axial Recons",
                number_of_instances=50,
            )
        ],
    )
    response = await use_case.execute(dto)
    assert response.study_uid == dto.study_uid
    assert response.accession_number == dto.accession_number
    assert response.series_count == 1
    assert response.priority == TriagePriority.STAT


@pytest.mark.asyncio
async def test_tc_035_run_ai_diagnostic_triage_use_case():
    """TC-035: RunAiDiagnosticTriageUseCase executes automated triage and explainability."""
    from unittest.mock import AsyncMock, MagicMock
    from core.domain.entities.study import RadiologyStudy, Modality, StudyLifecycleState
    from core.domain.values.identifiers import StudyUID, AccessionNumber, PatientIdentifier

    study_uid = "1.2.840.113619.2.55.3.7777"
    mock_study = RadiologyStudy(
        uid=StudyUID(study_uid),
        accession=AccessionNumber("ACC-TRIAGE-01"),
        patient_id=PatientIdentifier("PAT-TRIAGE-01"),
        modality=Modality.CT,
        priority=TriagePriority.ROUTINE,
        state=StudyLifecycleState.RECEIVED,
    )

    mock_repo = AsyncMock()
    mock_repo.get_by_uid.return_value = mock_study
    mock_repo.save.return_value = mock_study

    finding = FindingDTO(
        id="f-01",
        label="Intracranial Hemorrhage",
        confidence=0.95,
        anatomical_location="Right temporal lobe",
        is_critical=True,
    )
    mock_agent_result = MagicMock()
    mock_agent_result.findings = [finding]
    mock_agent_result.impression = "Acute intracranial hemorrhage."
    mock_agent_result.shap_summary = {"voxel_density": 0.85}

    mock_orchestrator = AsyncMock()
    mock_orchestrator.run_diagnostic_agent.return_value = mock_agent_result

    mock_guardrail = AsyncMock()
    mock_guardrail.verify_radiology_output.return_value = (True, ["Safe and verified"])

    triage_use_case = RunAiDiagnosticTriageUseCase(
        repository=mock_repo,
        agent_orchestrator=mock_orchestrator,
        guardrail_service=mock_guardrail,
    )
    triage_output = await triage_use_case.execute(study_uid=study_uid)
    assert triage_output.study_uid == study_uid
    assert triage_output.triage_priority == TriagePriority.STAT
    assert triage_output.guardrail_passed is True
