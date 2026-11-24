"""
Integration Tests: PostgreSQL Persistence, Alembic Migrations, Repositories,
Append-Only Immutability Invariants, and Transactional Outbox Pattern with Celery.
"""
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from core.domain.entities.audit_log import AuditLog
from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import Modality, RadiologyStudy
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import ImmutableReportOverrideError
from core.infrastructure.db.session import AsyncSessionLocal
from core.infrastructure.persistence.models import (
    ReportVersionModel,
    OutboxEventModel,
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
    """Provides a fresh transactional async database session for testing."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_patient_repository_create_and_query(db_session):
    repo = PatientRepository(db_session)
    pid = f"PAT-TEST-{uuid.uuid4().hex[:6]}"
    mrn = f"MRN-TEST-{uuid.uuid4().hex[:6]}"

    patient = Patient(
        patient_id=pid,
        mrn=mrn,
        identifier_namespace="urn:oid:sims:test:mrn",
        reconciliation_status=ReconciliationStatus.RECONCILED,
        given_name="Sarah",
        family_name="Connor",
        birth_date="1965-02-28",
        gender="female",
    )
    saved = await repo.create(patient)
    assert saved.patient_id == pid
    assert saved.mrn == mrn
    assert saved.reconciliation_status == ReconciliationStatus.RECONCILED

    fetched_by_id = await repo.get_by_id(pid)
    assert fetched_by_id is not None
    assert fetched_by_id.mrn == mrn
    assert fetched_by_id.given_name == "Sarah"

    fetched_by_mrn = await repo.get_by_mrn(mrn, namespace="urn:oid:sims:test:mrn")
    assert fetched_by_mrn is not None
    assert fetched_by_mrn.patient_id == pid


@pytest.mark.asyncio
async def test_study_and_work_item_repositories(db_session):
    p_repo = PatientRepository(db_session)
    s_repo = StudyPersistenceRepository(db_session)
    w_repo = WorkItemRepository(db_session)

    # 1. Setup Patient
    pid = f"PAT-{uuid.uuid4().hex[:6]}"
    mrn = f"MRN-{uuid.uuid4().hex[:6]}"
    await p_repo.create(Patient(
        patient_id=pid,
        mrn=mrn,
        identifier_namespace="urn:oid:sims:mrn",
        reconciliation_status=ReconciliationStatus.RECONCILED,
    ))

    # 2. Setup Study (CT)
    study_id = f"STU-CT-{uuid.uuid4().hex[:6]}"
    uid = f"1.2.840.113619.2.55.3.{uuid.uuid4().hex[:8]}"
    acc = f"ACC-{uuid.uuid4().hex[:6]}"
    study = RadiologyStudy(
        study_id=study_id,
        study_instance_uid=uid,
        accession_number=acc,
        modality=Modality.CT,
        study_date=datetime.now(timezone.utc),
        patient_id=pid,
        source_system="PACS-TEST",
    )
    saved_study = await s_repo.create(study)
    assert saved_study.study_id == study_id
    assert saved_study.modality == Modality.CT

    # Query study by instance UID
    queried_study = await s_repo.get_by_study_instance_uid(uid)
    assert queried_study is not None
    assert queried_study.study_id == study_id

    # 3. Create WorkItem
    wi_id = f"WI-{uuid.uuid4().hex[:6]}"
    work_item = WorkItem(
        work_item_id=wi_id,
        study_id=study_id,
        state=WorkItemState.RECEIVED,
        priority=Priority.STAT,
        assigned_radiologist_id=None,
        sla_deadline=datetime.now(timezone.utc) + timedelta(minutes=15),
        version=1,
    )
    saved_wi = await w_repo.create(work_item)
    assert saved_wi.work_item_id == wi_id
    assert saved_wi.state == WorkItemState.RECEIVED
    assert saved_wi.priority == Priority.STAT

    # 4. Update WorkItem (Assign and transition to in_progress)
    work_item.assign_to("RAD-DOC-TEST")
    work_item.state = WorkItemState.IN_PROGRESS
    work_item.version = 2
    updated_wi = await w_repo.update(work_item)
    assert updated_wi.assigned_radiologist_id == "RAD-DOC-TEST"
    assert updated_wi.state == WorkItemState.IN_PROGRESS
    assert updated_wi.version == 2

    # 5. Test Filter Worklist with Modality, Priority, Status
    items, count = await w_repo.filter_worklist(
        modality="CT",
        priority="STAT",
        status="in_progress",
        assigned_radiologist_id="RAD-DOC-TEST",
        limit=10,
    )
    assert count >= 1
    matched_ids = [item.work_item_id for item in items]
    assert wi_id in matched_ids


@pytest.mark.asyncio
async def test_report_repository_versioning_and_snapshots(db_session):
    p_repo = PatientRepository(db_session)
    s_repo = StudyPersistenceRepository(db_session)
    w_repo = WorkItemRepository(db_session)
    r_repo = ReportRepository(db_session)

    # Setup base entities
    pid = f"PAT-{uuid.uuid4().hex[:6]}"
    await p_repo.create(Patient(
        patient_id=pid,
        mrn=f"MRN-{uuid.uuid4().hex[:6]}",
        identifier_namespace="urn:oid:test",
        reconciliation_status=ReconciliationStatus.RECONCILED,
    ))
    study_id = f"STU-{uuid.uuid4().hex[:6]}"
    await s_repo.create(RadiologyStudy(
        study_id=study_id,
        study_instance_uid=f"1.2.3.4.{uuid.uuid4().hex[:6]}",
        accession_number=f"ACC-{uuid.uuid4().hex[:6]}",
        modality=Modality.MRI,
        patient_id=pid,
    ))
    wi_id = f"WI-{uuid.uuid4().hex[:6]}"
    await w_repo.create(WorkItem(
        work_item_id=wi_id,
        study_id=study_id,
        state=WorkItemState.DRAFT_READY,
    ))

    # 1. Create Report with Version 1
    report_id = f"REP-{uuid.uuid4().hex[:6]}"
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={"description": "Preliminary finding of lumbar disc bulge"},
        impression="L4-L5 disc protrusion without acute canal stenosis.",
        author_id="RAD-DOC-01",
    )
    report = Report(
        report_id=report_id,
        work_item_id=wi_id,
        status=ReportStatus.DRAFT,
        current_version_id=None,
        versions={1: ver1},
    )
    saved_report = await r_repo.create(report)
    assert saved_report.report_id == report_id
    assert saved_report.current_version_id == f"{report_id}-v1"

    # 2. Append Version 2 (Strictly Append-Only)
    ver2 = ReportVersion(
        version_number=2,
        structured_findings={"description": "Addendum: Corroborated with prior exam"},
        impression="Stable L4-L5 disc protrusion. Signed final.",
        author_id="RAD-DOC-02",
        signature_hash="mock_signature_hash_final",
        signed_at=datetime.now(timezone.utc),
    )
    ver2_id = await r_repo.save_version(report_id, ver2)
    assert ver2_id == f"{report_id}-v2"

    # 3. Retrieve Report and verify all versions present
    fetched_report = await r_repo.get_by_id(report_id)
    assert fetched_report is not None
    assert len(fetched_report.versions) == 2
    assert fetched_report.current_version_id == f"{report_id}-v2"
    assert fetched_report.versions[1].impression == "L4-L5 disc protrusion without acute canal stenosis."
    assert fetched_report.versions[2].impression == "Stable L4-L5 disc protrusion. Signed final."

    # 4. Attempt to overwrite Version 1 with same version number -> raises ImmutableReportOverrideError
    with pytest.raises(ImmutableReportOverrideError):
        await r_repo.save_version(report_id, ver1)


async def _seed_test_hierarchy(db_session):
    p_repo = PatientRepository(db_session)
    s_repo = StudyPersistenceRepository(db_session)
    w_repo = WorkItemRepository(db_session)
    r_repo = ReportRepository(db_session)

    uid = uuid.uuid4().hex[:6]
    patient = await p_repo.create(Patient(
        patient_id=f"PAT-IMM-{uid}",
        mrn=f"MRN-IMM-{uid}",
        identifier_namespace="urn:oid:test",
        reconciliation_status=ReconciliationStatus.RECONCILED,
    ))
    study = await s_repo.create(RadiologyStudy(
        study_id=f"STU-IMM-{uid}",
        study_instance_uid=f"1.2.840.10008.5.1.4.1.1.2.{uid}",
        accession_number=f"ACC-IMM-{uid}",
        modality=Modality.CT,
        patient_id=patient.patient_id,
    ))
    work_item = await w_repo.create(WorkItem(
        work_item_id=f"WI-IMM-{uid}",
        study_id=study.study_id,
        state=WorkItemState.DRAFT_READY,
    ))
    report = await r_repo.create(Report(
        report_id=f"REP-IMM-{uid}",
        work_item_id=work_item.work_item_id,
        status=ReportStatus.DRAFT,
    ))
    ver_model = ReportVersionModel(
        id=f"{report.report_id}-v1",
        report_id=report.report_id,
        version_number=1,
        structured_findings={"key": "original"},
        impression="Original clinical impression.",
        author_id="RAD-TEST",
    )
    db_session.add(ver_model)
    await db_session.flush()
    return patient, study, work_item, report, ver_model


@pytest.mark.asyncio
async def test_report_version_immutability_orm_listener(db_session):
    """Verify that SQLAlchemy ORM listeners block UPDATE and DELETE on ReportVersionModel."""
    _, _, _, report, ver_model = await _seed_test_hierarchy(db_session)
    ver_id = ver_model.id

    # Attempt ORM-level UPDATE -> Must raise ImmutableReportOverrideError
    ver_model.impression = "Mutated impression attempt"
    with pytest.raises(ImmutableReportOverrideError) as exc_info:
        await db_session.flush()
    assert "strictly append-only" in str(exc_info.value)
    await db_session.rollback()

    # Re-seed fresh record and attempt ORM-level DELETE -> Must raise ImmutableReportOverrideError
    _, _, _, _, fresh_ver = await _seed_test_hierarchy(db_session)
    await db_session.delete(fresh_ver)
    with pytest.raises(ImmutableReportOverrideError) as exc_info:
        await db_session.flush()
    assert "strictly append-only" in str(exc_info.value)
    await db_session.rollback()


@pytest.mark.asyncio
async def test_report_version_immutability_db_trigger(db_session):
    """Verify that PostgreSQL database trigger 'trg_report_versions_append_only' blocks raw SQL mutation."""
    _, _, _, _, ver_model = await _seed_test_hierarchy(db_session)
    ver_id = ver_model.id

    # 1. Attempt raw SQL UPDATE -> Must trigger PostgreSQL exception
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("UPDATE report_versions SET impression = 'Hacked by raw SQL' WHERE id = :vid"),
            {"vid": ver_id},
        )
    assert "strictly append-only" in str(exc_info.value)
    await db_session.rollback()

    # 2. Attempt raw SQL DELETE -> Must trigger PostgreSQL exception
    _, _, _, _, fresh_ver = await _seed_test_hierarchy(db_session)
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("DELETE FROM report_versions WHERE id = :vid"),
            {"vid": fresh_ver.id},
        )
    assert "strictly append-only" in str(exc_info.value)
    await db_session.rollback()


@pytest.mark.asyncio
async def test_transactional_outbox_pattern_and_batch_processing(db_session):
    """Verify atomic persistence of audit log + outbox event and downstream batch processing."""
    audit_repo = AuditRepository(db_session)
    res_id = f"STU-{uuid.uuid4().hex[:6]}"

    audit_entry = AuditLog(
        actor_id="AI_TRIAGE_AGENT",
        action="TRIAGE_COMPLETED",
        resource_id=res_id,
        correlation_id=f"corr-{uuid.uuid4().hex[:8]}",
        details={"priority": "STAT", "detected_critical_findings": True},
    )

    outbox_event = await audit_repo.record_with_outbox(
        audit_log=audit_entry,
        aggregate_type="STUDY",
        aggregate_id=res_id,
        event_type="study.triaged",
        payload={"study_id": res_id, "priority": "STAT"},
    )
    await db_session.commit()

    assert outbox_event.id is not None
    assert outbox_event.processed_at is None

    # Test processing the outbox batch
    processed_count = await process_outbox_batch(batch_size=10)
    assert processed_count >= 1

    # Verify event is now marked as processed
    async with AsyncSessionLocal() as verify_session:
        refreshed_event = await verify_session.get(OutboxEventModel, outbox_event.id)
        assert refreshed_event is not None
        assert refreshed_event.processed_at is not None


def test_celery_outbox_worker_task():
    """Verify Celery task execution for outbox worker."""
    result = process_outbox_events_task.apply(kwargs={"batch_size": 10})
    assert result.successful()
    data = result.result
    assert data["status"] == "SUCCESS"
    assert "events_processed" in data
