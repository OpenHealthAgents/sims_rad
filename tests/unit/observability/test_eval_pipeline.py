"""
Unit Tests: LLM-as-a-Judge Evaluation Pipeline for Radiology Reports.
Tests criteria:
1. Clinical Context Accuracy (1-5)
2. Absence of Hallucinated Findings (Pass/Fail)
3. Template Formatting Compliance (1-5)
And verifies scores are linked to Langfuse trace IDs.
"""
import uuid
import pytest

from agents.evals.report_evaluator import ReportDraftJudge, report_judge
from core.infrastructure.observability.langfuse_config import (
    RecordedTrace,
    in_mem_trace_store,
)


@pytest.fixture(autouse=True)
def clean_trace_store():
    in_mem_trace_store.clear()
    yield
    in_mem_trace_store.clear()


def test_evaluator_clinical_context_accuracy_high_score():
    """Verify high score (4-5) when draft report aligns with indication and modality."""
    judge = ReportDraftJudge()
    draft = (
        "EXAMINATION: CT Head without contrast.\n"
        "CLINICAL INDICATION: 45-year-old male with acute severe headache and altered mental status.\n"
        "TECHNIQUE: Axial non-contrast computed tomography images of the brain.\n"
        "FINDINGS: Symmetrical ventricles without hydrocephalus. No midline shift or acute intracranial hemorrhage.\n"
        "IMPRESSION: No acute intracranial abnormality to explain acute headache."
    )
    score = judge.evaluate_clinical_context_accuracy(
        draft_text=draft,
        clinical_indication="acute severe headache altered mental status",
        modality="CT",
    )

    assert score.passed is True
    assert score.value >= 4.0
    assert score.data_type == "NUMERIC"
    assert "accuracy" in score.comment.lower()


def test_evaluator_clinical_context_accuracy_penalizes_omission():
    """Verify lower score when draft misses clinical indication and referral questions."""
    judge = ReportDraftJudge()
    draft = "Scan looks fine. Normal bones. No problems seen."

    score = judge.evaluate_clinical_context_accuracy(
        draft_text=draft,
        clinical_indication="Evaluate for pulmonary embolism and acute chest pain",
        modality="CT",
    )

    assert score.value < 3.0
    assert score.passed is False
    assert "fails to address" in score.comment.lower() or "brief" in score.comment.lower()


def test_evaluator_absence_of_hallucination_passes_grounded_findings():
    """Verify PASS when findings are grounded in verified DICOM observations."""
    judge = ReportDraftJudge()
    ground_truth = [
        {"label": "Subdural Hematoma", "confidence": 0.94, "slice_index": 18},
        {"label": "Mild Mass Effect", "confidence": 0.88, "slice_index": 19},
    ]
    draft = (
        "FINDINGS: A crescentic subdural hematoma is identified along the left cerebral convexity "
        "with mild mass effect and effacement of adjacent sulci. No midline shift.\n"
        "IMPRESSION: Left convex subdural hematoma."
    )

    score = judge.evaluate_absence_of_hallucination(
        draft_findings=draft,
        ground_truth_findings=ground_truth,
    )

    assert score.passed is True
    assert score.value is True
    assert score.data_type == "BOOLEAN"
    assert "grounded" in score.comment.lower()


def test_evaluator_absence_of_hallucination_fails_fabricated_pathology():
    """Verify FAIL when draft asserts severe pathologies not present in ground truth."""
    judge = ReportDraftJudge()
    ground_truth = [
        {"label": "Chronic Microvascular Ischemia", "confidence": 0.91},
    ]
    # Draft fabricates an acute hemorrhage
    draft = (
        "FINDINGS: Large acute intracranial hemorrhage observed in left temporal lobe with "
        "significant surrounding edema.\n"
        "IMPRESSION: Critical acute intracranial hemorrhage."
    )

    score = judge.evaluate_absence_of_hallucination(
        draft_findings=draft,
        ground_truth_findings=ground_truth,
    )

    assert score.passed is False
    assert score.value is False
    assert "Hallucination Detected" in score.comment


