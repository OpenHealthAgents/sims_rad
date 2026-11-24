"""
Unit Tests: Langfuse AI Observability, Tracing, Context Propagation,
PHI/PII Sanitization, and Prompt Management with Local Failover.
"""
from datetime import datetime, timezone
import json
import uuid
import pytest

from agents.case_concierge import CaseConciergeAgent
from agents.radiology_orchestrator import RadiologyOrchestratorAgent
from core.domain.entities.study import Modality, RadiologyStudy
from core.infrastructure.observability.langfuse_config import (
    RecordedTrace,
    in_mem_trace_store,
    instrument_agent,
    mask_phi_text,
    observability_service,
    sanitize_payload,
)
from core.infrastructure.observability.prompts import (
    CASE_CONCIERGE_PROMPT_DEFAULT,
    REPORTING_ASSISTANT_PROMPT_DEFAULT,
    PromptItem,
    prompt_manager,
)


@pytest.fixture(autouse=True)
def clean_trace_store():
    """Clear in-memory trace store before each test."""
    in_mem_trace_store.clear()
    yield
    in_mem_trace_store.clear()


# =============================================================================
# 1. PHI / PII Masking and Sanitization Invariants
# =============================================================================

def test_phi_text_masking_replaces_names_dobs_and_identifiers():
    """Ensure regex pattern rules strictly mask patient names and DOBs."""
    sample_text = (
        "Patient Name: Jonathanathan Smithers, DOB: 1980-05-15, SSN: 123-45-6789. "
        "Clinical Indication: Head trauma. Contact: 555-123-4567, email: jsmith@example.com."
    )
    masked = mask_phi_text(sample_text)

    assert "Jonathanathan Smithers" not in masked
    assert "[REDACTED_NAME]" in masked
    assert "1980-05-15" not in masked
    assert "[REDACTED_DOB]" in masked
    assert "123-45-6789" not in masked
    assert "[REDACTED_SSN]" in masked
    assert "555-123-4567" not in masked
    assert "[REDACTED_PHONE]" in masked
    assert "jsmith@example.com" not in masked
    assert "[REDACTED_EMAIL]" in masked


def test_sanitize_payload_deep_scrubbing_dictionaries_and_lists():
    """Verify deep recursive scrubbing eliminates sensitive dictionary keys and values."""
    payload = {
        "study_id": "STU-1001",
        "modality": "CT",
        "patient": {
            "first_name": "Eleanor",
            "last_name": "Rigby",
            "dob": "1940-10-09",
            "medical_history": "Patient Name: Eleanor Rigby has hypertension, born: 1940-10-09.",
        },
        "findings_list": [
            "Normal scan for Patient Name: Eleanor Rigby",
            {"reviewer": "Dr. House", "patient_name": "Eleanor Rigby"},
        ],
    }

    sanitized = sanitize_payload(payload)

    # Dictionary keys scrubbed
    assert sanitized["patient"]["first_name"] == "[REDACTED_PHI]"
    assert sanitized["patient"]["last_name"] == "[REDACTED_PHI]"
    assert sanitized["patient"]["dob"] == "[REDACTED_PHI]"
    assert sanitized["findings_list"][1]["patient_name"] == "[REDACTED_PHI]"

    # Text inside nested fields scrubbed
    assert "Eleanor Rigby" not in str(sanitized)
    assert "[REDACTED_NAME]" in sanitized["patient"]["medical_history"]
    assert "[REDACTED_DOB]" in sanitized["patient"]["medical_history"]


# =============================================================================
# 2. Agent Tracing, Context Propagation, Latency, and Costs
# =============================================================================

@pytest.mark.asyncio
async def test_instrument_agent_records_trace_with_metadata_and_shap():
    """Verify @instrument_agent captures execution, latency, model cost, and SHAP vectors."""
    custom_trace_id = f"trc-{uuid.uuid4().hex[:12]}"
    user_id = "rad_specialist_01"
    session_id = f"ses-{uuid.uuid4().hex[:8]}"
    shap_scores = {
        "elapsed_turnaround_ratio": 0.45,
        "modality_complexity_score": 0.25,
        "unassigned_duration_minutes": 0.15,
        "emergency_volume_surge_index": 0.10,
        "off_hours_shift_flag": 0.05,
    }

    @instrument_agent(name="TestDiagnosticSubAgent", as_type="agent")
    async def sample_diagnostic_node(**kwargs):
        return {
            "finding": "Subtle cortical fissure asymmetry",
            "confidence": 0.92,
            "shap_attribution": shap_scores,
        }

    result = await sample_diagnostic_node(
        trace_id=custom_trace_id,
        user_id=user_id,
        session_id=session_id,
        shap_attribution_scores=shap_scores,
        metadata={"modality": "MRI", "work_item_id": "WI-999"},
    )

    assert result["finding"] == "Subtle cortical fissure asymmetry"

    # Verify recorded trace in telemetry store
    trace: RecordedTrace = in_mem_trace_store.get(custom_trace_id)
    assert trace is not None
    assert trace.trace_id == custom_trace_id
    assert trace.name == "TestDiagnosticSubAgent"
    assert trace.user_id == user_id
    assert trace.session_id == session_id
    assert trace.observation_type == "agent"
    assert trace.latency_ms > 0.0
    assert trace.cost_usd >= 0.0
    assert trace.guardrail_verified is True
    assert trace.shap_attribution_scores == shap_scores
    assert trace.metadata["modality"] == "MRI"
    assert trace.metadata["work_item_id"] == "WI-999"


