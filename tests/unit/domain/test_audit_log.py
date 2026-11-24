"""
Unit Tests: AuditLog Domain Entity.
Validates immutability invariants and required audit fields.
"""
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import pytest
from core.domain.entities.audit_log import AuditLog


def test_audit_log_creation():
    ts = datetime.now(timezone.utc)
    entry = AuditLog(
        actor_id="rad-dr-smith",
        action="REPORT_SIGNED",
        resource_id="rep-101",
        timestamp=ts,
        correlation_id="corr-987654",
        details={"status": "SIGNED", "version": 1},
    )

    assert entry.actor_id == "rad-dr-smith"
    assert entry.action == "REPORT_SIGNED"
    assert entry.resource_id == "rep-101"
    assert entry.timestamp == ts
    assert entry.correlation_id == "corr-987654"
    assert entry.details == {"status": "SIGNED", "version": 1}


def test_audit_log_immutability():
    entry = AuditLog(
        actor_id="system-agent",
        action="STUDY_INGESTED",
        resource_id="std-001",
    )

    with pytest.raises(FrozenInstanceError):
        entry.action = "MUTATED_ACTION"  # type: ignore

    with pytest.raises(FrozenInstanceError):
        entry.actor_id = "hacker"  # type: ignore


def test_audit_log_validation_empty_fields_fail():
    with pytest.raises(ValueError):
        AuditLog(actor_id="", action="ACT", resource_id="res-1")

    with pytest.raises(ValueError):
        AuditLog(actor_id="act-1", action="", resource_id="res-1")

    with pytest.raises(ValueError):
        AuditLog(actor_id="act-1", action="ACT", resource_id="")
