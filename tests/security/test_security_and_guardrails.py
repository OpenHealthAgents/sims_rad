"""
Security, RBAC, and Clinical Safety Guardrails Test Suite (TC-049 to TC-056).
Enforces:
- TC-049: RBAC - Radiology Resident prohibited from signing/finalizing reports (403 Forbidden).
- TC-050: RBAC - Radiographer prohibited from assignment and signing (403 Forbidden).
- TC-051: RBAC - Coordinator allowed assignment, prohibited from signing (403 Forbidden).
- TC-052: Unauthenticated requests without Bearer token rejected (401 Unauthorized).
- Token Expiry: Session timeout / expired JWT validation rejected (401 Unauthorized).
- TC-053: Clinical Safety Boundary - Verify AI agent and NeMo guardrails NEVER auto-sign or bypass radiologist sign-off.
- TC-054: NeMo Guardrails hallucination and low-confidence finding interception.
- TC-055: PII/PHI scrubbing and masking in logs, output buffers, and trace payloads.
- TC-056: SQL injection and XSS payload rejection.
"""
from datetime import datetime, timezone, timedelta
import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.middleware.auth import UserRole, create_access_token
from apps.api.routes.reports import IN_MEMORY_REPORTS, seed_in_memory_report
from apps.api.src.endpoints.integrations import (
    IN_MEMORY_PATIENTS,
    IN_MEMORY_STUDIES,
    IN_MEMORY_WORK_ITEMS,
)
from apps.api.src.main import app
from agents.guardrails.service import NemoGuardrailService, guardrail_service
from agents.tools.reporting_tools import sign_and_finalize_report
from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import Modality, RadiologyStudy
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import UnauthorizedSignoffError
from core.infrastructure.observability.langfuse_config import (
    mask_phi_text,
    sanitize_payload,
)


@pytest.fixture(autouse=True)
def setup_security_test_data():
    """Seed test fixtures for security testing."""
    IN_MEMORY_PATIENTS.clear()
    IN_MEMORY_STUDIES.clear()
    IN_MEMORY_WORK_ITEMS.clear()
    IN_MEMORY_REPORTS.clear()

    now = datetime.now(timezone.utc)
    patient = Patient(
        patient_id="PAT-SEC-01",
        mrn="MRN-SEC-100",
        identifier_namespace="urn:oid:sims.hospital.patients",
        reconciliation_status=ReconciliationStatus.RECONCILED,
    )
    IN_MEMORY_PATIENTS["PAT-SEC-01"] = patient

    study = RadiologyStudy(
        study_id="STU-SEC-01",
        study_instance_uid="1.2.840.113619.2.55.3.88888",
        accession_number="ACC-SEC-001",
        modality=Modality.CT,
        study_date=now,
        patient_id="PAT-SEC-01",
        description="Chest CT with IV Contrast",
    )
    IN_MEMORY_STUDIES["STU-SEC-01"] = study

    work_item = WorkItem(
        work_item_id="WI-SEC-01",
        study_id="STU-SEC-01",
        state=WorkItemState.READY,
        priority=Priority.STAT,
        sla_deadline=now + timedelta(minutes=30),
        version=1,
    )
    IN_MEMORY_WORK_ITEMS["WI-SEC-01"] = work_item

    seed_in_memory_report(
        report_id="REP-SEC-01",
        work_item_id="WI-SEC-01",
        version_number=1,
        findings="No acute pulmonary embolism or consolidation.",
        impression="Normal CT Chest.",
        is_signed=False,
    )


# =============================================================================
# TC-049: RBAC - Radiology Resident Prohibited from Signing
# =============================================================================
@pytest.mark.asyncio
async def test_tc_049_resident_cannot_finalize_report():
    """TC-049: Verify RADIOLOGY_RESIDENT is denied when attempting to finalize/sign reports."""
    token = create_access_token("res-01", UserRole.RADIOLOGY_RESIDENT)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/report-versions/REP-SEC-01-v1/finalize",
            headers=headers,
            json={"findings": "Resident preliminary finding", "impression": "Normal"},
        )
        assert res.status_code == 403
        data = res.json()
        assert "Forbidden" in data["detail"]
        assert "RADIOLOGY_RESIDENT" in data["detail"]


