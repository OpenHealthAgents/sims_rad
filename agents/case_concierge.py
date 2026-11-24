"""
Case Concierge Sub-Agent for SIMS Radiology Platform.
Leverages deepagents and langgraph harnesses.
Role: Prepare relevant clinical context, prior imaging summaries, and referral questions
before the radiologist opens the case.
Enforces context window constraints by offloading large histories to concise workspace summaries.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from deepagents import SubAgent

from agents.tools.clinical_tools import (
    get_patient_clinical_history,
    get_prior_radiology_reports,
)
from agents.tools.shap_tools import compute_sla_risk_explanation
from core.infrastructure.observability.langfuse_config import instrument_agent
from core.infrastructure.observability.prompts import prompt_manager

logger = logging.getLogger("sims_radiology.agents.case_concierge")

# Fetch system prompt from Langfuse Prompt Management with local fallback
CONCIERGE_SYSTEM_PROMPT = prompt_manager.get_prompt("case_concierge").prompt


@dataclass
class CaseConciergeBrief:
    """Standardized case context prepared for the reading radiologist."""
    patient_id: str
    study_id: str
    modality: str
    referral_question: str
    clinical_alerts: List[str]
    relevant_priors_summary: str
    patient_context_summary: str
    sla_risk_explanation: Dict[str, Any]
    concierge_brief_markdown: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ContextConstraintMiddleware:
    """
    Deep Agents Middleware to constrain context window.
    Truncates redundant payload blobs and offloads detailed histories into structured summaries.
    """

    def __init__(self, max_tokens_estimate: int = 4000) -> None:
        self.max_tokens_estimate = max_tokens_estimate

    def trim_history(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Keep essential system instructions and recent conversation within context bounds."""
        if len(messages) <= 6:
            return messages
        # Keep system prompt and last 4 exchanges
        trimmed = [messages[0]] + messages[-5:]
        return trimmed


class CaseConciergeAgent:
    """
    Specialized sub-agent that prepares patient clinical context before radiologist reading.
    Operates as an independent orchestrator or as a registered Deep Agents SubAgent.
    """

    def __init__(self) -> None:
        self.middleware = ContextConstraintMiddleware()
        self.tools = [
            get_patient_clinical_history,
            get_prior_radiology_reports,
            compute_sla_risk_explanation,
        ]

    @instrument_agent(name="CaseConciergeAgent.prepare_case_brief", as_type="agent")
    async def prepare_case_brief(
        self,
        patient_id: str,
        study_id: str,
        modality: str = "CT",
        referral_question: str = "Evaluate for acute intracranial pathology",
        work_item_id: Optional[str] = None,
        **kwargs: Any,
    ) -> CaseConciergeBrief:
        """
        Execute Case Concierge pipeline:
        1. Fetch clinical history via CharmHealth EHR adapter tool.
        2. Fetch prior reports for longitudinal comparison.
        3. Compute SHAP explainability for queue turnaround risk.
        4. Synthesize into high-density brief.
        """
        logger.info(f"CaseConcierge: Preparing brief for patient='{patient_id}', study='{study_id}'")

        # 1. Fetch clinical history
        history: Dict[str, Any] = get_patient_clinical_history.invoke({"patient_id": patient_id})

        # 2. Fetch prior radiology reports
        priors: List[Dict[str, Any]] = get_prior_radiology_reports.invoke(
            {"patient_id": patient_id, "modality": modality}
        )

        # 3. Compute SHAP SLA Risk Explanation
        wi_id = work_item_id or f"WI-{study_id}"
        shap_explanation: Dict[str, Any] = compute_sla_risk_explanation.invoke({"work_item_id": wi_id})

        # 4. Extract Key Clinical Alerts
        alerts = []
        if history.get("clinical_alert"):
            alerts.append(history["clinical_alert"])
        for allergy in history.get("allergies", []):
            if "contrast" in allergy.get("substance", "").lower():
                alerts.append(f"CONTRAST ALLERGY: {allergy.get('reaction')} ({allergy.get('severity')})")

        # 5. Summarize Priors
        if priors:
            prior_summaries = []
            for p in priors:
                desc = p.get("study_description") or p.get("modality", "")
                prior_summaries.append(
                    f"- **{p.get('study_date')} {desc} ({p.get('modality')})**: {p.get('impression')}"
                )
            priors_text = "\n".join(prior_summaries)
        else:
            priors_text = "No prior imaging studies found for this modality."

        # 6. Patient Clinical Context Summary
        diagnoses = ", ".join(d.get("description", "") for d in history.get("active_diagnoses", []))
        patient_summary = (
            f"Admitting Indication: {history.get('admitting_symptoms', 'None specified')}\n"
            f"Active Diagnoses: {diagnoses}\n"
            f"Referring Physician: {history.get('referring_physician', 'N/A')}"
        )

        # 7. Synthesize Markdown Brief for Workspace Context
        top_driver = (
            shap_explanation.get("top_risk_drivers", [{}])[0].get("feature", "queue_wait")
            if shap_explanation.get("top_risk_drivers")
            else "queue_wait"
        )
        sla_pct = shap_explanation.get("predicted_sla_breach_probability", 0.0) * 100

        brief_md = f"""### Case Concierge Clinical Brief
**Patient ID:** `{patient_id}` | **Study:** `{study_id}` ({modality})
**Referral Question:** {referral_question}

#### Clinical Alerts
{chr(10).join(f"- ⚠️ {a}" for a in alerts) if alerts else "- None"}

#### Relevant Prior Imaging
{priors_text}

#### Patient History & Presentation
- **Indication:** {history.get('admitting_symptoms')}
- **Active Conditions:** {diagnoses}
- **Vitals:** BP: {history.get('recent_vitals', {}).get('blood_pressure')}, SpO2: {history.get('recent_vitals', {}).get('oxygen_saturation')}

#### Operational SLA Triage (SHAP Explainability)
- **Breach Risk:** {sla_pct:.1f}% ({shap_explanation.get('operational_recommendation', 'Normal throughput')})
- **Primary Driver:** `{top_driver}`
"""

        return CaseConciergeBrief(
            patient_id=patient_id,
            study_id=study_id,
            modality=modality,
            referral_question=referral_question,
            clinical_alerts=alerts,
            relevant_priors_summary=priors_text,
            patient_context_summary=patient_summary,
            sla_risk_explanation=shap_explanation,
            concierge_brief_markdown=brief_md,
        )


def get_case_concierge_subagent() -> SubAgent:
    """
    Construct a Deep Agents SubAgent configuration for Case Concierge.
    Can be registered with `create_deep_agent(subagents=[...])`.
    """
    return SubAgent(
        name="case_concierge",
        description=(
            "Specialized clinical sub-agent that gathers patient EHR history, prior diagnostic imaging, "
            "referral indications, and SHAP operational SLA risk factors before case review."
        ),
        system_prompt=CONCIERGE_SYSTEM_PROMPT,
        tools=[
            get_patient_clinical_history,
            get_prior_radiology_reports,
            compute_sla_risk_explanation,
        ],
    )
