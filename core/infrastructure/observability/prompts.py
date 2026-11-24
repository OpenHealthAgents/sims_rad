"""
Langfuse Prompt Management and Skill Registry with Local Failover (Clean Architecture).
Fetches enterprise system prompts for Case Concierge, Reporting Assistant, and LLM Judges
from the Langfuse Prompt Management API, with automatic local fallback guarantees.
"""
from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Optional
from core.infrastructure.observability.langfuse_config import observability_service

logger = logging.getLogger("sims_radiology.observability.prompts")

# =============================================================================
# Local Default System Prompts (Authoritative Fallback Definitions)
# =============================================================================

CASE_CONCIERGE_PROMPT_DEFAULT = """You are the Case Concierge AI Agent for the SIMS Radiology Operating Platform.
Your mission is to synthesize patient clinical history, prior diagnostic imaging reports,
and operational turnaround factors into an actionable, high-density case brief before the radiologist opens the study.

Clinical Directives:
1. Highlight clinical alerts (allergies, renal function, contrast contraindications).
2. Summarize relevant prior imaging studies of the same or related anatomical regions.
3. Incorporate SHAP operational explanation to alert the clinician to SLA turnaround risks.
4. Keep summaries concise to avoid cognitive overload and respect context window limits.
"""

REPORTING_ASSISTANT_PROMPT_DEFAULT = """You are the Structured Diagnostic Reporting Assistant for the SIMS Radiology Operating Platform.
Your mission is to draft clinical report findings and impressions adhering strictly to
radiological standards (e.g. RadLex, ACR guidelines).

CRITICAL SAFETY & GOVERNANCE INVARIANTS:
1. You generate preliminary, unsigned DRAFT versions only.
2. Under NO CIRCUMSTANCES may you sign, finalize, release, or apply digital signature hashes to reports.
3. Any mention of report sign-off requires human radiologist authentication and license verification.
4. State all radiographic observations clearly in 'Findings' and differential diagnosis in 'Impression'.
"""

ORCHESTRATOR_SYSTEM_PROMPT_DEFAULT = """You are the SIMS Radiology AI Orchestrator Agent.
You coordinate sub-agents (Case Concierge, DICOM extraction, SHAP Explainability, and Reporting Assistant)
to prepare cases, monitor operational SLA queues, and draft structured preliminary reports.

Safety Rules:
- Autonomous sign-off is strictly prohibited.
- Mask all PHI/PII.
- Respect deterministic clinical state machine transitions.
"""

EVAL_CLINICAL_ACCURACY_PROMPT_DEFAULT = """Evaluate the Clinical Context Accuracy of the drafted diagnostic report on a scale of 1 to 5:
1: Factually contradictory or completely mismatched with clinical indication and imaging modality.
2: Poor alignment; misses critical anatomical regions or primary referral questions.
3: Adequate; captures general region but lacks nuance or specific prior comparisons.
4: Strong; accurately addresses referral question and correctly incorporates historical findings.
5: Exemplary; comprehensive anatomical correlation, accurate differential, and complete clinical context.
"""

EVAL_HALLUCINATION_JUDGE_PROMPT_DEFAULT = """Determine if the drafted report contains ungrounded or hallucinated diagnostic assertions:
Evaluate whether every stated lesion, fracture, hemorrhage, or abnormality in 'Findings'
is directly grounded in the provided DICOM slice data and verified imaging observations.
Output: PASS if strictly grounded, FAIL if any fabricated finding is identified.
"""

EVAL_FORMATTING_COMPLIANCE_PROMPT_DEFAULT = """Evaluate Template Formatting Compliance on a scale of 1 to 5:
1: Unstructured free text lacking standard radiological headings.
2: Missing major sections (e.g., missing Impression or Technique).
3: Standard sections present but improper hierarchy or formatting.
4: Full adherence to structured sections: Indication, Technique, Findings, Impression.
5: Flawless adherence to template structure with clean RadLex/ACR standard nomenclature and zero premature sign-off tags.
"""

