"""
Unit Tests: Deterministic State Machine Engine (`core/domain/state_machine.py`).
Validates allowed transition paths, concurrency checks via version numbers,
exception/cancellation branches, and clinical writeback guards.
"""
import pytest
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import (
    ClinicalWritebackBlockedError,
    ConcurrencyVersionError,
    InvalidStateTransitionError,
)
from core.domain.state_machine import RadiologyStateMachine


def test_standard_happy_path_transitions_and_version_increments():
    """
    Test standard deterministic happy path:
    received -> ready -> assigned -> in_progress -> draft_ready -> in_review -> finalized -> delivered
    Verifies that each successful transition increments version monotonically.
    """
    wi = WorkItem(work_item_id="wi-flow-1", study_id="std-1", state=WorkItemState.RECEIVED, version=1)

    # 1. received -> ready (version 1 -> 2)
    wi, log = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.READY,
        expected_version=1,
        actor_id="ingestion-service",
        correlation_id="corr-1",
    )
    assert wi.state == WorkItemState.READY
    assert wi.version == 2
    assert log.action == "STATE_TRANSITION"
    assert log.details["from_state"] == "received"
    assert log.details["to_state"] == "ready"

    # Assign radiologist before transitioning to ASSIGNED
    wi.assign_to("rad-dr-evans")

    # 2. ready -> assigned (version 2 -> 3)
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.ASSIGNED,
        expected_version=2,
        actor_id="triage-dispatcher",
    )
    assert wi.state == WorkItemState.ASSIGNED
    assert wi.version == 3

    # 3. assigned -> in_progress (version 3 -> 4)
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.IN_PROGRESS,
        expected_version=3,
        actor_id="rad-dr-evans",
    )
    assert wi.state == WorkItemState.IN_PROGRESS
    assert wi.version == 4

    # 4. in_progress -> draft_ready (version 4 -> 5)
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.DRAFT_READY,
        expected_version=4,
        actor_id="ai-agent-deepagents",
    )
    assert wi.state == WorkItemState.DRAFT_READY
    assert wi.version == 5

    # 5. draft_ready -> in_review (version 5 -> 6)
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.IN_REVIEW,
        expected_version=5,
        actor_id="rad-dr-evans",
    )
    assert wi.state == WorkItemState.IN_REVIEW
    assert wi.version == 6

    # 6. in_review -> finalized (version 6 -> 7)
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.FINALIZED,
        expected_version=6,
        actor_id="rad-dr-evans",
    )
    assert wi.state == WorkItemState.FINALIZED
    assert wi.version == 7

    # 7. finalized -> delivered (version 7 -> 8)
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.DELIVERED,
        expected_version=7,
        actor_id="hl7-delivery-connector",
    )
    assert wi.state == WorkItemState.DELIVERED
    assert wi.version == 8


def test_reconciliation_branch_and_resolution():
    """
    Test reconciliation flow:
    received -> reconciliation_required -> ready
    """
    wi = WorkItem(work_item_id="wi-recon-1", study_id="std-2", state=WorkItemState.RECEIVED, version=1)

    # received -> reconciliation_required
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.RECONCILIATION_REQUIRED,
        expected_version=1,
        actor_id="him-identity-matcher",
        reason="Patient MRN conflict detected in ADT feed.",
    )
    assert wi.state == WorkItemState.RECONCILIATION_REQUIRED
    assert wi.version == 2

    # reconciliation_required -> ready
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.READY,
        expected_version=2,
        actor_id="him-supervisor",
        reason="Patient identity confirmed against Master Patient Index.",
    )
    assert wi.state == WorkItemState.READY
    assert wi.version == 3


def test_amendment_path_from_delivered():
    """
    Test amendment path:
    delivered -> amended -> delivered
    """
    wi = WorkItem(work_item_id="wi-amend-1", study_id="std-3", state=WorkItemState.DELIVERED, version=10)

    # delivered -> amended
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.AMENDED,
        expected_version=10,
        actor_id="rad-dr-evans",
        reason="Addendum needed for secondary fracture finding.",
    )
    assert wi.state == WorkItemState.AMENDED
    assert wi.version == 11

    # amended -> delivered
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.DELIVERED,
        expected_version=11,
        actor_id="hl7-delivery-connector",
    )
    assert wi.state == WorkItemState.DELIVERED
    assert wi.version == 12


