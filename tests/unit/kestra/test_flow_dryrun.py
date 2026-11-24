"""
Kestra Pipeline Simulation & Dry-Run Integration Tests.
Simulates end-to-end execution of study_ingestion_pipeline, report_delivery_retry,
and sla_monitor_pipeline flows against the FastAPI presentation layer.
"""
from datetime import datetime, timezone, timedelta
import uuid
import pytest
from starlette.testclient import TestClient

from apps.api.src.endpoints.integrations import IN_MEMORY_WORK_ITEMS, IN_MEMORY_STUDIES
from apps.api.src.main import app
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.state_machine import RadiologyStateMachine


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


def test_dry_run_study_ingestion_pipeline_clean_flow(client):
    """
    Simulates dry-run execution of study_ingestion_pipeline.yml (Happy Path):
    1. Ingest order from BackBone HMS
    2. Deterministic reconciliation against PACS metadata
    3. Branch condition evaluation -> Clean reconciliation
    4. Worklist transition to 'ready'
    """
    accession = f"ACC-TEST-{uuid.uuid4().hex[:6]}"
    mrn = f"MRN-TEST-{uuid.uuid4().hex[:6]}"
    namespace = "urn:oid:sims:hospital:mrn"

    # Task 1: Ingest order from BackBone HMS
    ingest_payload = {
        "accession_number": accession,
        "patient": {
            "mrn": mrn,
            "namespace": namespace,
            "first_name": "Jane",
            "last_name": "Doe",
            "dob": "1985-04-12",
            "gender": "female",
        },
        "modality": "CT",
        "study_instance_uid": f"1.2.840.10008.5.1.4.1.1.2.{uuid.uuid4().hex[:8]}",
        "priority": "ROUTINE",
        "study_description": "CT Brain Non-Contrast",
    }

    res_ingest = client.post("/api/v1/integrations/backbone/ingest", json=ingest_payload)
    assert res_ingest.status_code == 201
    ingest_data = res_ingest.json()
    assert ingest_data["status"] == "ingested"
    assert ingest_data["accession_number"] == accession
    work_item_id = ingest_data["work_item_id"]
    study_id = ingest_data["study_id"]
    assert ingest_data["state"] == "received"

    # Task 2: Deterministic Reconciliation (PACS metadata matches Order metadata)
    reconcile_payload = {
        "accession_number": accession,
        "order_mrn": mrn,
        "order_namespace": namespace,
        "pacs_mrn": mrn,
        "pacs_namespace": namespace,
        "study_id": study_id,
        "work_item_id": work_item_id,
    }

    res_reconcile = client.post("/api/v1/integrations/backbone/reconcile", json=reconcile_payload)
    assert res_reconcile.status_code == 200
    reconcile_data = res_reconcile.json()
    assert reconcile_data["is_reconciled"] is True
    assert reconcile_data["status"] == "reconciled"

    # Task 3: Branch Evaluation (condition: outputs.deterministic_reconciliation.body.is_reconciled == false)
    branch_condition = reconcile_data["is_reconciled"] is False
    assert branch_condition is False, "Clean flow must evaluate to false for conflict branch"

    # Task 4: Else branch -> Update worklist status to 'ready'
    res_ready = client.post(f"/api/v1/integrations/worklist/{work_item_id}/ready")
    assert res_ready.status_code == 200
    ready_data = res_ready.json()
    assert ready_data["current_state"] == "ready"
    assert ready_data["work_item_id"] == work_item_id


