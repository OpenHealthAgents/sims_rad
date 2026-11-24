"""
Application Layer DTOs: Report & Diagnostic Inference contracts (Pydantic v2).
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from core.domain.values.triage_priority import TriagePriority


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FindingDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    anatomical_location: str
    is_critical: bool = False
    shap_attribution_score: Optional[float] = None
    slice_index: Optional[int] = None


class DiagnosticTriageResultDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_uid: str
    triage_priority: TriagePriority
    findings: List[FindingDTO]
    impression: str
    guardrail_passed: bool
    guardrail_reasons: List[str] = Field(default_factory=list)
    shap_summary: Optional[dict] = None
    processed_at: datetime = Field(default_factory=get_utc_now)
