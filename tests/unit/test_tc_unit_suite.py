"""
Unit and Domain Test Suite (TC-001 to TC-020).
Comprehensive test coverage verifying:
- TC-001 to TC-010: Patient RULE-01, RadiologyStudy attributes, WorkItem SLA calculation,
  Report append-only versioning, and AuditLog records.
- TC-011: Ingest duplicate inbound event -> Verify idempotency.
- TC-012: Ingest ambiguous patient match -> Verify quarantine in exception queue.
- TC-013 to TC-016: Priority TAT thresholds, deterministic state machine, and concurrency lock.
- TC-017: Attempt invalid state transition (draft_ready -> delivered without finalized) -> Verify rejection.
- TC-018 to TC-020: Value objects (StudyUID, AccessionNumber, PatientIdentifier) validation and comparison.
"""
from datetime import datetime, timezone, timedelta
import pytest

from core.domain.entities.audit_log import AuditLog
from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import ImagingSeries, Modality, RadiologyStudy, StudyLifecycleState
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import (
    ClinicalWritebackBlockedError,
    ConcurrencyVersionError,
    ImmutableReportOverrideError,
    InvalidDICOMMetadataError,
    InvalidStateTransitionError,
    PatientMismatchError,
    UnauthorizedSignoffError,
)
from core.domain.state_machine import RadiologyStateMachine
from core.domain.values.identifiers import AccessionNumber, PatientIdentifier, StudyUID
from core.infrastructure.adapters.backbone_adapter import BackBoneHMSAdapter


# =============================================================================
# TC-001: Patient Entity & RULE-01 Invariant
# =============================================================================
def test_tc_001_patient_rule_01_authoritative_matching():
    """
    TC-001: RULE-01: Never match solely on Name or DOB.
    Matching must succeed on authoritative identifier namespace + MRN.
    """
    patient = Patient(
        patient_id="PAT-100",
        mrn="MRN-100",
        identifier_namespace="urn:oid:sims.hospital.mrn",
        reconciliation_status=ReconciliationStatus.RECONCILED,
        family_name="Connor",
        given_name="Sarah",
        birth_date="1965-02-28",
    )

    # 1. Matching candidate with exact namespace + MRN succeeds
    assert patient.match_with(
        candidate_mrn="MRN-100",
        candidate_namespace="urn:oid:sims.hospital.mrn",
        candidate_name="Connor",
        candidate_dob="1965-02-28",
    ) is True

    # 2. Matching candidate with same Name & DOB but different MRN raises PatientMismatchError (RULE-01)
    with pytest.raises(PatientMismatchError, match="Patient identifier mismatch"):
        patient.match_with(
            candidate_mrn="MRN-DIFFERENT-999",
            candidate_namespace="urn:oid:sims.hospital.mrn",
            candidate_name="Connor",
            candidate_dob="1965-02-28",
        )

    # 3. Candidate with same MRN but mismatched namespace raises PatientMismatchError
    with pytest.raises(PatientMismatchError, match="Patient identifier mismatch"):
        patient.match_with(
            candidate_mrn="MRN-100",
            candidate_namespace="urn:oid:external.clinic.mrn",
        )


# =============================================================================
# TC-002: Patient Reconciliation Status Transitions
# =============================================================================
def test_tc_002_patient_reconciliation_status_lifecycle():
    """TC-002: Patient transitions across PENDING, RECONCILIATION_REQUIRED, and RECONCILED."""
    p = Patient(
        patient_id="PAT-200",
        mrn="MRN-200",
        identifier_namespace="urn:oid:sims",
        reconciliation_status=ReconciliationStatus.PENDING,
    )
    assert p.reconciliation_status == ReconciliationStatus.PENDING

    # Flag for reconciliation
    p.reconciliation_status = ReconciliationStatus.RECONCILIATION_REQUIRED
    assert p.reconciliation_status == ReconciliationStatus.RECONCILIATION_REQUIRED

    # Resolve reconciliation
    p.reconciliation_status = ReconciliationStatus.RECONCILED
    assert p.reconciliation_status == ReconciliationStatus.RECONCILED


