"""
Domain Entity: WorkItem (Clean Architecture).
Represents a clinical task/worklist item within the radiology reading lifecycle.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class WorkItemState(str, Enum):
    RECEIVED = "received"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    READY = "ready"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DRAFT_READY = "draft_ready"
    IN_REVIEW = "in_review"
    FINALIZED = "finalized"
    DELIVERED = "delivered"
    AMENDED = "amended"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    STAT = "STAT"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"

    @property
    def max_turnaround_minutes(self) -> int:
        match self:
            case Priority.STAT:
                return 15
            case Priority.URGENT:
                return 60
            case Priority.ROUTINE:
                return 240


@dataclass
class WorkItem:
    """
    WorkItem domain entity.
    Maintains clinical state, assignment, SLA deadlines, and optimistic concurrency version.
    """
    work_item_id: str
    study_id: str
    state: WorkItemState = WorkItemState.RECEIVED
    priority: Priority = Priority.ROUTINE
    assigned_radiologist_id: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def assign_to(self, radiologist_id: str) -> None:
        """Assign radiologist to work item."""
        if not radiologist_id or not radiologist_id.strip():
            raise ValueError("assigned_radiologist_id cannot be empty.")
        self.assigned_radiologist_id = radiologist_id
        self.updated_at = datetime.now(timezone.utc)

    def unassign(self) -> None:
        """Unassign radiologist from work item."""
        self.assigned_radiologist_id = None
        self.updated_at = datetime.now(timezone.utc)
