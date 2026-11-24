"""
Safety & Guardrails Tests: NeMo Guardrails safety policies and critical detection.
"""
import pytest
from agents.guardrails.service import NemoGuardrailService


@pytest.mark.asyncio
async def test_guardrail_detects_critical_findings():
    service = NemoGuardrailService()
    findings = [
        {"label": "Acute Subdural Hemorrhage", "confidence": 0.94, "is_critical": False}
    ]
    is_safe, reasons = await service.verify_radiology_output(
        study_uid="1.2.3.4",
        clinical_text="Subdural hemorrhage noted.",
        findings=findings,
    )

    assert is_safe is True
    assert findings[0]["is_critical"] is True
    assert any("Critical finding flagged" in r for r in reasons)


@pytest.mark.asyncio
async def test_guardrail_rejects_low_confidence_hallucination():
    service = NemoGuardrailService()
    findings = [
        {"label": "Suspected cavernous angioma", "confidence": 0.25, "is_critical": False}
    ]
    is_safe, reasons = await service.verify_radiology_output(
        study_uid="1.2.3.4",
        clinical_text="Possible cavernous angioma.",
        findings=findings,
    )

    assert is_safe is False
    assert any("confidence threshold" in r for r in reasons)