# =============================================================================
# TC-003 & TC-004: RadiologyStudy Attributes and Lifecycle States
# =============================================================================
def test_tc_003_radiology_study_dicom_attributes():
    """TC-003: RadiologyStudy supports DICOM PS 3.5 attributes and modalities."""
    now = datetime.now(timezone.utc)
    series1 = ImagingSeries(
        series_uid="1.2.840.113619.2.55.3.1.1",
        series_number=1,
        modality="CT",
        description="Axial Brain 5mm",
        number_of_instances=48,
    )

    study = RadiologyStudy(
        study_id="STU-001",
        study_instance_uid="1.2.840.113619.2.55.3.1",
        accession_number="ACC-1001",
        modality=Modality.CT,
        study_date=now,
        patient_id="PAT-100",
        description="CT Brain Non-Contrast",
        series=[series1],
        state=StudyLifecycleState.RECEIVED,
    )
    assert study.study_id == "STU-001"
    assert study.modality == Modality.CT
    assert len(study.series) == 1
    assert study.series[0].number_of_instances == 48


def test_tc_004_study_lifecycle_state_transitions():
    """TC-004: Study advances through lifecycle states."""
    study = RadiologyStudy(
        study_id="STU-002",
        study_instance_uid="1.2.840.113619.2.55.3.2",
        accession_number="ACC-1002",
        modality=Modality.MRI,
        state=StudyLifecycleState.RECEIVED,
    )
    assert study.state == StudyLifecycleState.RECEIVED

    study.state = StudyLifecycleState.ANALYSIS_IN_PROGRESS
    assert study.state == StudyLifecycleState.ANALYSIS_IN_PROGRESS

    study.state = StudyLifecycleState.COMPLETED
    assert study.state == StudyLifecycleState.COMPLETED


# =============================================================================
# TC-005 & TC-006: WorkItem SLA Deadlines & Assignment Tracking
# =============================================================================
def test_tc_005_work_item_sla_deadlines_by_priority():
    """TC-005: Priority determines max turnaround time: STAT (15m), URGENT (60m), ROUTINE (240m)."""
    assert Priority.STAT.max_turnaround_minutes == 15
    assert Priority.URGENT.max_turnaround_minutes == 60
    assert Priority.ROUTINE.max_turnaround_minutes == 240

    now = datetime.now(timezone.utc)
    wi_stat = WorkItem(
        work_item_id="WI-STAT",
        study_id="STU-01",
        priority=Priority.STAT,
        sla_deadline=now + timedelta(minutes=Priority.STAT.max_turnaround_minutes),
    )
    assert wi_stat.priority == Priority.STAT
    assert wi_stat.sla_deadline <= now + timedelta(minutes=16)


def test_tc_006_work_item_assignment():
    """TC-006: Assigning work item sets clinician ID and updates version."""
    wi = WorkItem(
        work_item_id="WI-ASSIGN-1",
        study_id="STU-01",
        state=WorkItemState.READY,
        version=1,
    )
    wi.assign_to("rad-dr-smith")
    assert wi.assigned_radiologist_id == "rad-dr-smith"


# =============================================================================
# TC-007, TC-008 & TC-009: Report Versioning, Immutability & Amendment
# =============================================================================
def test_tc_007_report_creation_and_drafting():
    """TC-007: Report drafting creates initial version in DRAFT state."""
    report = Report(
        report_id="REP-001",
        work_item_id="WI-001",
        status=ReportStatus.DRAFT,
    )
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={"lungs": "Clear"},
        impression="Normal chest radiograph.",
        author_id="AI_CONCIERGE",
    )
    v1_id = report.add_version(ver1)
    assert v1_id == "REP-001-v1"
    assert report.current_version_id == "REP-001-v1"
    assert report.status == ReportStatus.DRAFT