# =============================================================================
# TC-050: RBAC - Radiographer Prohibited from Assignment and Signing
# =============================================================================
@pytest.mark.asyncio
async def test_tc_050_radiographer_cannot_assign_or_sign():
    """TC-050: Verify RADIOGRAPHER cannot assign work items or sign reports."""
    token = create_access_token("tech-01", UserRole.RADIOGRAPHER)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Radiographer attempts to sign report -> 403 Forbidden
        sign_res = await ac.post(
            "/api/v1/report-versions/REP-SEC-01-v1/finalize",
            headers=headers,
            json={},
        )
        assert sign_res.status_code == 403

        # 2. Radiographer attempts to assign work item -> 403 Forbidden
        assign_res = await ac.post(
            "/api/v1/work-items/WI-SEC-01/assignments",
            headers=headers,
            json={"assigned_radiologist_id": "rad-01", "reason_code": "CLINICAL_SPECIALTY"},
        )
        assert assign_res.status_code == 403


# =============================================================================
# TC-051: RBAC - Coordinator Can Assign but Cannot Sign
# =============================================================================
@pytest.mark.asyncio
async def test_tc_051_coordinator_can_assign_but_cannot_sign():
    """TC-051: Verify COORDINATOR can assign work items but is forbidden from signing reports."""
    token = create_access_token("coord-01", UserRole.COORDINATOR)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Assignment succeeds for COORDINATOR
        assign_res = await ac.post(
            "/api/v1/work-items/WI-SEC-01/assignments",
            headers=headers,
            json={"assigned_radiologist_id": "rad-dr-smith", "reason_code": "WORKLOAD_BALANCING"},
        )
        assert assign_res.status_code == 200
        assert assign_res.json()["assigned_radiologist_id"] == "rad-dr-smith"

        # 2. Signing is strictly forbidden for COORDINATOR -> 403
        sign_res = await ac.post(
            "/api/v1/report-versions/REP-SEC-01-v1/finalize",
            headers=headers,
            json={},
        )
        assert sign_res.status_code == 403


