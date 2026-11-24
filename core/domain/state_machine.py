"""
Deterministic State Machine Engine for the SIMS Radiology Platform.
Enforces strict clinical workflow lifecycle paths, optimistic concurrency locking,
and safety invariants (e.g. blocking clinical writeback during reconciliation).
"""
from datetime import datetime, timezone
from typing import Dict, Optional, Set, Tuple, Union

from core.domain.entities.audit_log import AuditLog
from core.domain.entities.work_item import WorkItem, WorkItemState
from core.domain.exceptions import (
    ClinicalWritebackBlockedError,
    ConcurrencyVersionError,
    InvalidStateTransitionError,
)

# Deterministic allowed transition table
# received -> reconciliation_required | ready -> assigned -> in_progress -> draft_ready -> in_review -> finalized -> delivered | amended
# Exception and cancellation branches supported from active states.
ALLOWED_TRANSITIONS: Dict[WorkItemState, Set[WorkItemState]] = {
    WorkItemState.RECEIVED: {
        WorkItemState.RECONCILIATION_REQUIRED,
        WorkItemState.READY,
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.RECONCILIATION_REQUIRED: {
        WorkItemState.READY,
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.READY: {
        WorkItemState.ASSIGNED,
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.ASSIGNED: {
        WorkItemState.IN_PROGRESS,
        WorkItemState.READY,  # Unassigned/returned to queue
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.IN_PROGRESS: {
        WorkItemState.DRAFT_READY,
        WorkItemState.ASSIGNED,
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.DRAFT_READY: {
        WorkItemState.IN_REVIEW,
        WorkItemState.IN_PROGRESS,  # Draft rejected back for reworking
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.IN_REVIEW: {
        WorkItemState.FINALIZED,
        WorkItemState.DRAFT_READY,
        WorkItemState.IN_PROGRESS,
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.FINALIZED: {
        WorkItemState.DELIVERED,
        WorkItemState.AMENDED,
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.DELIVERED: {
        WorkItemState.AMENDED,
        WorkItemState.EXCEPTION,
    },
    WorkItemState.AMENDED: {
        WorkItemState.IN_REVIEW,
        WorkItemState.FINALIZED,
        WorkItemState.DELIVERED,
        WorkItemState.EXCEPTION,
        WorkItemState.CANCELLED,
    },
    WorkItemState.EXCEPTION: {
        WorkItemState.READY,  # Resolved exception
        WorkItemState.CANCELLED,
    },
    WorkItemState.CANCELLED: set(),  # Terminal state
}


class RadiologyStateMachine:
    """
    Deterministic State Machine for WorkItem clinical workflow.
    """

    @classmethod
    def can_transition(
        cls, current_state: Union[WorkItemState, str], target_state: Union[WorkItemState, str]
    ) -> bool:
        """Check if transition between two states is valid according to deterministic graph."""
        curr = WorkItemState(current_state) if isinstance(current_state, str) else current_state
        target = WorkItemState(target_state) if isinstance(target_state, str) else target_state
        return target in ALLOWED_TRANSITIONS.get(curr, set())

    @classmethod
    def validate_clinical_writeback_allowed(cls, work_item_or_state: Union[WorkItem, WorkItemState, str]) -> None:
        """
        Block clinical writeback if state is `reconciliation_required`.
        Enforces hospital safety policy: clinical findings, reports, or results
        must never be written back to EHR/PACS while patient identity is in doubt.
        """
        state = (
            work_item_or_state.state
            if isinstance(work_item_or_state, WorkItem)
            else WorkItemState(work_item_or_state)
        )
        if state == WorkItemState.RECONCILIATION_REQUIRED:
            work_item_id = getattr(work_item_or_state, "work_item_id", "UNKNOWN")
            raise ClinicalWritebackBlockedError(
                f"Clinical writeback blocked for WorkItem '{work_item_id}': "
                "State is 'reconciliation_required'. Patient identity reconciliation must be completed first."
            )

    @classmethod
    def transition(
        cls,
        work_item: WorkItem,
        target_state: Union[WorkItemState, str],
        expected_version: int,
        actor_id: str,
        correlation_id: str = "",
        reason: str = "",
    ) -> Tuple[WorkItem, AuditLog]:
        """
        Execute deterministic state transition with concurrency verification.

        Parameters:
        - work_item: Domain WorkItem to transition
        - target_state: Desired destination WorkItemState
        - expected_version: Concurrency control version token
        - actor_id: ID of the clinician, agent, or service driving the transition
        - correlation_id: Tracing correlation ID
        - reason: Context or rationale for transition (e.g. exception details)

        Returns:
        - Tuple of (updated WorkItem, immutable AuditLog entry)
        """
        target = WorkItemState(target_state) if isinstance(target_state, str) else target_state
        current = work_item.state

        # 1. Concurrency Check via Version Number
        if work_item.version != expected_version:
            raise ConcurrencyVersionError(
                f"Optimistic lock conflict on WorkItem '{work_item.work_item_id}': "
                f"Expected version {expected_version}, but entity is at version {work_item.version}."
            )

        # 2. State Transition Graph Validation
        if not cls.can_transition(current, target):
            raise InvalidStateTransitionError(
                from_state=current.value,
                to_state=target.value,
                reason=reason or f"Path from {current.value} to {target.value} is not permitted.",
            )

        # 3. Business Invariant Checks
        if target == WorkItemState.ASSIGNED and not work_item.assigned_radiologist_id:
            raise InvalidStateTransitionError(
                from_state=current.value,
                to_state=target.value,
                reason="Cannot transition to 'assigned' without an assigned_radiologist_id.",
            )

        # 4. State Update and Version Increment
        old_state = work_item.state
        work_item.state = target
        work_item.version += 1
        work_item.updated_at = datetime.now(timezone.utc)

        # 5. Immutable Audit Log Creation
        audit_entry = AuditLog(
            actor_id=actor_id,
            action="STATE_TRANSITION",
            resource_id=work_item.work_item_id,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            details={
                "from_state": old_state.value,
                "to_state": target.value,
                "version_before": expected_version,
                "version_after": work_item.version,
                "reason": reason,
            },
        )

        return work_item, audit_entry
