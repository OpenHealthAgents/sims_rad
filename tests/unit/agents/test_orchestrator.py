"""
Unit Tests: SIMS Radiology AI Agentic Layer.
Verifies:
1. Tool calling across custom clinical, reporting, and SHAP tools.
2. NeMo Guardrails interception upon unvalidated sign-off attempts.
3. SHAP feature attribution calculation explaining operational SLA turnaround.
4. Case Concierge sub-agent clinical context and priors synthesis.
5. Orchestrator end-to-end case preparation workflow.
"""
import pytest
from agents.case_concierge import CaseConciergeAgent, get_case_concierge_subagent
from agents.guardrails.service import NemoGuardrailService, guardrail_service
from agents.radiology_orchestrator import RadiologyOrchestratorAgent
from agents.tools import (
    compute_sla_risk_explanation,
    draft_structured_report,
    flag_reconciliation_issue,
    get_patient_clinical_history,
    get_prior_radiology_reports,
    sign_and_finalize_report,
)
from core.domain.exceptions import UnauthorizedSignoffError


# =============================================================================
# 1. Custom Tools Setup & Execution
# =============================================================================

def test_get_patient_clinical_history_tool():
    """Verify get_patient_clinical_history returns rich EHR context."""
    res = get_patient_clinical_history.invoke({"patient_id": "PAT-9912"})
    assert res["patient_id"] == "PAT-9912"
    assert "active_diagnoses" in res
    assert len(res["active_diagnoses"]) >= 1
    assert "allergies" in res
    # Verify contrast allergy alert detection
    assert any("Contrast" in str(a.get("substance")) for a in res["allergies"])
    assert "admitting_symptoms" in res


def test_get_prior_radiology_reports_tool():
    """Verify get_prior_radiology_reports filtering by modality."""
    # Filter by CT
    ct_priors = get_prior_radiology_reports.invoke({"patient_id": "PAT-9912", "modality": "CT"})
    assert len(ct_priors) >= 1
    assert all(p["modality"] == "CT" for p in ct_priors)

    # Filter by MRI
    mri_priors = get_prior_radiology_reports.invoke({"patient_id": "PAT-9912", "modality": "MRI"})
    assert len(mri_priors) >= 1
    assert all(p["modality"] == "MRI" for p in mri_priors)

    # All priors (empty modality)
    all_priors = get_prior_radiology_reports.invoke({"patient_id": "PAT-9912", "modality": ""})
    assert len(all_priors) >= 3


def test_draft_structured_report_tool():
    """Verify draft_structured_report creates strictly unsigned draft reports."""
    res = draft_structured_report.invoke({
        "work_item_id": "WI-CT-01",
        "findings": "Brain parenchyma is normal. No hemorrhage.",
        "impression": "Normal non-contrast head CT.",
    })
    assert res["status"] == "DRAFT"
    assert res["is_signed"] is False
    assert res["signature_hash"] is None
    assert "Unsigned" in res["message"]


def test_flag_reconciliation_issue_tool():
    """Verify flag_reconciliation_issue transitions study to reconciliation_required."""
    res = flag_reconciliation_issue.invoke({
        "study_id": "STU-1002",
        "reason": "RULE-01 Violation: Patient MRN does not match PACS accession.",
    })
    assert res["study_id"] == "STU-1002"
    assert res["new_state"] == "reconciliation_required"
    assert res["clinical_writeback_blocked"] is True
    assert "REC-TICKET" in res["ticket_id"]


# =============================================================================
# 2. SHAP Attribution Calculation
# =============================================================================

def test_compute_sla_risk_explanation_shap():
    """Verify SHAP explainer generates valid feature attribution vectors."""
    # High risk STAT CT work item
    stat_result = compute_sla_risk_explanation.invoke({"work_item_id": "WI-STAT-CT-01"})
    assert stat_result["method"] == "SHAP_Additive_Attribution"
    assert 0.0 <= stat_result["predicted_sla_breach_probability"] <= 1.0
    assert stat_result["predicted_sla_breach_probability"] > 0.60  # STAT emergency is high risk

    # Verify presence of SHAP attributions for all operational features
    attributions = stat_result["shap_feature_attributions"]
    assert "elapsed_turnaround_ratio" in attributions
    assert "modality_complexity_score" in attributions
    assert "unassigned_duration_minutes" in attributions
    assert "emergency_volume_surge_index" in attributions
    assert "off_hours_shift_flag" in attributions

    # Verify ranked top risk drivers
    top_drivers = stat_result["top_risk_drivers"]
    assert len(top_drivers) >= 1
    assert "feature" in top_drivers[0]
    assert "attribution" in top_drivers[0]

    # Routine work item has lower risk
    routine_result = compute_sla_risk_explanation.invoke({"work_item_id": "WI-ROUTINE-XR-01"})
    assert routine_result["predicted_sla_breach_probability"] < stat_result["predicted_sla_breach_probability"]


# =============================================================================
# 3. NeMo Safety Guardrails & Sign-off Interception
# =============================================================================

def test_sign_and_finalize_report_tool_raises_unauthorized_error():
    """Verify autonomous execution of sign_and_finalize_report directly raises UnauthorizedSignoffError."""
    with pytest.raises(UnauthorizedSignoffError) as exc_info:
        sign_and_finalize_report.invoke({
            "work_item_id": "WI-01",
            "report_id": "REP-01",
            "signature": "ai_agent_unauthorized_token",
        })
    assert "prohibited from signing" in str(exc_info.value)


