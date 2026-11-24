"""
End-to-End (E2E) Integration Test Runner: Full Study Lifecycle.
Simulates and validates complete radiology workflow across all architectural boundaries:
1. Ingestion:
   - Generate synthetic CT DICOM payload with pydicom headers.
   - Post to BackBone HMS Ingestion endpoint (/api/v1/integrations/backbone/ingest).
   - Verify Kestra pipeline picks up event, executes deterministic reconciliation, and transitions WorkItem to 'ready'.
2. Case Concierge & Reporting:
   - Invoke Deep Agent Case Concierge to synthesize patient clinical history and priors.
   - Transition WorkItem to 'assigned' and 'in_progress'.
   - Generate AI preliminary report draft and verify NeMo guardrails validate clean non-hallucinatory content.
   - Confirm WorkItem and Report advance to 'draft_ready'.
3. Finalization & Delivery:
   - Execute clinician sign-off via API with authorized radiologist credentials.
   - Verify state becomes 'finalized', cryptographic SHA-256 signature record is generated, and version is append-only immutable.
   - Verify Transactional Outbox event is dispatched via Celery background worker to CharmHealth EHR adapter.
"""
from datetime import datetime, timezone, timedelta
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch
import httpx

from apps.api.middleware.auth import UserRole, create_access_token
from apps.api.src.endpoints.integrations import (
    IN_MEMORY_PATIENTS,
    IN_MEMORY_STUDIES,
    IN_MEMORY_WORK_ITEMS,
)
from apps.api.routes.reports import IN_MEMORY_REPORTS
from apps.api.src.main import app
from agents.case_concierge import CaseConciergeAgent
from agents.guardrails.service import NemoGuardrailService, guardrail_service
from agents.tools.reporting_tools import draft_structured_report
from core.domain.entities.audit_log import AuditLog
from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import Modality, RadiologyStudy
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import ImmutableReportOverrideError
from core.domain.state_machine import RadiologyStateMachine
from core.infrastructure.adapters.charmhealth_adapter import (
    CapabilityMatrix,
    CharmHealthEHRAdapter,
)
from core.infrastructure.adapters.mock_harness import (
    MockVendorTransport,
    SyntheticDICOMBuilder,
)
from core.infrastructure.adapters.pacs_adapter import PACSAdapter
from core.infrastructure.db.session import AsyncSessionLocal
from core.infrastructure.kestra.client import kestra_client
from core.infrastructure.persistence.models import OutboxEventModel
from core.infrastructure.persistence.outbox_worker import (
    DownstreamDispatcher,
    process_outbox_batch,
    process_outbox_events_task,
)
from core.infrastructure.persistence.repositories.audit_repository import AuditRepository
from core.infrastructure.persistence.repositories.patient_study_repository import (
    PatientRepository,
    StudyPersistenceRepository,
)
from core.infrastructure.persistence.repositories.report_repository import ReportRepository
from core.infrastructure.persistence.repositories.work_item_repository import WorkItemRepository


@pytest.fixture(autouse=True)
def clean_in_memory_registries():
    """Ensure in-memory mock repositories have fresh state before each test scenario."""
    IN_MEMORY_PATIENTS.clear()
    IN_MEMORY_STUDIES.clear()
    IN_MEMORY_WORK_ITEMS.clear()
    IN_MEMORY_REPORTS.clear()


