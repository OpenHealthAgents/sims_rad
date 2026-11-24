"""
Server-Sent Events (SSE) Agent Streaming Endpoint.
Streams real-time A2UI protocol messages emitted by Deep Agents:
- Surface layouts
- Worklist updates
- Case Concierge AI briefs
- SHAP feature attributions
- Diagnostic report drafts and clinician sign-off events
"""
import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from apps.api.src.endpoints.integrations import IN_MEMORY_WORK_ITEMS, IN_MEMORY_STUDIES

logger = logging.getLogger("sims_radiology.api.agent_stream")

router = APIRouter(prefix="/agent", tags=["Deep Agents SSE Stream"])


def create_a2ui_message(message_type: str, surface_id: str, payload: dict) -> str:
    """Format an A2UI compliant Server-Sent Event message."""
    data = {
        "protocol": "a2ui-v0.9",
        "type": message_type,
        "surfaceId": surface_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    return f"data: {json.dumps(data)}\n\n"


@router.get(
    "/stream",
    summary="Establish SSE stream for dynamic A2UI widgets emitted by Deep Agents",
    response_class=StreamingResponse,
)
async def stream_agent_ui(
    work_item_id: Optional[str] = Query(None, description="Optional active work item to monitor"),
) -> StreamingResponse:
    """
    Establish Server-Sent Events stream delivering A2UI protocol widgets.
    Emits initial workbench layout, worklist state, Case Concierge briefs,
    and operational telemetry.
    """
    logger.info(f"SSE client connected to /api/v1/agent/stream (work_item_id={work_item_id})")

    async def event_generator() -> AsyncGenerator[str, None]:
        # 1. Emit Initial Handshake
        yield f"event: open\ndata: {json.dumps({'status': 'connected', 'server': 'SIMS DeepAgents A2UI Engine'})}\n\n"
        await asyncio.sleep(0.1)

        # 2. Emit Workbench Surface Root Layout
        root_surface = {
            "rootWidget": "RadiologistWorkbench",
            "title": "SIMS Radiology Operating Platform",
            "activeWorkItemId": work_item_id or "WI-001",
            "panels": [
                {"id": "worklist", "widget": "WorklistTable", "title": "Diagnostic Worklist"},
                {"id": "concierge", "widget": "CaseConciergePanel", "title": "Case Concierge AI"},
                {"id": "editor", "widget": "ReportEditorWidget", "title": "Diagnostic Report"},
                {"id": "explainability", "widget": "ExplainabilityWidget", "title": "SLA & Triage SHAP Analysis"},
                {"id": "metrics", "widget": "MetricsDashboardWidget", "title": "Operational Metrics"},
            ],
        }
        yield create_a2ui_message("surfaceCreate", "workbench-root", root_surface)
        await asyncio.sleep(0.1)

        # 3. Emit Worklist Data
        work_items_data = []
        for wi in IN_MEMORY_WORK_ITEMS.values():
            study = IN_MEMORY_STUDIES.get(wi.study_id)
            modality = study.modality.value if study else "CT"
            work_items_data.append({
                "work_item_id": wi.work_item_id,
                "study_id": wi.study_id,
                "modality": modality,
                "priority": wi.priority.value,
                "state": wi.state.value,
                "assigned_radiologist_id": wi.assigned_radiologist_id,
                "sla_deadline": wi.sla_deadline.isoformat() if wi.sla_deadline else "",
                "version": wi.version,
            })
        yield create_a2ui_message("dataUpdate", "worklist-table", {"items": work_items_data})
        await asyncio.sleep(0.1)

        # 4. Emit Active Case Concierge Brief
        active_id = work_item_id or "WI-001"
        concierge_brief = {
            "work_item_id": active_id,
            "patient_name": "Eleanor Vance (Age 64, F)",
            "mrn": "MRN-1001",
            "study_type": "CT Head Non-Contrast",
            "referral_question": "Rule out acute intracranial hemorrhage following fall with blunt head trauma.",
            "clinical_alerts": [
                "CRITICAL: Patient on high-dose anticoagulant therapy (Warfarin, INR 2.8).",
                "ALERT: Prior ischemic stroke noted in 2024 left MCA territory.",
            ],
            "relevant_priors_summary": "CT Head (2024-03-12): Encephalomalacia in left middle cerebral artery territory, unchanged ventricular size.",
            "patient_context_summary": "Hypertension, chronic atrial fibrillation, recent syncopal episode.",
        }
        yield create_a2ui_message("dataUpdate", "case-concierge", concierge_brief)
        await asyncio.sleep(0.1)

        # 5. Emit SHAP Explainability Attributes
        shap_payload = {
            "work_item_id": active_id,
            "predicted_sla_breach_probability": 0.22,
            "base_expected_value": 0.48,
            "top_drivers": [
                {"feature": "modality_complexity_score", "attribution": 0.12, "impact": "INCREASES_RISK"},
                {"feature": "emergency_volume_surge_index", "attribution": 0.08, "impact": "INCREASES_RISK"},
                {"feature": "elapsed_turnaround_ratio", "attribution": -0.15, "impact": "DECREASES_RISK"},
            ],
            "recommendation": "LOW RISK (22.0%): Operational throughput is within normal clinical limits.",
        }
        yield create_a2ui_message("dataUpdate", "explainability-panel", shap_payload)
        await asyncio.sleep(0.1)

        # 6. Periodic Heartbeat / telemetry updates
        try:
            while True:
                await asyncio.sleep(15.0)
                heartbeat = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "active_agents": ["CaseConciergeAgent", "ReportingAssistantAgent", "GuardrailVerifier"],
                    "queue_depth": len(IN_MEMORY_WORK_ITEMS),
                }
                yield f"event: ping\ndata: {json.dumps(heartbeat)}\n\n"
        except asyncio.CancelledError:
            logger.info("SSE client disconnected from /api/v1/agent/stream.")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