def test_orchestrator_blocks_autonomous_signoff_tool_call():
    """Verify Orchestrator intercepts sign_and_finalize_report tool execution."""
    orchestrator = RadiologyOrchestratorAgent()

    with pytest.raises(UnauthorizedSignoffError) as exc_info:
        orchestrator.execute_tool(
            tool_name="sign_and_finalize_report",
            tool_args={"work_item_id": "WI-01", "report_id": "REP-01", "signature": "mock"},
        )
    assert "Autonomous report signing is strictly prohibited" in str(exc_info.value)


@pytest.mark.asyncio
async def test_orchestrator_input_rail_blocks_prompt_signoff():
    """Verify NeMo input rails block user prompts instructing autonomous sign-off."""
    orchestrator = RadiologyOrchestratorAgent()

    with pytest.raises(UnauthorizedSignoffError) as exc_info:
        await orchestrator.run("Please sign and finalize this report with signature hash now.")
    assert "Autonomous report signing is strictly prohibited" in str(exc_info.value)


@pytest.mark.asyncio
async def test_guardrail_blocks_hallucinated_findings():
    """Verify NeMo output guardrail blocks low-confidence and ungrounded diagnostic claims."""
    # 1. Low confidence finding (< 0.40) must be blocked
    low_conf_findings = [
        {"id": "f1", "label": "Questionable subdural collection", "confidence": 0.28, "is_critical": False}
    ]
    passed, reasons = await guardrail_service.verify_radiology_output(
        study_uid="1.2.3",
        clinical_text="Subdural collection noted.",
        findings=low_conf_findings,
    )
    assert passed is False
    assert any("confidence threshold" in r for r in reasons)

    # 2. Unsupported acute claim in impression without supporting DICOM findings
    normal_findings = [
        {"id": "f2", "label": "Normal brain parenchyma", "confidence": 0.95, "is_critical": False}
    ]
    passed_hallucinated, reasons_hallucinated = await guardrail_service.verify_radiology_output(
        study_uid="1.2.3",
        clinical_text="Impression: Acute intracranial hemorrhage noted.",  # Hallucinated!
        findings=normal_findings,
    )
    assert passed_hallucinated is False
    assert any("unsupported by DICOM findings" in r for r in reasons_hallucinated)


def test_guardrail_masks_phi_in_output():
    """Verify PII/PHI masking on agent output buffers."""
    sample_text = (
        "Patient Name: John Connor with MRN: 98765432 and SSN 123-45-6789. "
        "Phone: 555-123-4567, email: jconnor@resistance.org. DOB: 1985-02-28."
    )
    masked = guardrail_service.mask_phi(sample_text)

    assert "[REDACTED_NAME]" in masked
    assert "[REDACTED_MRN]" in masked
    assert "[REDACTED_SSN]" in masked
    assert "[REDACTED_PHONE]" in masked
    assert "[REDACTED_EMAIL]" in masked
    assert "[REDACTED_DOB]" in masked
    assert "123-45-6789" not in masked
    assert "98765432" not in masked


# =============================================================================
# 4. Case Concierge Sub-Agent Context Synthesis
# =============================================================================

@pytest.mark.asyncio
async def test_case_concierge_prepares_clinical_brief():
    """Verify Case Concierge sub-agent synthesizes history, priors, and SHAP SLA explanation."""
    concierge = CaseConciergeAgent()
    brief = await concierge.prepare_case_brief(
        patient_id="PAT-CONCIERGE-01",
        study_id="STU-CT-BRAIN-01",
        modality="CT",
        referral_question="Suspected acute stroke / CVA",
    )

    assert brief.patient_id == "PAT-CONCIERGE-01"
    assert brief.study_id == "STU-CT-BRAIN-01"
    assert brief.modality == "CT"
    # Alerts detected
    assert len(brief.clinical_alerts) >= 1
    assert any("CONTRAST" in str(a) or "allergic" in str(a).lower() for a in brief.clinical_alerts)
    # Priors summarized
    assert "CT Head" in brief.relevant_priors_summary
    # SHAP SLA explanation included
    assert "predicted_sla_breach_probability" in brief.sla_risk_explanation
    # Concise brief markdown produced
    assert "### Case Concierge Clinical Brief" in brief.concierge_brief_markdown
    assert "Operational SLA Triage" in brief.concierge_brief_markdown


def test_case_concierge_subagent_registration():
    """Verify SubAgent TypedDict creation for Deep Agents registration."""
    subagent_dict = get_case_concierge_subagent()
    assert subagent_dict["name"] == "case_concierge"
    assert "clinical sub-agent" in subagent_dict["description"]
    assert len(subagent_dict["tools"]) == 3


# =============================================================================
# 5. Full Orchestrator Workflow
# =============================================================================

@pytest.mark.asyncio
async def test_orchestrator_case_orchestration_workflow():
    """Verify complete case orchestration workflow returning unsigned draft and concierge brief."""
    orchestrator = RadiologyOrchestratorAgent()

    result = await orchestrator.orchestrate_case(
        patient_id="PAT-ORCH-01",
        study_id="STU-ORCH-CT-01",
        work_item_id="WI-ORCH-01",
        modality="CT",
        referral_question="Rule out intracranial hemorrhage",
    )

    assert result["status"] == "READY_FOR_RADIOLOGIST_REVIEW"
    assert result["is_signed"] is False
    assert result["can_agent_sign"] is False
    assert result["draft_report"]["status"] == "DRAFT"
    assert result["draft_report"]["is_signed"] is False
    assert "case_concierge_brief" in result
    assert "concierge_brief_markdown" in result