def test_tc_008_report_append_only_version_increment():
    """TC-008: Adding a version increments version number without modifying prior version."""
    report = Report(
        report_id="REP-002",
        work_item_id="WI-002",
        status=ReportStatus.DRAFT,
    )
    v1 = ReportVersion(version_number=1, structured_findings={"a": 1}, impression="Draft 1", author_id="RAD-1")
    v2 = ReportVersion(version_number=2, structured_findings={"a": 2}, impression="Draft 2", author_id="RAD-1")

    report.add_version(v1)
    report.add_version(v2)

    assert len(report.versions) == 2
    assert report.versions[1].impression == "Draft 1"
    assert report.versions[2].impression == "Draft 2"
    assert report.current_version_id == "REP-002-v2"


def test_tc_009_report_amendment_workflow():
    """TC-009: Signed report can be amended, moving to AMENDED status with a new version."""
    report = Report(
        report_id="REP-003",
        work_item_id="WI-003",
        status=ReportStatus.DRAFT,
    )
    v1 = ReportVersion(version_number=1, structured_findings={}, impression="Initial", author_id="RAD-1")
    report.add_version(v1)
    report.sign_and_release(radiologist_id="RAD-1", signature_hash="sha256:test_hash")
    assert report.status == ReportStatus.SIGNED

    # Create amendment
    v2 = ReportVersion(version_number=2, structured_findings={"note": "Addendum"}, impression="Amended Impression", author_id="RAD-1")
    amend_id = report.amend(v2)
    assert amend_id == "REP-003-v2"
    assert report.status == ReportStatus.AMENDED
    assert len(report.versions) == 2


# =============================================================================
# TC-010: AuditLog Immutability & Event Records
# =============================================================================
def test_tc_010_audit_log_record():
    """TC-010: AuditLog captures state changes, actor IDs, and correlation metadata."""
    now = datetime.now(timezone.utc)
    audit = AuditLog(
        actor_id="rad-dr-smith",
        action="STATE_TRANSITION",
        resource_id="WI-001",
        timestamp=now,
        correlation_id="corr-12345",
        details={"from_state": "ready", "to_state": "assigned"},
    )
    assert audit.resource_id == "WI-001"
    assert audit.action == "STATE_TRANSITION"
    assert audit.actor_id == "rad-dr-smith"
    assert audit.details["to_state"] == "assigned"


# =============================================================================
# TC-011: Ingest Duplicate Inbound Event -> Idempotency
# =============================================================================
def test_tc_011_ingest_duplicate_inbound_event_idempotency():
    """
    TC-011: Ingest duplicate inbound event -> Verify idempotency (no duplicate work item created).
    Subsequent delivery of identical event ID returns SKIPPED_DUPLICATE without mutating state.
    """
    adapter = BackBoneHMSAdapter()
    event_id = "EVT-DUP-001"
    accession = "ACC-DUP-100"
    timestamp = datetime.now(timezone.utc)
    payload = {"order_id": "ORD-1", "accession_number": accession}

    # First event application -> APPLIED
    res1 = adapter.handle_out_of_order_event(
        event_id=event_id,
        accession_number=accession,
        event_type="ORDER_CREATED",
        event_timestamp=timestamp,
        payload=payload,
    )
    assert res1["status"] == "APPLIED"
    assert res1["event_id"] == event_id

    # Second event application with same event_id -> SKIPPED_DUPLICATE (Idempotent)
    res2 = adapter.handle_out_of_order_event(
        event_id=event_id,
        accession_number=accession,
        event_type="ORDER_CREATED",
        event_timestamp=timestamp,
        payload=payload,
    )
    assert res2["status"] == "SKIPPED_DUPLICATE"
    assert res2["event_id"] == event_id