def test_evaluator_template_formatting_compliance_full_score():
    """Verify 5/5 score when all standard sections (Indication, Technique, Findings, Impression) are present."""
    judge = ReportDraftJudge()
    draft = (
        "CLINICAL INDICATION: Rule out acute stroke.\n"
        "TECHNIQUE: MRI Brain DWI, FLAIR, T1, T2.\n"
        "FINDINGS: Normal brain parenchyma. No restricted diffusion or acute ischemia.\n"
        "IMPRESSION: Negative for acute territorial infarction."
    )

    score = judge.evaluate_template_formatting_compliance(draft_text=draft)
    assert score.passed is True
    assert score.value == 5.0
    assert "complete adherence" in score.comment.lower()


def test_evaluator_template_formatting_compliance_penalizes_unauthorized_signoff():
    """Verify safety penalty when agent draft contains premature unauthorized sign-off tag."""
    judge = ReportDraftJudge()
    draft = (
        "CLINICAL INDICATION: Headache.\n"
        "TECHNIQUE: CT Head.\n"
        "FINDINGS: Clear sinuses, normal brain.\n"
        "IMPRESSION: Normal scan.\n"
        "Digitally signed by AI Concierge Agent."
    )

    score = judge.evaluate_template_formatting_compliance(draft_text=draft)
    assert score.value <= 3.0
    assert "SAFETY VIOLATION" in score.comment


def test_composite_evaluation_records_scores_linked_to_trace_id():
    """
    Test end-to-end composite evaluation pipeline:
    Verifies that all 3 criteria are evaluated and scores are linked to the specific Langfuse trace ID.
    """
    trace_id = f"trc-eval-{uuid.uuid4().hex[:8]}"

    # Seed trace in in_mem_trace_store
    dummy_trace = RecordedTrace(
        trace_id=trace_id,
        name="DiagnosticReportPipeline",
        user_id="rad_user_1",
        session_id="ses-123",
        observation_type="agent",
        inputs={"indication": "Headache"},
        outputs={"draft": "Draft text"},
        metadata={"modality": "CT"},
        shap_attribution_scores={"surge": 0.2},
        model="gemini-1.5-pro",
        cost_usd=0.0001,
        latency_ms=250.0,
        guardrail_verified=True,
    )
    in_mem_trace_store.record(dummy_trace)

    draft_report = (
        "CLINICAL INDICATION: Acute right-sided weakness, rule out stroke.\n"
        "TECHNIQUE: Non-contrast head CT.\n"
        "FINDINGS: Normal gray-white differentiation. No acute intracranial hemorrhage or territorial infarction.\n"
        "IMPRESSION: No acute intracranial process."
    )

    result = report_judge.evaluate_report_draft(
        trace_id=trace_id,
        report_id="REP-001",
        draft_text=draft_report,
        clinical_indication="acute right-sided weakness rule out stroke",
        modality="CT",
        ground_truth_findings=[],
    )

    assert result.trace_id == trace_id
    assert result.overall_passed is True
    assert result.clinical_context_accuracy >= 4.0
    assert result.absence_of_hallucination is True
    assert result.template_formatting_compliance >= 4.0

    # Verify scores are registered under trace_id in telemetry store
    recorded_trace = in_mem_trace_store.get(trace_id)
    assert recorded_trace is not None
    assert "clinical_context_accuracy" in recorded_trace.scores
    assert "absence_of_hallucination" in recorded_trace.scores
    assert "template_formatting_compliance" in recorded_trace.scores

    assert recorded_trace.scores["clinical_context_accuracy"]["value"] >= 4.0
    assert recorded_trace.scores["absence_of_hallucination"]["value"] is True
    assert recorded_trace.scores["template_formatting_compliance"]["value"] >= 4.0