def test_exception_and_cancellation_branches():
    """Test exception and cancellation branches from various states."""
    # From in_progress to exception
    wi = WorkItem(work_item_id="wi-ex-1", study_id="std-4", state=WorkItemState.IN_PROGRESS, version=4)
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.EXCEPTION,
        expected_version=4,
        actor_id="ai-pipeline",
        reason="Corrupt DICOM pixel data encountered.",
    )
    assert wi.state == WorkItemState.EXCEPTION

    # Exception resolved back to ready
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.READY,
        expected_version=5,
        actor_id="pacs-engineer",
        reason="Series re-transferred from scanner successfully.",
    )
    assert wi.state == WorkItemState.READY

    # From ready to cancelled
    wi, _ = RadiologyStateMachine.transition(
        work_item=wi,
        target_state=WorkItemState.CANCELLED,
        expected_version=6,
        actor_id="ordering-physician",
        reason="Exam cancelled by attending physician.",
    )
    assert wi.state == WorkItemState.CANCELLED

    # Cancelled is terminal: cannot transition anywhere
    assert RadiologyStateMachine.can_transition(WorkItemState.CANCELLED, WorkItemState.READY) is False
    with pytest.raises(InvalidStateTransitionError):
        RadiologyStateMachine.transition(
            work_item=wi,
            target_state=WorkItemState.READY,
            expected_version=7,
            actor_id="any",
        )


def test_invalid_state_transitions_raise_error():
    """Verify unauthorized transition paths raise InvalidStateTransitionError."""
    wi = WorkItem(work_item_id="wi-inv-1", study_id="std-5", state=WorkItemState.RECEIVED, version=1)

    # Direct jump: received -> finalized is strictly forbidden
    with pytest.raises(InvalidStateTransitionError, match="Invalid state transition from 'received' to 'finalized'"):
        RadiologyStateMachine.transition(
            work_item=wi,
            target_state=WorkItemState.FINALIZED,
            expected_version=1,
            actor_id="test",
        )

    # ready -> delivered without reading/signing is forbidden
    wi.state = WorkItemState.READY
    with pytest.raises(InvalidStateTransitionError, match="Invalid state transition from 'ready' to 'delivered'"):
        RadiologyStateMachine.transition(
            work_item=wi,
            target_state=WorkItemState.DELIVERED,
            expected_version=1,
            actor_id="test",
        )


def test_assigned_requires_radiologist_id():
    """Transition to 'assigned' requires an assigned_radiologist_id."""
    wi = WorkItem(
        work_item_id="wi-unassigned",
        study_id="std-6",
        state=WorkItemState.READY,
        assigned_radiologist_id=None,
        version=1,
    )
    with pytest.raises(InvalidStateTransitionError, match="without an assigned_radiologist_id"):
        RadiologyStateMachine.transition(
            work_item=wi,
            target_state=WorkItemState.ASSIGNED,
            expected_version=1,
            actor_id="dispatcher",
        )


def test_optimistic_concurrency_version_check():
    """Verify concurrency conflict is caught when version token mismatches."""
    wi = WorkItem(
        work_item_id="wi-concurrent",
        study_id="std-7",
        state=WorkItemState.READY,
        version=5,
    )

    # Stale version token: expected 4, actual is 5
    with pytest.raises(ConcurrencyVersionError, match="Optimistic lock conflict"):
        RadiologyStateMachine.transition(
            work_item=wi,
            target_state=WorkItemState.CANCELLED,
            expected_version=4,
            actor_id="actor-a",
        )

    # State and version must remain completely untouched
    assert wi.state == WorkItemState.READY
    assert wi.version == 5


def test_clinical_writeback_blocked_in_reconciliation_required():
    """
    Hospital safety invariant:
    Clinical writeback must be strictly blocked if state is reconciliation_required.
    """
    wi_recon = WorkItem(
        work_item_id="wi-blocked",
        study_id="std-8",
        state=WorkItemState.RECONCILIATION_REQUIRED,
    )

    with pytest.raises(ClinicalWritebackBlockedError, match="Clinical writeback blocked"):
        RadiologyStateMachine.validate_clinical_writeback_allowed(wi_recon)

    with pytest.raises(ClinicalWritebackBlockedError, match="Clinical writeback blocked"):
        RadiologyStateMachine.validate_clinical_writeback_allowed(WorkItemState.RECONCILIATION_REQUIRED)

    # For other active states, clinical writeback check passes
    wi_ready = WorkItem(work_item_id="wi-ok", study_id="std-8", state=WorkItemState.READY)
    RadiologyStateMachine.validate_clinical_writeback_allowed(wi_ready)
    RadiologyStateMachine.validate_clinical_writeback_allowed(WorkItemState.FINALIZED)