@pytest.mark.asyncio
async def test_case_concierge_agent_tracing_and_phi_sanitization():
    """Ensure CaseConciergeAgent execution records trace while masking any PHI in brief."""
    concierge = CaseConciergeAgent()
    trace_id = f"trc-concierge-{uuid.uuid4().hex[:8]}"

    # Execute concierge brief preparation
    brief = await concierge.prepare_case_brief(
        patient_id="PAT-SIMS-001",
        study_id="STU-BRAIN-01",
        modality="CT",
        referral_question="Patient Name: Michael Scott presenting with sudden cephalalgia, DOB: 1965-03-15",
        work_item_id="WI-STAT-01",
        trace_id=trace_id,
        user_id="dr_pam_beesly",
    )

    assert brief.patient_id == "PAT-SIMS-001"
    assert "concierge_brief_markdown" in dir(brief)

    # Check trace record in telemetry audit store
    trace = in_mem_trace_store.get(trace_id)
    assert trace is not None
    assert trace.name == "CaseConciergeAgent.prepare_case_brief"
    assert trace.user_id == "dr_pam_beesly"

    # PHI verification: raw patient name and DOB must NOT be in inputs
    raw_inputs_str = json.dumps(trace.inputs)
    assert "Michael Scott" not in raw_inputs_str
    assert "1965-03-15" not in raw_inputs_str
    assert "[REDACTED_NAME]" in raw_inputs_str
    assert "[REDACTED_DOB]" in raw_inputs_str


@pytest.mark.asyncio
async def test_radiology_orchestrator_agent_tracing():
    """Ensure RadiologyOrchestratorAgent registers traces with guardrail decisions."""
    orchestrator = RadiologyOrchestratorAgent()
    trace_id = f"trc-orch-{uuid.uuid4().hex[:8]}"

    case_packet = await orchestrator.orchestrate_case(
        patient_id="PAT-SIMS-404",
        study_id="STU-MRI-02",
        work_item_id="WI-MRI-02",
        modality="MRI",
        referral_question="Suspected multiple sclerosis flare",
        preliminary_findings="Multiple hyperintense periventricular white matter lesions.",
        preliminary_impression="Findings consistent with demyelinating disease.",
        trace_id=trace_id,
        user_id="dr_gregory_house",
    )

    assert case_packet["status"] == "READY_FOR_RADIOLOGIST_REVIEW"
    assert case_packet["draft_report"]["status"] == "DRAFT"
    assert case_packet["draft_report"]["is_signed"] is False  # Invariant

    # Check trace
    trace = in_mem_trace_store.get(trace_id)
    assert trace is not None
    assert trace.name == "RadiologyOrchestratorAgent.orchestrate_case"
    assert trace.guardrail_verified is True
    assert trace.user_id == "dr_gregory_house"


# =============================================================================
# 3. Prompt Management with Local Failover Guarantees
# =============================================================================

def test_prompt_manager_fetches_default_prompts_with_fallback():
    """Verify PromptManager retrieves system prompts with version and fallback metadata."""
    concierge_p = prompt_manager.get_prompt("case_concierge")
    assert concierge_p.name == "case_concierge"
    assert "Case Concierge" in concierge_p.prompt
    assert concierge_p.is_fallback is True
    assert concierge_p.version >= 1

    reporting_p = prompt_manager.get_prompt("reporting_assistant")
    assert reporting_p.name == "reporting_assistant"
    assert "CRITICAL SAFETY & GOVERNANCE INVARIANTS" in reporting_p.prompt
    assert reporting_p.version >= 1


def test_prompt_template_compilation():
    """Test variable substitution in PromptItem.compile()."""
    template = PromptItem(
        name="custom_template",
        prompt="Review study {{ study_id }} for patient {{ patient_id }} with modality {{ modality }}.",
        version=2,
    )
    compiled = template.compile(study_id="STU-001", patient_id="PAT-999", modality="CT")
    assert compiled == "Review study STU-001 for patient PAT-999 with modality CT."
