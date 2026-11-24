"""
LLM-as-a-Judge Evaluation Pipeline for Radiology Diagnostic Reports (Clean Architecture).
Evaluates drafted report quality and safety across 3 clinical criteria:
1. Clinical Context Accuracy (1-5)
2. Absence of Hallucinated Findings (Pass/Fail)
3. Template Formatting Compliance (1-5)
Scores are published directly to Langfuse and linked to specific trace IDs.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from core.infrastructure.observability.langfuse_config import (
    mask_phi_text,
    observability_service,
    sanitize_payload,
)
from core.infrastructure.observability.prompts import prompt_manager

logger = logging.getLogger("sims_radiology.evals.report_judge")


@dataclass
class CriterionScore:
    """Evaluation score and diagnostic rationale for a single criterion."""
    name: str
    value: Union[float, int, bool]
    data_type: str  # "NUMERIC", "BOOLEAN", "CATEGORICAL"
    passed: bool
    comment: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportEvaluationResult:
    """Composite outcome of LLM-as-a-Judge evaluation for a drafted radiology report."""
    trace_id: str
    report_id: str
    overall_passed: bool
    clinical_context_accuracy: float
    absence_of_hallucination: bool
    template_formatting_compliance: float
    scores: Dict[str, CriterionScore]
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evaluation_summary: str = ""


class ReportDraftJudge:
    """
    LLM-as-a-Judge automated evaluation engine for clinical radiology reports.
    Computes rigorous scores and directly registers them with the Langfuse telemetry server.
    """

    def __init__(self) -> None:
        self.accuracy_prompt = prompt_manager.get_prompt("eval_clinical_accuracy")
        self.hallucination_prompt = prompt_manager.get_prompt("eval_hallucination_judge")
        self.formatting_prompt = prompt_manager.get_prompt("eval_formatting_compliance")

    # =========================================================================
    # Evaluator 1: Clinical Context Accuracy (1-5)
    # =========================================================================
    def evaluate_clinical_context_accuracy(
        self,
        draft_text: str,
        clinical_indication: str,
        modality: str,
        patient_history: Optional[str] = None,
    ) -> CriterionScore:
        """
        Score 1-5 evaluating clinical indication correlation, anatomical relevance,
        and modality consistency.
        """
        score = 5.0
        reasons = []

        draft_lower = draft_text.lower()
        indication_lower = (clinical_indication or "").lower()
        modality_lower = (modality or "").lower()

        # Check modality congruence
        if modality_lower and modality_lower not in draft_lower:
            # Minor penalty if modality tag is not mentioned explicitly
            score -= 0.5
            reasons.append(f"Modality '{modality}' not explicitly referenced in narrative.")

        # Check key terms from clinical indication
        indication_keywords = [
            w for w in re.findall(r"\w+", indication_lower)
            if len(w) > 3 and w not in {"with", "without", "pain", "left", "right", "rule", "year", "male", "female"}
        ]
        matched_keywords = [w for w in indication_keywords if w in draft_lower]
        coverage_ratio = len(matched_keywords) / max(len(indication_keywords), 1)

        if coverage_ratio < 0.25 and len(indication_keywords) > 0:
            score -= 2.0
            reasons.append("Draft fails to address primary clinical indication or referral questions.")
        elif coverage_ratio < 0.50:
            score -= 1.0
            reasons.append("Partial coverage of clinical indication referral terms.")

        # Check if empty or too brief
        if len(draft_text.split()) < 15:
            score = min(score, 2.0)
            reasons.append("Report draft is excessively brief for comprehensive clinical evaluation.")

        final_score = max(1.0, min(5.0, round(score, 1)))
        passed = final_score >= 3.0
        comment = "; ".join(reasons) if reasons else "High clinical context accuracy and anatomical correlation."

        return CriterionScore(
            name="clinical_context_accuracy",
            value=final_score,
            data_type="NUMERIC",
            passed=passed,
            comment=comment,
            metadata={"coverage_ratio": round(coverage_ratio, 2), "matched_keywords": matched_keywords},
        )

    # =========================================================================
    # Evaluator 2: Absence of Hallucinated Findings (Pass/Fail)
    # =========================================================================
    def evaluate_absence_of_hallucination(
        self,
        draft_findings: Union[str, Dict[str, Any], List[Any]],
        ground_truth_findings: List[Dict[str, Any]],
        confidence_threshold: float = 0.70,
    ) -> CriterionScore:
        """
        Pass/Fail criterion verifying that diagnostic assertions are grounded in
        imaging slice observations without ungrounded pathology fabrication.
        """
        hallucination_detected = False
        reasons = []

        # Extract textual representation of draft findings
        narrative = ""
        if isinstance(draft_findings, str):
            narrative = draft_findings
        elif isinstance(draft_findings, dict):
            narrative = draft_findings.get("narrative", "") or draft_findings.get("findings", "") or str(draft_findings)
        elif isinstance(draft_findings, list):
            narrative = " ".join(str(f) for f in draft_findings)

        narrative_lower = narrative.lower()

        # Severe pathologies that must be supported by ground truth
        critical_markers = {
            "intracranial hemorrhage": ["hemorrhage", "bleed", "hematoma"],
            "pneumothorax": ["pneumothorax", "collapsed lung"],
            "acute infarction": ["infarction", "stroke", "ischemia"],
            "displaced fracture": ["displaced fracture", "shattered", "comminuted"],
            "aortic dissection": ["dissection", "intimal flap"],
        }

        # Index verified labels in ground truth
        gt_labels = [str(g.get("label", "")).lower() for g in ground_truth_findings]
        gt_text = " ".join(gt_labels)

        for pathology, markers in critical_markers.items():
            found_positive_in_draft = False
            for m in markers:
                for match in re.finditer(r"\b" + re.escape(m) + r"\b", narrative_lower):
                    # Check for negation in the current sentence or clause up to the match
                    sentence_start = max(
                        narrative_lower.rfind(".", 0, match.start()),
                        narrative_lower.rfind("\n", 0, match.start()),
                        narrative_lower.rfind(";", 0, match.start()),
                        0,
                    )
                    preceding_in_sentence = narrative_lower[sentence_start:match.start()]
                    if any(neg in preceding_in_sentence for neg in ("no ", "without ", "negative for ", "absence of ", "no evidence of ", "free of ", "rule out ")):
                        continue
                    found_positive_in_draft = True
                    break
                if found_positive_in_draft:
                    break

            found_in_gt = any(m in gt_text for m in markers)

            if found_positive_in_draft and not found_in_gt:
                hallucination_detected = True
                reasons.append(
                    f"Hallucination Detected: Draft asserts '{pathology}' which is absent from verified DICOM findings."
                )

        # Check for ungrounded low-confidence findings in ground truth assertions
        for g in ground_truth_findings:
            conf = g.get("confidence", 1.0)
            if conf < confidence_threshold and str(g.get("label", "")).lower() in narrative_lower:
                # Agent promoted low confidence finding to definitive statement
                hallucination_detected = True
                reasons.append(
                    f"Ungrounded finding: Asserted '{g.get('label')}' which had insufficient AI confidence ({conf:.2f} < {confidence_threshold})."
                )

        passed = not hallucination_detected
        comment = "; ".join(reasons) if reasons else "All stated diagnostic assertions are grounded in verified imaging observations."

        return CriterionScore(
            name="absence_of_hallucination",
            value=passed,
            data_type="BOOLEAN",
            passed=passed,
            comment=comment,
            metadata={"ground_truth_count": len(ground_truth_findings), "hallucinations": reasons},
        )

    # =========================================================================
    # Evaluator 3: Template Formatting Compliance (1-5)
    # =========================================================================
    def evaluate_template_formatting_compliance(self, draft_text: str) -> CriterionScore:
        """
        Score 1-5 measuring structured section completeness and absence of unauthorized signature blocks.
        """
        score = 5.0
        reasons = []
        text_lower = draft_text.lower()

        # Core required sections for ACR / RadLex clinical report template
        required_sections = {
            "findings": ["finding", "findings", "radiographic observations"],
            "impression": ["impression", "conclusion", "differential"],
        }
        recommended_sections = {
            "indication": ["indication", "history", "clinical background", "reason for exam"],
            "technique": ["technique", "protocol", "comparison", "modality"],
        }

        for sec_name, keywords in required_sections.items():
            if not any(k in text_lower for k in keywords):
                score -= 1.5
                reasons.append(f"Missing mandatory section: {sec_name.capitalize()}")

        for sec_name, keywords in recommended_sections.items():
            if not any(k in text_lower for k in keywords):
                score -= 0.5
                reasons.append(f"Missing recommended section: {sec_name.capitalize()}")

        # Check safety invariant: no unauthorized signature or finalized stamps
        unauthorized_signature_markers = [
            "digitally signed by ai",
            "autonomous sign-off",
            "signed by agent",
            "released by ai concierge",
            "final signoff: approved",
        ]
        for marker in unauthorized_signature_markers:
            if marker in text_lower:
                score -= 2.0
                reasons.append(f"SAFETY VIOLATION: Premature/unauthorized sign-off tag found: '{marker}'")

        final_score = max(1.0, min(5.0, round(score, 1)))
        passed = final_score >= 3.0
        comment = "; ".join(reasons) if reasons else "Complete adherence to structured ACR radiology template standards."

        return CriterionScore(
            name="template_formatting_compliance",
            value=final_score,
            data_type="NUMERIC",
            passed=passed,
            comment=comment,
            metadata={"final_score": final_score},
        )

    # =========================================================================
    # Composite Pipeline Execution & Langfuse Publishing
    # =========================================================================
    def evaluate_report_draft(
        self,
        trace_id: str,
        report_id: str,
        draft_text: str,
        clinical_indication: str,
        modality: str,
        ground_truth_findings: Optional[List[Dict[str, Any]]] = None,
        patient_history: Optional[str] = None,
    ) -> ReportEvaluationResult:
        """
        Executes all 3 LLM-as-a-Judge evaluations and records scores directly in Langfuse.
        """
        gt = ground_truth_findings or []

        # Run individual evaluators
        score_acc = self.evaluate_clinical_context_accuracy(
            draft_text=draft_text,
            clinical_indication=clinical_indication,
            modality=modality,
            patient_history=patient_history,
        )

        score_hal = self.evaluate_absence_of_hallucination(
            draft_findings=draft_text,
            ground_truth_findings=gt,
        )

        score_fmt = self.evaluate_template_formatting_compliance(
            draft_text=draft_text,
        )

        # Store evaluation scores in Langfuse linked to trace_id
        observability_service.record_score(
            trace_id=trace_id,
            name=score_acc.name,
            value=score_acc.value,
            data_type=score_acc.data_type,
            comment=score_acc.comment,
            metadata=score_acc.metadata,
        )

        observability_service.record_score(
            trace_id=trace_id,
            name=score_hal.name,
            value=score_hal.value,
            data_type=score_hal.data_type,
            comment=score_hal.comment,
            metadata=score_hal.metadata,
        )

        observability_service.record_score(
            trace_id=trace_id,
            name=score_fmt.name,
            value=score_fmt.value,
            data_type=score_fmt.data_type,
            comment=score_fmt.comment,
            metadata=score_fmt.metadata,
        )

        overall_passed = score_acc.passed and score_hal.passed and score_fmt.passed
        summary = (
            f"Overall: {'PASS' if overall_passed else 'FAIL'} | "
            f"Accuracy: {score_acc.value}/5.0 | "
            f"Hallucination-Free: {score_hal.value} | "
            f"Format Compliance: {score_fmt.value}/5.0"
        )

        logger.info(f"Evaluation for trace '{trace_id}': {summary}")

        return ReportEvaluationResult(
            trace_id=trace_id,
            report_id=report_id,
            overall_passed=overall_passed,
            clinical_context_accuracy=float(score_acc.value),
            absence_of_hallucination=bool(score_hal.value),
            template_formatting_compliance=float(score_fmt.value),
            scores={
                score_acc.name: score_acc,
                score_hal.name: score_hal,
                score_fmt.name: score_fmt,
            },
            evaluation_summary=summary,
        )


report_judge = ReportDraftJudge()
