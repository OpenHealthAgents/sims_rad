"""
Unit Tests: WorkItem Domain Entity.
Validates attributes, initial state, priority, SLA deadlines, versioning, and assignment.
"""
from datetime import datetime, timedelta, timezone
import pytest
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState


def test_work_item_creation():
    deadline = datetime.now(timezone.utc) + timedelta(minutes=60)
    item = WorkItem(
        work_item_id="wi-101",
        study_id="std-101",
        state=WorkItemState.RECEIVED,
        priority=Priority.URGENT,
        assigned_radiologist_id=None,
        sla_deadline=deadline,
        version=1,
    )

    assert item.work_item_id == "wi-101"
    assert item.study_id == "std-101"
    assert item.state == WorkItemState.RECEIVED
    assert item.priority == Priority.URGENT
    assert item.assigned_radiologist_id is None
    assert item.sla_deadline == deadline
    assert item.version == 1


def test_work_item_assignment_and_unassignment():
    item = WorkItem(
        work_item_id="wi-102",
        study_id="std-102",
        state=WorkItemState.READY,
        priority=Priority.STAT,
    )

    item.assign_to("rad-dr-smith")
    assert item.assigned_radiologist_id == "rad-dr-smith"

    item.unassign()
    assert item.assigned_radiologist_id is None

    with pytest.raises(ValueError):
        item.assign_to("")


def test_priority_sla_turnaround_times():
    assert Priority.STAT.max_turnaround_minutes == 15
    assert Priority.URGENT.max_turnaround_minutes == 60
    assert Priority.ROUTINE.max_turnaround_minutes == 240