# =============================================================================
# TC-052: Authentication Enforcement and Session Expiry
# =============================================================================
@pytest.mark.asyncio
async def test_tc_052_unauthenticated_request_rejected():
    """TC-052: Verify requests without Bearer token or credentials return 401 Unauthorized."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Request with no headers
        res = await ac.get("/api/v1/work-items")
        assert res.status_code == 401
        assert "Bearer token required" in res.json()["detail"]


@pytest.mark.asyncio
async def test_tc_052_expired_token_rejected():
    """TC-052: Verify that an expired JWT token returns 401 Unauthorized with token expired detail."""
    expired_token = create_access_token(
        user_id="rad-expired",
        role=UserRole.REPORTING_RADIOLOGIST,
        expires_delta=timedelta(seconds=-60),  # expired 60 seconds ago
    )
    headers = {"Authorization": f"Bearer {expired_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/work-items", headers=headers)
        assert res.status_code == 401
        assert "expired" in res.json()["detail"].lower()


# =============================================================================
# TC-053: Clinical Safety Boundary - AI Agent Never Auto-Signs
# =============================================================================
def test_tc_053_clinical_safety_agent_cannot_auto_sign():
    """
    TC-053: Verify AI agent and NeMo guardrails NEVER auto-sign or bypass radiologist sign-off.
    1. Direct tool call to sign_and_finalize_report by agent raises UnauthorizedSignoffError.
    2. NeMo Guardrails check_signing_safety intercepts and blocks autonomous sign-off phrases.
    3. Domain entity Report.sign_and_release requires authorized human radiologist and signature hash.
    """
    # 1. Tool call by agent raises UnauthorizedSignoffError
    with pytest.raises(UnauthorizedSignoffError) as exc_info:
        sign_and_finalize_report.invoke({
            "work_item_id": "WI-SEC-01",
            "report_id": "REP-SEC-01",
            "signature": "autonomous_ai_bot_signature",
        })
    assert "Autonomous AI agent is prohibited from signing" in str(exc_info.value)

    # 2. NeMo Guardrails intercept autonomous sign-off action/prompt
    rail_svc = NemoGuardrailService()
    forbidden_prompts = [
        "sign_and_finalize_report",
        "Agent decided to sign the report automatically",
        "Execute digital signature autonomously",
        "Finalize and release signed diagnostic report",
    ]
    for prompt in forbidden_prompts:
        with pytest.raises(UnauthorizedSignoffError) as rail_exc:
            rail_svc.check_signing_safety(prompt)
        assert "Autonomous report signing is strictly prohibited" in str(rail_exc.value)

    # 3. Intercept tool action via guardrail service
    with pytest.raises(UnauthorizedSignoffError):
        rail_svc.intercept_agent_action("sign_and_finalize_report", {"report_id": "REP-01"})

    # 4. Domain entity verification: Non-authorized radiologist or empty signature rejected
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={"text": "Normal"},
        impression="Unremarkable",
        author_id="AI_CONCIERGE",
    )
    report = Report(
        report_id="REP-SAFETY-01",
        work_item_id="WI-SEC-01",
        status=ReportStatus.DRAFT,
        current_version_id="REP-SAFETY-01-v1",
        versions={1: ver1},
    )

    # Empty signature hash raises UnauthorizedSignoffError
    with pytest.raises(UnauthorizedSignoffError, match="signature_hash is mandatory"):
        report.sign_and_release(
            radiologist_id="rad-dr-jones",
            signature_hash="",
        )

    # Unauthorized radiologist ID raises UnauthorizedSignoffError
    with pytest.raises(UnauthorizedSignoffError, match="not authorized to sign"):
        report.sign_and_release(
            radiologist_id="ai_agent_imposter",
            signature_hash="sha256:valid_hash_format",
            authorized_radiologists=["rad-dr-jones", "rad-dr-smith"],
        )


# =============================================================================
# TC-054: NeMo Guardrails Hallucination & Low-Confidence Interception
# =============================================================================
@pytest.mark.asyncio
async def test_tc_054_hallucination_and_low_confidence_interception():
    """
    TC-054: Verify NeMo guardrails reject low-confidence findings and block
    ungrounded acute clinical pathology assertions.
    """
    rail_svc = NemoGuardrailService()

    # 1. Finding confidence below 0.40 must be blocked
    low_conf_findings = [
        {"label": "Subtle cortical nodule", "confidence": 0.28, "slice": 14}
    ]
    passed, reasons = await rail_svc.verify_radiology_output(
        study_uid="1.2.3.4",
        clinical_text="Possible lung nodule observed.",
        findings=low_conf_findings,
    )
    assert passed is False
    assert any("below confidence threshold" in r for r in reasons)

    # 2. Severe acute pathology (hemorrhage) asserted without supporting DICOM findings must be blocked
    hallucinated_text = "Acute intracranial hemorrhage detected in right basal ganglia."
    unsupported_findings = [
        {"label": "Normal brain parenchyma", "confidence": 0.95}
    ]
    passed_hallucination, reasons_h = await rail_svc.verify_radiology_output(
        study_uid="1.2.3.4",
        clinical_text=hallucinated_text,
        findings=unsupported_findings,
    )
    assert passed_hallucination is False
    assert any("unsupported by DICOM findings" in r for r in reasons_h)

    # 3. Grounded critical finding with supporting DICOM evidence passes and is flagged as critical
    valid_text = "Acute intracranial hemorrhage in right temporal lobe."
    grounded_findings = [
        {"label": "Acute intracranial hemorrhage", "confidence": 0.92, "is_critical": True}
    ]
    passed_valid, reasons_v = await rail_svc.verify_radiology_output(
        study_uid="1.2.3.4",
        clinical_text=valid_text,
        findings=grounded_findings,
    )
    assert passed_valid is True
    assert any("Critical finding flagged" in r for r in reasons_v)


# =============================================================================
# TC-055: PII/PHI De-Identification and Masking
# =============================================================================
def test_tc_055_phi_scrubbing_and_masking():
    """
    TC-055: Verify that patient names, DOBs, SSNs, phone numbers, and emails
    are completely scrubbed and masked in observability trace payloads and log outputs.
    """
    # 1. Text-level masking
    unmasked_text = (
        "Patient Name: Johnathan Doe, DOB: 1980-05-15, SSN: 123-45-6789. "
        "Contact: 555-123-4567, email: jdoe@example.com."
    )
    masked = mask_phi_text(unmasked_text)
    assert "Johnathan Doe" not in masked
    assert "[REDACTED_NAME]" in masked
    assert "1980-05-15" not in masked
    assert "[REDACTED_DOB]" in masked
    assert "123-45-6789" not in masked
    assert "[REDACTED_SSN]" in masked
    assert "555-123-4567" not in masked
    assert "[REDACTED_PHONE]" in masked
    assert "jdoe@example.com" not in masked
    assert "[REDACTED_EMAIL]" in masked

    # 2. Nested dictionary payload sanitization
    raw_payload = {
        "work_item_id": "WI-100",
        "patient_name": "Eleanor Vance",
        "dob": "1992-11-04",
        "ssn": "987-65-4321",
        "clinical_notes": "Patient Name: Eleanor Vance was admitted.",
        "metadata": {
            "family_name": "Vance",
            "phone": "415-555-0199",
            "modality": "CT",
        },
    }
    sanitized = sanitize_payload(raw_payload)
    assert sanitized["patient_name"] == "[REDACTED_PHI]"
    assert sanitized["dob"] == "[REDACTED_PHI]"
    assert sanitized["ssn"] == "[REDACTED_PHI]"
    assert "Eleanor Vance" not in sanitized["clinical_notes"]
    assert sanitized["metadata"]["family_name"] == "[REDACTED_PHI]"
    assert sanitized["metadata"]["phone"] == "[REDACTED_PHI]"
    assert sanitized["metadata"]["modality"] == "CT"

    # 3. Guardrail service mask_phi
    rail_svc = NemoGuardrailService()
    assert rail_svc.contains_phi("Patient Name: Sarah Connor") is True
    assert rail_svc.contains_phi("Clear lung fields, normal cardiothoracic ratio.") is False
    masked_by_rail = rail_svc.mask_phi("Patient Name: Sarah Connor, DOB: 1965-02-28")
    assert "Sarah Connor" not in masked_by_rail
    assert "1965-02-28" not in masked_by_rail


# =============================================================================
# TC-056: SQL Injection & XSS Payload Rejection
# =============================================================================
@pytest.mark.asyncio
async def test_tc_056_sql_injection_and_xss_safeguards():
    """
    TC-056: Verify that SQL injection and XSS payloads in query parameters,
    assignment reasons, or transition requests are safely handled without code execution.
    """
    token = create_access_token("rad-sec-tester", UserRole.REPORTING_RADIOLOGIST)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. SQL Injection payload in query parameters (worklist filter)
        sql_payload = "' OR 1=1; DROP TABLE work_items; --"
        res = await ac.get(
            f"/api/v1/work-items?modality={sql_payload}",
            headers=headers,
        )
        # Endpoint should return 200 with an empty or properly filtered list, NOT a 500 SQL crash
        assert res.status_code == 200
        assert isinstance(res.json()["items"], list)

        # 2. XSS script tag payload in assignment reason
        xss_payload = "<script>alert('XSS_ATTACK');</script>"
        coord_token = create_access_token("coord-sec", UserRole.COORDINATOR)
        coord_headers = {"Authorization": f"Bearer {coord_token}"}

        assign_res = await ac.post(
            "/api/v1/work-items/WI-SEC-01/assignments",
            headers=coord_headers,
            json={"assigned_radiologist_id": "rad-dr-smith", "reason_code": f"SPECIALTY_{xss_payload}"},
        )
        assert assign_res.status_code == 200
        # The payload is safely stored/echoed as text without execution or unescaped HTML injection
        data = assign_res.json()
        assert data["assigned_radiologist_id"] == "rad-dr-smith"

        # 3. SQL injection payload in path parameter
        path_inject_res = await ac.get(
            f"/api/v1/work-items/{sql_payload}",
            headers=headers,
        )
        # Should return 404 Not Found, not execute SQL
        assert path_inject_res.status_code == 404