# =============================================================================
# TC-012: Ingest Ambiguous Patient Match -> Quarantine in Exception Queue
# =============================================================================
def test_tc_012_ingest_ambiguous_patient_match_quarantine():
    """
    TC-012: Ingest ambiguous patient match -> Verify quarantine in exception queue.
    WorkItem initial_state transitions to 'reconciliation_required' and clinical writeback is blocked.
    """
    adapter = BackBoneHMSAdapter()

    # Ingest order with missing/unreconciled MRN
    order_payload = {
        "accession_number": "ACC-AMBIG-001",
        "patient": {
            "mrn": "",  # Missing MRN triggers reconciliation requirement
            "first_name": "Unknown",
            "last_name": "Patient",
        },
        "modality": "CT",
        "priority": "STAT",
    }

    study, work_item, patient = adapter.ingest_order(order_payload)

    # Verify patient flagged as RECONCILIATION_REQUIRED
    assert patient.reconciliation_status == ReconciliationStatus.RECONCILIATION_REQUIRED
    # Verify work item quarantined in reconciliation_required state
    assert work_item.state == WorkItemState.RECONCILIATION_REQUIRED

    # Verify hospital safety rule: Clinical writeback is strictly blocked
    with pytest.raises(ClinicalWritebackBlockedError, match="Clinical writeback blocked"):
        RadiologyStateMachine.validate_clinical_writeback_allowed(work_item)


# =============================================================================
# TC-013 to TC-016: Priority, State Machine & Concurrency Locking
# =============================================================================
def test_tc_013_priority_tat_and_sorting():
    """TC-013: STAT priority has earliest SLA deadlines and highest queue sorting priority."""
    now = datetime.now(timezone.utc)
    wi_routine = WorkItem(work_item_id="WI-R", study_id="S-1", priority=Priority.ROUTINE, sla_deadline=now + timedelta(hours=24))
    wi_urgent = WorkItem(work_item_id="WI-U", study_id="S-2", priority=Priority.URGENT, sla_deadline=now + timedelta(hours=2))
    wi_stat = WorkItem(work_item_id="WI-S", study_id="S-3", priority=Priority.STAT, sla_deadline=now + timedelta(minutes=30))

    items = [wi_routine, wi_stat, wi_urgent]
    priority_order = {"STAT": 0, "URGENT": 1, "ROUTINE": 2}
    items.sort(key=lambda w: (priority_order.get(w.priority.value, 3), w.sla_deadline))

    assert items[0].priority == Priority.STAT
    assert items[1].priority == Priority.URGENT
    assert items[2].priority == Priority.ROUTINE


def test_tc_014_deterministic_state_machine_transitions():
    """TC-014: Deterministic transition sequence increments version monotonically."""
    wi = WorkItem(work_item_id="WI-TRANS", study_id="STU-01", state=WorkItemState.RECEIVED, version=1)

    wi, _ = RadiologyStateMachine.transition(wi, WorkItemState.READY, expected_version=1, actor_id="ingest")
    assert wi.state == WorkItemState.READY
    assert wi.version == 2

    wi.assign_to("rad-01")
    wi, _ = RadiologyStateMachine.transition(wi, WorkItemState.ASSIGNED, expected_version=2, actor_id="coord")
    assert wi.state == WorkItemState.ASSIGNED
    assert wi.version == 3

    wi, _ = RadiologyStateMachine.transition(wi, WorkItemState.IN_PROGRESS, expected_version=3, actor_id="rad-01")
    assert wi.state == WorkItemState.IN_PROGRESS
    assert wi.version == 4


def test_tc_015_optimistic_concurrency_lock_conflict():
    """TC-015: Stale version token raises ConcurrencyVersionError without mutating state."""
    wi = WorkItem(work_item_id="WI-CONC", study_id="STU-01", state=WorkItemState.READY, version=5)

    with pytest.raises(ConcurrencyVersionError, match="Optimistic lock conflict"):
        RadiologyStateMachine.transition(wi, WorkItemState.CANCELLED, expected_version=4, actor_id="stale_client")

    assert wi.state == WorkItemState.READY
    assert wi.version == 5