def test_dry_run_study_ingestion_pipeline_conflict_routing(client):
    """
    Simulates dry-run execution of study_ingestion_pipeline.yml (Discrepancy Path):
    1. Ingest order from BackBone HMS
    2. Deterministic reconciliation encounters MRN mismatch
    3. Branch condition evaluation -> is_reconciled == false triggers 'then' branch
    4. Flag study and push to human reconciliation queue
    5. Invariant: Clinical writeback is blocked
    """
    accession = f"ACC-MISMATCH-{uuid.uuid4().hex[:6]}"
    order_mrn = f"MRN-ORDER-{uuid.uuid4().hex[:6]}"
    pacs_mrn = f"MRN-PACS-DIFFERENT-{uuid.uuid4().hex[:6]}"
    namespace = "urn:oid:sims:hospital:mrn"

    # Task 1: Ingest order
    ingest_payload = {
        "accession_number": accession,
        "patient": {
            "mrn": order_mrn,
            "namespace": namespace,
            "first_name": "Alice",
            "last_name": "Smith",
        },
        "modality": "MRI",
        "priority": "URGENT",
    }
    res_ingest = client.post("/api/v1/integrations/backbone/ingest", json=ingest_payload)
    assert res_ingest.status_code == 201
    ingest_data = res_ingest.json()
    work_item_id = ingest_data["work_item_id"]
    study_id = ingest_data["study_id"]

    # Task 2: Deterministic Reconciliation with mismatched patient identifier
    reconcile_payload = {
        "accession_number": accession,
        "order_mrn": order_mrn,
        "order_namespace": namespace,
        "pacs_mrn": pacs_mrn,
        "pacs_namespace": namespace,
        "study_id": study_id,
        "work_item_id": work_item_id,
    }
    res_reconcile = client.post("/api/v1/integrations/backbone/reconcile", json=reconcile_payload)
    assert res_reconcile.status_code == 200
    reconcile_data = res_reconcile.json()
    assert reconcile_data["is_reconciled"] is False
    assert reconcile_data["status"] == "reconciliation_required"
    assert len(reconcile_data["discrepancy_reasons"]) > 0

    # Task 3: Branch Evaluation (condition: is_reconciled == false)
    branch_condition = reconcile_data["is_reconciled"] is False
    assert branch_condition is True, "Conflict flow must trigger 'then' branch"

    # Task 4: Then branch -> Flag and push to exception queue
    flag_payload = {
        "study_id": study_id,
        "work_item_id": work_item_id,
        "reason": f"Discrepancy detected: {reconcile_data['discrepancy_reasons']}",
    }
    res_flag = client.post("/api/v1/integrations/backbone/reconciliation/flag", json=flag_payload)
    assert res_flag.status_code == 200
    flag_data = res_flag.json()
    assert flag_data["clinical_writeback_blocked"] is True
    assert flag_data["new_state"] == "reconciliation_required"
    assert "ticket_id" in flag_data

    # Task 5: Verify safety invariant in State Machine
    work_item = IN_MEMORY_WORK_ITEMS[work_item_id]
    assert work_item.state == WorkItemState.RECONCILIATION_REQUIRED
    with pytest.raises(Exception) as exc_info:
        RadiologyStateMachine.validate_clinical_writeback_allowed(work_item)
    assert "Clinical writeback blocked" in str(exc_info.value)


def test_dry_run_report_delivery_retry_pipeline(client):
    """
    Simulates dry-run execution of report_delivery_retry.yml:
    1. Scheduled trigger executes flush_outbox_deliveries
    2. Endpoint processes pending events and returns status
    """
    res = client.post("/api/v1/integrations/charmhealth/retry-deliveries?batch_size=20")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert "processed_count" in data
    assert "timestamp" in data


def test_dry_run_sla_monitor_pipeline(client):
    """
    Simulates dry-run execution of sla_monitor_pipeline.yml:
    1. Seed an overdue work item
    2. Execute /api/v1/triage/sla/evaluate
    3. Evaluate breach condition (overdue_count > 0)
    4. Escalate priority to STAT with SHAP explainability
    """
    overdue_work_item_id = f"WI-OVERDUE-{uuid.uuid4().hex[:6]}"
    overdue_item = WorkItem(
        work_item_id=overdue_work_item_id,
        study_id=f"STUDY-{overdue_work_item_id}",
        state=WorkItemState.IN_PROGRESS,
        priority=Priority.ROUTINE,
        sla_deadline=datetime.now(timezone.utc) - timedelta(minutes=45),  # 45 min overdue
    )
    IN_MEMORY_WORK_ITEMS[overdue_work_item_id] = overdue_item

    # Step 1: Evaluate SLA Deadlines
    res_eval = client.post("/api/v1/triage/sla/evaluate?threshold_minutes=15")
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["overdue_count"] >= 1
    assert any(item["work_item_id"] == overdue_work_item_id for item in eval_data["at_risk_items"])

    # Step 2: Breach condition evaluation
    has_breach_risk = eval_data["overdue_count"] > 0 or eval_data["approaching_count"] > 0
    assert has_breach_risk is True

    # Step 3: Escalate at-risk work item to STAT
    escalate_payload = {
        "work_item_id": overdue_work_item_id,
        "target_priority": "STAT",
        "reason": "Automated SLA Monitor: 45 min overdue. Elevated to STAT.",
    }
    res_escalate = client.post("/api/v1/triage/sla/escalate", json=escalate_payload)
    assert res_escalate.status_code == 200
    escalate_data = res_escalate.json()
    assert escalate_data["work_item_id"] == overdue_work_item_id
    assert escalate_data["previous_priority"] == "ROUTINE"
    assert escalate_data["new_priority"] == "STAT"
    assert escalate_data["notification_dispatched"] is True

    # Step 4: Verify SHAP explainability attributes in escalation payload
    shap_attr = escalate_data["shap_attribution"]
    assert "top_risk_driver" in shap_attr
    assert "breach_risk_probability" in shap_attr
    assert "feature_attributions" in shap_attr
    assert shap_attr["breach_risk_probability"] > 0.0

    # Step 5: Verify work item updated state
    assert IN_MEMORY_WORK_ITEMS[overdue_work_item_id].priority == Priority.STAT
