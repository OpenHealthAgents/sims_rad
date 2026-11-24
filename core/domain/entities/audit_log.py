"""
Domain Entity: AuditLog (Clean Architecture).
Immutable event capture for full clinical compliance, regulatory auditability,
and chain-of-custody tracking.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AuditLog:
    """
    Immutable audit log entry.
    Required attributes:
    - actor_id: ID of the clinician, AI agent, or system service
    - action: Description of the action (e.g. WORK_ITEM_TRANSITION, REPORT_SIGNED)
    - resource_id: Targeted domain entity ID (study, work_item, report)
    - timestamp: UTC timestamp of the event
    - correlation_id: Distributed tracing correlation ID
    - details: Optional supplementary contextual metadata
    """
    actor_id: str
    action: str
    resource_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str = ""
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.actor_id or not self.actor_id.strip():
            raise ValueError("actor_id cannot be empty.")
        if not self.action or not self.action.strip():
            raise ValueError("action cannot be empty.")
        if not self.resource_id or not self.resource_id.strip():
            raise ValueError("resource_id cannot be empty.")
