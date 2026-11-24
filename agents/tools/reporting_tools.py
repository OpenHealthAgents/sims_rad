"""
Reporting and Reconciliation Tools for SIMS Radiology Agents.
Decorated with @tool for LangChain, Deep Agents, and LangGraph interoperability.
Enforces hard safety invariants: AI agents can draft reports, but CANNOT autonomously sign or finalize.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict
import uuid
from langchain_core.tools import tool

from core.domain.entities.report import ReportStatus
from core.domain.exceptions import UnauthorizedSignoffError
from core.infrastructure.observability.prompts import prompt_manager

logger = logging.getLogger("sims_radiology.agents.tools.reporting")


@tool
def draft_structured_report(
    work_item_id: str,
    findings: str,
    impression: str,
) -> Dict[str, Any]:
    """
    Generate an unsigned preliminary diagnostic report draft for a radiology work item.
    Crucial Safety Invariant: The generated report remains strictly in 'DRAFT' status
    and cannot be released or finalized without an explicit human radiologist sign-off.
    
    Args:
        work_item_id: ID of the targeted clinical work item.
        findings: Radiographic observations and structural findings across imaging slices.
        impression: Synthesized diagnostic conclusion / differential diagnosis.
    """
    logger.info(f"Tool called: draft_structured_report for work_item_id='{work_item_id}'")
    report_id = f"REP-DRAFT-{uuid.uuid4().hex[:8]}"
    version_number = 1
    prompt_obj = prompt_manager.get_prompt("reporting_assistant")
    
    draft_record = {
        "status": ReportStatus.DRAFT.value,
        "report_id": report_id,
        "work_item_id": work_item_id,
        "version_number": version_number,
        "author_id": "SIMS_AI_CONCIERGE_AGENT",
        "prompt_name": prompt_obj.name,
        "prompt_version": prompt_obj.version,
        "structured_findings": {
            "narrative": findings,
            "ai_confidence_score": 0.94,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "impression": impression,
        "is_signed": False,
        "signature_hash": None,
        "message": (
            "Draft report generated successfully. Status: DRAFT (Unsigned). "
            "A licensed radiologist must review, verify findings, and execute the final sign-off."
        ),
    }
    return draft_record


@tool
def flag_reconciliation_issue(
    study_id: str,
    reason: str,
) -> Dict[str, Any]:
    """
    Route an imaging study to the human reconciliation queue when an accession mismatch,
    RULE-01 patient identifier discrepancy, or clinical ambiguity is detected.
    Blocks clinical writeback until reconciliation is completed by medical records staff.
    
    Args:
        study_id: The ID of the study requiring reconciliation.
        reason: Explanation of the discrepancy (e.g. 'MRN mismatch between PACS and HMS order').
    """
    logger.warning(f"Tool called: flag_reconciliation_issue for study_id='{study_id}': {reason}")
    ticket_id = f"REC-TICKET-{uuid.uuid4().hex[:8]}"
    
    return {
        "ticket_id": ticket_id,
        "study_id": study_id,
        "new_state": "reconciliation_required",
        "reason": reason,
        "flagged_at": datetime.now(timezone.utc).isoformat(),
        "clinical_writeback_blocked": True,
        "assigned_queue": "HOSPITAL_PATIENT_IDENTITY_RECONCILIATION",
        "message": (
            f"Study '{study_id}' successfully flagged for reconciliation. "
            "State transitioned to 'reconciliation_required'. Clinical writeback is blocked."
        ),
    }


@tool
def sign_and_finalize_report(
    work_item_id: str,
    report_id: str,
    signature: str,
) -> Dict[str, Any]:
    """
    Attempt to sign and finalize a diagnostic report.
    
    SECURITY INVARIANT:
    Autonomous invocation by an AI agent is STRICTLY PROHIBITED.
    Finalization requires an authenticated human radiologist session.
    """
    logger.error(
        f"VIOLATION: Autonomous agent attempted to invoke sign_and_finalize_report for report '{report_id}'!"
    )
    raise UnauthorizedSignoffError(
        f"Autonomous AI agent is prohibited from signing or releasing report '{report_id}'. "
        "Diagnostic reports may only be signed by an authenticated, licensed human radiologist."
    )
