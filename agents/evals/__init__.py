"""
Evaluation Package for SIMS Radiology AI Agents.
Provides automated LLM-as-a-Judge evaluations for diagnostic reports.
"""
from agents.evals.report_evaluator import (
    CriterionScore,
    ReportDraftJudge,
    ReportEvaluationResult,
    report_judge,
)

__all__ = [
    "CriterionScore",
    "ReportEvaluationResult",
    "ReportDraftJudge",
    "report_judge",
]