LOCAL_DEFAULTS_REGISTRY: Dict[str, str] = {
    "case_concierge": CASE_CONCIERGE_PROMPT_DEFAULT,
    "reporting_assistant": REPORTING_ASSISTANT_PROMPT_DEFAULT,
    "radiology_orchestrator": ORCHESTRATOR_SYSTEM_PROMPT_DEFAULT,
    "eval_clinical_accuracy": EVAL_CLINICAL_ACCURACY_PROMPT_DEFAULT,
    "eval_hallucination_judge": EVAL_HALLUCINATION_JUDGE_PROMPT_DEFAULT,
    "eval_formatting_compliance": EVAL_FORMATTING_COMPLIANCE_PROMPT_DEFAULT,
}


@dataclass
class PromptItem:
    """Standardized Prompt representation with compilation capabilities."""
    name: str
    prompt: str
    version: int = 1
    is_fallback: bool = True
    label: str = "production"
    labels: List[str] = field(default_factory=lambda: ["production"])

    def compile(self, **variables: Any) -> str:
        """
        Compile prompt template by substituting {{ variable }} placeholders.
        """
        compiled = self.prompt
        for key, val in variables.items():
            pattern = r"\{\{\s*" + re.escape(str(key)) + r"\s*\}\}"
            compiled = re.sub(pattern, str(val), compiled)
        return compiled


class PromptManager:
    """
    Manages prompt retrieval with Langfuse Prompt Management API and local fallback.
    """

    def __init__(self) -> None:
        self.registry = LOCAL_DEFAULTS_REGISTRY

    def get_prompt(
        self,
        name: str,
        version: Optional[int] = None,
        label: Optional[str] = None,
        fallback: Optional[str] = None,
    ) -> PromptItem:
        """
        Fetch prompt from Langfuse Prompt Management API.
        If Langfuse is unavailable or prompt is not found, seamlessly falls back to local defaults.
        """
        default_fallback = fallback or self.registry.get(name, f"System prompt for {name}")

        client = observability_service.client
        if client and observability_service.is_server_available():
            try:
                # Call official Langfuse get_prompt with zero retries and fast timeout for failover
                lf_prompt = client.get_prompt(
                    name=name,
                    version=version,
                    label=label,
                    fallback=default_fallback,
                    max_retries=0,
                    fetch_timeout_seconds=1,
                )
                if lf_prompt and hasattr(lf_prompt, "prompt"):
                    logger.info(f"Retrieved prompt '{name}' from Langfuse Prompt Management (v{getattr(lf_prompt, 'version', 1)}).")
                    return PromptItem(
                        name=name,
                        prompt=lf_prompt.prompt,
                        version=getattr(lf_prompt, "version", version or 1),
                        is_fallback=False,
                        label=label or "remote",
                    )
            except Exception as e:
                logger.warning(
                    f"Langfuse prompt retrieval for '{name}' failed ({e}). "
                    "Engaging local fallback prompt."
                )

        # Fallback path
        logger.debug(f"Using local fallback prompt for '{name}'.")
        return PromptItem(
            name=name,
            prompt=default_fallback,
            version=version or 1,
            is_fallback=True,
            label=label or "local_fallback",
        )

    def register_default_prompts(self) -> Dict[str, bool]:
        """
        Publish local default prompts to Langfuse Prompt Management if connected.
        """
        client = observability_service.client
        results = {}
        if not client or not observability_service.is_server_available():
            return {name: False for name in self.registry}

        for name, text in self.registry.items():
            try:
                client.create_prompt(
                    name=name,
                    prompt=text,
                    labels=["production", "default"],
                    tags=["sims_radiology", "clinical"],
                    commit_message="Initial default prompt registration",
                )
                results[name] = True
                logger.info(f"Registered prompt '{name}' in Langfuse.")
            except Exception as e:
                logger.warning(f"Could not register prompt '{name}' in Langfuse: {e}")
                results[name] = False
        return results


prompt_manager = PromptManager()