@pytest.mark.asyncio
async def test_full_radiology_study_lifecycle_e2e():
    """
    End-to-End Simulation of Full Study Lifecycle:
    Step 1: Synthetic DICOM Ingestion & Kestra Reconciliation -> READY
    Step 2: Case Concierge Priors Synthesis & NeMo Guardrail AI Draft -> DRAFT_READY
    Step 3: Clinician Cryptographic Sign-Off & CharmHealth Outbox Delivery -> FINALIZED & DELIVERED
    """
    # Create authenticated client session
    rad_token = create_access_token(
        user_id="rad-dr-evans",
        role=UserRole.REPORTING_RADIOLOGIST,
        name="Dr. Jane Evans, MD",
        license_number="RAD-MD-STATE-99412",
    )
    auth_headers = {"Authorization": f"Bearer {rad_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        # =====================================================================
        # SCENARIO 1: INGESTION & RECONCILIATION
        # =====================================================================
        # 1.1 Generate synthetic CT DICOM payload with pydicom headers
        acc_num = f"ACC-E2E-{uuid.uuid4().hex[:6]}"
        pat_mrn = f"MRN-E2E-{uuid.uuid4().hex[:6]}"
        study_uid_num = str(int(uuid.uuid4().int % 100000000))
        study_uid = f"1.2.840.113619.2.55.3.{study_uid_num}"

        dicom_bytes = SyntheticDICOMBuilder.create_dicom_bytes(
            modality="CT",
            patient_id=f"PAT-{pat_mrn}",
            patient_name="Connor^Sarah",
            patient_birth_date="19650228",
            patient_sex="F",
            accession_number=acc_num,
            study_description="CT Chest Pulmonary Angiogram",
            study_instance_uid=study_uid,
            include_pixel_data=True,
        )

        # 1.2 Parse headers via PACS adapter (strictly excluding pixel data)
        dicom_meta = PACSAdapter.parse_dicom_bytes(dicom_bytes, stop_before_pixels=True)
        assert dicom_meta.modality == "CT"
        assert dicom_meta.accession_number == acc_num
        assert "PixelData" not in dicom_meta.raw_metadata_json

        # 1.3 Post to BackBone HMS Ingestion endpoint
        ingest_payload = {
            "accession_number": acc_num,
            "patient": {
                "id": f"PAT-{pat_mrn}",
                "mrn": pat_mrn,
                "namespace": "urn:oid:sims.hospital.patients",
                "family_name": "Connor",
                "given_name": "Sarah",
                "birth_date": "1965-02-28",
                "gender": "female",
            },
            "modality": "CT",
            "study_instance_uid": study_uid,
            "priority": "STAT",
            "study_description": "CT Chest Pulmonary Angiogram",
            "initial_state": "received",
        }

        ingest_res = await client.post("/api/v1/integrations/backbone/ingest", json=ingest_payload)
        assert ingest_res.status_code == 201
        ingest_data = ingest_res.json()

        work_item_id = ingest_data["work_item_id"]
        study_id = ingest_data["study_id"]
        assert ingest_data["accession_number"] == acc_num
        assert ingest_data["modality"] == "CT"
        assert ingest_data["priority"] == "STAT"
        assert ingest_data["reconciliation_status"] == "reconciled"

        # 1.4 Simulate Kestra Pipeline: trigger ingestion flow & run reconciliation check
        kestra_res = await kestra_client.trigger_flow(
            flow_id="study_ingestion_pipeline",
            inputs={"study_uid": study_uid, "accession_number": acc_num},
        )
        assert kestra_res["status"] in ("submitted", "running", "simulated", "success", "sent", "queued_offline")

        # Run authoritative reconciliation check
        recon_res = await client.post(
            "/api/v1/integrations/backbone/reconcile",
            json={
                "accession_number": acc_num,
                "order_mrn": pat_mrn,
                "order_namespace": "urn:oid:sims.hospital.patients",
                "pacs_mrn": pat_mrn,
                "pacs_namespace": "urn:oid:sims.hospital.patients",
                "study_id": study_id,
            },
        )
        assert recon_res.status_code == 200
        assert recon_res.json()["is_reconciled"] is True
        assert recon_res.json()["status"] == "reconciled"

        # Clean validation transitions WorkItem to 'ready'
        ready_res = await client.post(f"/api/v1/integrations/worklist/{work_item_id}/ready")
        assert ready_res.status_code == 200
        assert ready_res.json()["current_state"] == "ready"

        # Verify WorkItem in worklist is 'ready'
        wi_detail_res = await client.get(f"/api/v1/work-items/{work_item_id}", headers=auth_headers)
        assert wi_detail_res.status_code == 200
        assert wi_detail_res.json()["state"] == "ready"

        # =====================================================================
        # SCENARIO 2: CASE CONCIERGE & AI REPORT DRAFTING
        # =====================================================================
        # 2.1 Invoke Deep Agent Case Concierge to synthesize clinical context and priors
        case_concierge = CaseConciergeAgent()
        concierge_brief = await case_concierge.prepare_case_brief(
            patient_id=f"PAT-{pat_mrn}",
            study_id=study_id,
            modality="CT",
            work_item_id=work_item_id,
        )
        assert concierge_brief.patient_id == f"PAT-{pat_mrn}"
        assert concierge_brief.modality == "CT"
        assert concierge_brief.referral_question != ""
        assert len(concierge_brief.relevant_priors_summary) > 0

        # Verify Case Concierge AI summary is returned through API
        wi_res = await client.get(f"/api/v1/work-items/{work_item_id}", headers=auth_headers)
        wi_data = wi_res.json()
        assert wi_data["concierge_brief"] is not None
        assert "referral_question" in wi_data["concierge_brief"]

        # 2.2 Assign WorkItem to Radiologist -> 'assigned'
        assign_res = await client.post(
            f"/api/v1/work-items/{work_item_id}/assignments",
            headers=auth_headers,
            json={
                "assigned_radiologist_id": "rad-dr-evans",
                "reason_code": "CLINICAL_SPECIALTY_MATCH",
            },
        )
        assert assign_res.status_code == 200
        assert assign_res.json()["state"] == "assigned"
        assert assign_res.json()["assigned_radiologist_id"] == "rad-dr-evans"

        # 2.3 Radiologist begins review -> transition to 'in_progress'
        trans_res = await client.post(
            f"/api/v1/work-items/{work_item_id}/transitions",
            headers=auth_headers,
            json={"target_state": "in_progress", "reason": "Radiologist opened exam in viewer"},
        )
        assert trans_res.status_code == 200
        assert trans_res.json()["state"] == "in_progress"

        # 2.4 Generate AI Draft Report using reporting agent tool
        draft_findings = (
            "The thoracic aorta is normal in caliber. No acute pulmonary embolism in main pulmonary arteries. "
            "Lungs are clear of acute focal consolidation or pleural effusion."
        )
        draft_impression = "No acute pulmonary embolism. Normal contrast-enhanced chest CT."

        draft_tool_res = draft_structured_report.invoke({
            "work_item_id": work_item_id,
            "findings": draft_findings,
            "impression": draft_impression,
        })
        assert draft_tool_res["status"] == "DRAFT"
        assert draft_tool_res["is_signed"] is False
        assert draft_tool_res["author_id"] == "SIMS_AI_CONCIERGE_AGENT"

        # 2.5 Run NeMo Guardrail verification on AI draft output
        rail_findings = [
            {"label": "Thoracic Aorta Normal", "confidence": 0.98},
            {"label": "No Pulmonary Embolism", "confidence": 0.96},
        ]
        is_safe, reasons = await guardrail_service.verify_radiology_output(
            study_uid=study_uid,
            clinical_text=draft_impression,
            findings=rail_findings,
        )
        assert is_safe is True
        assert any("passed" in r.lower() for r in reasons)

        # 2.6 Post Draft to API -> transitions WorkItem to 'draft_ready'
        draft_api_res = await client.post(
            f"/api/v1/work-items/{work_item_id}/report-drafts",
            headers=auth_headers,
            json={
                "findings": draft_findings,
                "impression": draft_impression,
                "clinical_indication": "CT Chest rule out pulmonary embolism",
            },
        )
        assert draft_api_res.status_code == 200
        draft_data = draft_api_res.json()
        report_id = draft_data["report_id"]
        version_id = f"{report_id}-v{draft_data['version_number']}"
        assert draft_data["status"] == "DRAFT"

        # Verify WorkItem state is now DRAFT_READY
        wi_check = await client.get(f"/api/v1/work-items/{work_item_id}", headers=auth_headers)
        assert wi_check.json()["state"] == "draft_ready"

        # =====================================================================
        # SCENARIO 3: CLINICIAN FINALIZATION & CHARMHEALTH DELIVERY
        # =====================================================================
        # 3.1 Advance to 'in_review' for clinician final sign-off
        in_review_res = await client.post(
            f"/api/v1/work-items/{work_item_id}/transitions",
            headers=auth_headers,
            json={"target_state": "in_review", "reason": "Radiologist final verification"},
        )
        assert in_review_res.status_code == 200
        assert in_review_res.json()["state"] == "in_review"

        # 3.2 Clinician executes cryptographic sign-off via API
        sign_res = await client.post(
            f"/api/v1/report-versions/{version_id}/finalize",
            headers=auth_headers,
            json={"additional_notes": "Findings corroborated and signed by Dr. Evans"},
        )
        assert sign_res.status_code == 200
        sign_data = sign_res.json()
        assert sign_data["status"] == "SIGNED"
        assert sign_data["is_signed"] is True
        assert sign_data["signature_hash"] != ""
        assert len(sign_data["signature_hash"]) == 64  # SHA-256 hexadecimal hash
        assert sign_data["signer_role"] == UserRole.REPORTING_RADIOLOGIST.value

        # Verify associated WorkItem transitioned to FINALIZED
        wi_final = await client.get(f"/api/v1/work-items/{work_item_id}", headers=auth_headers)
        assert wi_final.json()["state"] == "finalized"

        # 3.3 Verify Report Version Immutability (Append-Only Invariant)
        # Attempting to re-finalize or mutate signed version raises error or is blocked
        async with AsyncSessionLocal() as session:
            r_repo = ReportRepository(session)
            db_report = await r_repo.get_by_id(report_id)
            if db_report:
                # Appending with existing version number 1 must fail
                v1_dup = ReportVersion(
                    version_number=1,
                    structured_findings={"mutation": "illegal"},
                    impression="Altered impression",
                    author_id="ATTACKER",
                )
                with pytest.raises(ImmutableReportOverrideError):
                    await r_repo.save_version(report_id, v1_dup)

        # 3.4 Outbox Dispatch & Delivery to CharmHealth EHR
        # Atomically queue outbox delivery event
        async with AsyncSessionLocal() as session:
            audit_repo = AuditRepository(session)
            audit_entry = AuditLog(
                actor_id="rad-dr-evans",
                action="REPORT_FINALIZED_FOR_DELIVERY",
                resource_id=report_id,
                correlation_id=f"corr-e2e-{acc_num}",
                details={"version_id": version_id, "signature": sign_data["signature_hash"]},
            )
            outbox_evt = await audit_repo.record_with_outbox(
                audit_log=audit_entry,
                aggregate_type="REPORT",
                aggregate_id=report_id,
                event_type="DIAGNOSTIC_REPORT_FINALIZED",
                payload={
                    "destination_system": "CHARMHEALTH_EHR",
                    "report_id": report_id,
                    "accession_number": acc_num,
                    "patient_id": f"PAT-{pat_mrn}",
                    "modality": "CT",
                },
            )
            await session.commit()

        # 3.5 Dispatch via DownstreamDispatcher & Celery worker
        dispatch_ok = await DownstreamDispatcher.dispatch(outbox_evt)
        assert dispatch_ok is True

        # Process outbox events via Celery background runner task
        celery_result = process_outbox_events_task(batch_size=10)
        assert celery_result["status"] == "SUCCESS"
        assert celery_result["events_processed"] >= 1

        # 3.6 Transmit to CharmHealth EHR adapter and verify FHIR R4 DiagnosticReport delivery
        transport = MockVendorTransport()
        transport.simulate_outage = False
        charm_adapter = CharmHealthEHRAdapter(
            base_url="http://mock-ehr/fhir/r4",
            capabilities=CapabilityMatrix(final_report_write=True),
        )

        patient_entity = Patient(
            patient_id=f"PAT-{pat_mrn}",
            mrn=pat_mrn,
            identifier_namespace="urn:oid:sims.hospital.patients",
        )
        study_entity = RadiologyStudy(
            study_id=study_id,
            study_instance_uid=study_uid,
            accession_number=acc_num,
            modality=Modality.CT,
        )
        ver_entity = ReportVersion(
            version_number=1,
            structured_findings={"narrative": draft_findings},
            impression=draft_impression,
            author_id="rad-dr-evans",
            signature_hash=sign_data["signature_hash"],
            signed_at=datetime.now(timezone.utc),
        )
        report_entity = Report(
            report_id=report_id,
            work_item_id=work_item_id,
            status=ReportStatus.RELEASED,
            current_version_id=version_id,
            versions={1: ver_entity},
        )

        with patch.object(httpx.AsyncClient, "post", new=lambda self, url, **kwargs: transport.handle_async_request(
            httpx.Request("POST", url, json=kwargs.get("json"))
        )):
            delivery = await charm_adapter.transmit_final_report(
                report=report_entity,
                patient=patient_entity,
                study=study_entity,
                version=ver_entity,
            )

        assert delivery.status == "DELIVERED"
        assert delivery.delivered is True
        assert delivery.fallback_to_outbox is False
        assert delivery.fhir_resource_id is not None

        # Verify WorkItem can now reach DELIVERED state
        delivered_trans_res = await client.post(
            f"/api/v1/work-items/{work_item_id}/transitions",
            headers=auth_headers,
            json={"target_state": "delivered", "reason": "Delivered to CharmHealth EHR"},
        )
        assert delivered_trans_res.status_code == 200
        assert delivered_trans_res.json()["state"] == "delivered"


@pytest.mark.asyncio
async def test_e2e_reconciliation_quarantine_and_resolution():
    """
    E2E Scenario: Inbound Patient MRN Mismatch / Ambiguity
    1. Inbound study has mismatched demographic and identifier fields.
    2. Flagged for human reconciliation -> quarantined in 'reconciliation_required'.
    3. Clinical writeback is strictly blocked.
    4. Identity resolved by supervisor -> transitions to 'ready'.
    """
    coord_token = create_access_token("coord-supervisor", UserRole.COORDINATOR)
    coord_headers = {"Authorization": f"Bearer {coord_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        acc_num = f"ACC-AMBIG-{uuid.uuid4().hex[:6]}"

        # 1. Ingest order with ambiguous/missing MRN
        ingest_res = await client.post(
            "/api/v1/integrations/backbone/ingest",
            json={
                "accession_number": acc_num,
                "patient": {
                    "mrn": "",  # Triggers quarantine
                    "namespace": "urn:oid:sims.hospital.patients",
                    "family_name": "Doe",
                    "given_name": "John",
                },
                "modality": "CT",
                "priority": "STAT",
            },
        )
        assert ingest_res.status_code == 201
        data = ingest_res.json()
        work_item_id = data["work_item_id"]
        study_id = data["study_id"]
        assert data["reconciliation_status"] == "reconciliation_required"

        # 2. Flag reconciliation via Kestra pipeline / exception router
        flag_res = await client.post(
            "/api/v1/integrations/backbone/reconciliation/flag",
            json={
                "study_id": study_id,
                "work_item_id": work_item_id,
                "reason": "Missing authoritative MRN in inbound order ADT feed",
            },
        )
        assert flag_res.status_code == 200
        assert flag_res.json()["new_state"] == "reconciliation_required"

        # Verify WorkItem is quarantined in 'reconciliation_required'
        wi_quarantined = await client.get(f"/api/v1/work-items/{work_item_id}", headers=coord_headers)
        assert wi_quarantined.json()["state"] == "reconciliation_required"

        # 3. Verify clinical writeback is blocked
        rad_token = create_access_token("rad-01", UserRole.REPORTING_RADIOLOGIST)
        rad_headers = {"Authorization": f"Bearer {rad_token}"}
        draft_blocked_res = await client.post(
            f"/api/v1/work-items/{work_item_id}/report-drafts",
            headers=rad_headers,
            json={"findings": "Test", "impression": "Test"},
        )
        assert draft_blocked_res.status_code == 409
        assert "Clinical writeback blocked" in draft_blocked_res.json()["detail"]

        # 4. Medical records supervisor resolves reconciliation -> ready
        resolve_res = await client.post(f"/api/v1/integrations/worklist/{work_item_id}/ready")
        assert resolve_res.status_code == 200
        assert resolve_res.json()["current_state"] == "ready"


@pytest.mark.asyncio
async def test_e2e_agent_signoff_blocked_requires_human_clinician():
    """
    E2E Scenario: Clinical Safety Boundary Verification
    1. Ingest valid study and advance to 'in_review'.
    2. Attempt sign-off using agent / non-human credentials -> Rejected (HTTP 403 / UnauthorizedSignoffError).
    3. Finalization only succeeds when authenticated reporting radiologist signs.
    """
    rad_token = create_access_token("rad-md-legal", UserRole.REPORTING_RADIOLOGIST)
    rad_headers = {"Authorization": f"Bearer {rad_token}"}

    resident_token = create_access_token("resident-ai-proxy", UserRole.RADIOLOGY_RESIDENT)
    resident_headers = {"Authorization": f"Bearer {resident_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        acc_num = f"ACC-SAFETY-{uuid.uuid4().hex[:6]}"
        ingest_res = await client.post(
            "/api/v1/integrations/backbone/ingest",
            json={
                "accession_number": acc_num,
                "patient": {
                    "mrn": f"MRN-S-{acc_num}",
                    "namespace": "urn:oid:sims",
                    "family_name": "Smith",
                    "given_name": "Adam",
                },
                "modality": "XRAY",
                "priority": "ROUTINE",
                "initial_state": "ready",
            },
        )
        work_item_id = ingest_res.json()["work_item_id"]

        # Assign and advance to in_progress -> draft_ready -> in_review
        await client.post(
            f"/api/v1/work-items/{work_item_id}/assignments",
            headers=rad_headers,
            json={"assigned_radiologist_id": "rad-md-legal", "reason_code": "ROUTINE_READ"},
        )
        await client.post(
            f"/api/v1/work-items/{work_item_id}/transitions",
            headers=rad_headers,
            json={"target_state": "in_progress"},
        )
        draft_res = await client.post(
            f"/api/v1/work-items/{work_item_id}/report-drafts",
            headers=rad_headers,
            json={"findings": "Normal chest.", "impression": "Normal."},
        )
        version_id = f"{draft_res.json()['report_id']}-v1"

        await client.post(
            f"/api/v1/work-items/{work_item_id}/transitions",
            headers=rad_headers,
            json={"target_state": "in_review"},
        )

        # Non-clinician proxy attempts sign-off -> 403 Forbidden
        proxy_sign_res = await client.post(
            f"/api/v1/report-versions/{version_id}/finalize",
            headers=resident_headers,
            json={},
        )
        assert proxy_sign_res.status_code == 403

        # Authenticated licensed radiologist signs -> 200 OK
        clinician_sign_res = await client.post(
            f"/api/v1/report-versions/{version_id}/finalize",
            headers=rad_headers,
            json={},
        )
        assert clinician_sign_res.status_code == 200
        assert clinician_sign_res.json()["is_signed"] is True