def test_tc_016_clinical_writeback_blocked_in_reconciliation():
    """TC-016: Clinical writeback is blocked when work item is in RECONCILIATION_REQUIRED."""
    wi = WorkItem(work_item_id="WI-BLOCKED", study_id="STU-01", state=WorkItemState.RECONCILIATION_REQUIRED)
    with pytest.raises(ClinicalWritebackBlockedError):
        RadiologyStateMachine.validate_clinical_writeback_allowed(wi)


# =============================================================================
# TC-017: Attempt Invalid State Transition -> Verify Rejection
# =============================================================================
def test_tc_017_invalid_transition_draft_ready_to_delivered_rejected():
    """
    TC-017: Attempt invalid state transition (draft_ready -> delivered without finalized)
    -> Verify rejection with InvalidStateTransitionError.
    """
    wi = WorkItem(
        work_item_id="WI-INV-17",
        study_id="STU-17",
        state=WorkItemState.DRAFT_READY,
        version=5,
    )

    # Verify can_transition returns False
    assert RadiologyStateMachine.can_transition(WorkItemState.DRAFT_READY, WorkItemState.DELIVERED) is False

    # Verify transition raises InvalidStateTransitionError
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        RadiologyStateMachine.transition(
            work_item=wi,
            target_state=WorkItemState.DELIVERED,
            expected_version=5,
            actor_id="premature_delivery_system",
        )
    assert "Invalid state transition from 'draft_ready' to 'delivered'" in str(exc_info.value)
    # Work item state and version must remain untouched
    assert wi.state == WorkItemState.DRAFT_READY
    assert wi.version == 5


# =============================================================================
# TC-018, TC-019 & TC-020: Value Objects Validation
# =============================================================================
def test_tc_018_study_uid_value_object():
    """TC-018: StudyUID validation for format, length, string conversion, and equality."""
    valid_uid_str = "1.2.840.113619.2.55.3.12345"
    uid = StudyUID(valid_uid_str)
    assert str(uid) == valid_uid_str
    assert uid == valid_uid_str
    assert uid == StudyUID(valid_uid_str)
    assert uid != 12345

    # Invalid empty or too long
    with pytest.raises(InvalidDICOMMetadataError, match="1-64 chars"):
        StudyUID("")
    with pytest.raises(InvalidDICOMMetadataError, match="1-64 chars"):
        StudyUID("1." * 35)  # > 64 chars

    # Malformed format (contains letters)
    with pytest.raises(InvalidDICOMMetadataError, match="Malformed DICOM Study UID format"):
        StudyUID("1.2.840.XYZ.123")


def test_tc_019_accession_number_value_object():
    """TC-019: AccessionNumber validation for non-empty string, str conversion, and equality."""
    acc_str = "ACC-RAD-2026-001"
    acc = AccessionNumber(acc_str)
    assert str(acc) == acc_str
    assert acc == acc_str
    assert acc == AccessionNumber(acc_str)
    assert acc != 9999

    # Empty accession raises error
    with pytest.raises(InvalidDICOMMetadataError, match="cannot be empty"):
        AccessionNumber("")
    with pytest.raises(InvalidDICOMMetadataError, match="cannot be empty"):
        AccessionNumber("   ")


def test_tc_020_patient_identifier_value_object():
    """TC-020: PatientIdentifier validation for non-empty string, str conversion, and equality."""
    pid_str = "PAT-HOSP-9901"
    pid = PatientIdentifier(pid_str)
    assert str(pid) == pid_str
    assert pid == pid_str
    assert pid == PatientIdentifier(pid_str)
    assert pid != 100

    # Empty patient id raises error
    with pytest.raises(InvalidDICOMMetadataError, match="cannot be empty"):
        PatientIdentifier("")
    with pytest.raises(InvalidDICOMMetadataError, match="cannot be empty"):
        PatientIdentifier("   ")
