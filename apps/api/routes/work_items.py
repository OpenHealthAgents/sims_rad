"""
Work Items REST API Endpoints (Clean Architecture).
Implements worklist queries, Case Concierge AI briefs, SHAP explainability,
assignment management, workflow state transitions, and AI report drafting.
"""
from datetime import datetime, timezone, timedelta
import logging
from typing import Annotated, Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from agents.case_concierge import CaseConciergeAgent
from agents.tools.reporting_tools import draft_structured_report
from agents.tools.shap_tools import compute_sla_risk_explanation
from apps.api.middleware.auth import (
    AuthenticatedUser,
    UserRole,
    get_current_user,
    require_roles,
)
from apps.api.src.endpoints.integrations import (
    IN_MEMORY_PATIENTS,
    IN_MEMORY_STUDIES,
    IN_MEMORY_WORK_ITEMS,
)
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import (
    ClinicalWritebackBlockedError,
    ConcurrencyVersionError,
    InvalidStateTransitionError,
)
from core.domain.state_machine import RadiologyStateMachine
from core.infrastructure.db.session import AsyncSessionLocal
from core.infrastructure.observability.langfuse_config import (
    instrument_agent,
    observability_service,
)
from core.infrastructure.persistence.repositories.report_repository import ReportRepository
from core.infrastructure.persistence.repositories.work_item_repository import WorkItemRepository
from apps.api.routes.reports import seed_in_memory_report

logger = logging.getLogger("sims_radiology.api.work_items")

router = APIRouter(prefix="/work-items", tags=["Work Items & Worklists"])
case_concierge = CaseConciergeAgent()


# Request / Response Schemas
class WorkItemDetailDTO(BaseModel):
    work_item_id: str
    study_id: str
    modality: str
    priority: str
    state: str
    assigned_radiologist_id: Optional[str] = None
    sla_deadline: str
    version: int
    created_at: str
    updated_at: str
    concierge_brief: Optional[Dict[str, Any]] = None


class WorkItemListResponse(BaseModel):
    items: List[WorkItemDetailDTO]
    total_count: int
    skip: int
    limit: int


class AssignmentRequest(BaseModel):
    assigned_radiologist_id: str = Field(..., description="Target clinician identifier")
    reason_code: str = Field(..., description="Assignment justification code (e.g. SUB_SPECIALTY_MATCH, CAPACITY_REBALANCE)")
    notes: Optional[str] = Field(None, description="Optional administrative notes")


class TransitionRequest(BaseModel):
    target_state: str = Field(..., description="Requested WorkItemState")
    expected_version: Optional[int] = Field(None, description="Optimistic locking version")
    reason: Optional[str] = Field(None, description="Clinical reason for state change")


class ReportDraftRequest(BaseModel):
    findings: str = Field(..., description="Draft findings text")
    impression: str = Field(..., description="Draft clinical impression")
    clinical_indication: Optional[str] = Field(None, description="Referral clinical indication")


class ReportDraftResponse(BaseModel):
    status: str
    report_id: str
    work_item_id: str
    version_number: int
    author_id: str
    structured_findings: Dict[str, Any]
    impression: str
    is_signed: bool
    message: str


# =============================================================================
# 1. GET /api/v1/work-items: Paginated & Filtered Worklist
# =============================================================================
@router.get(
    "",
    response_model=WorkItemListResponse,
    summary="List paginated radiology worklist items with filters",
)
async def list_work_items(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    modality: Optional[str] = Query(None, description="Filter by modality (CT, MRI, XRAY)"),
    priority: Optional[str] = Query(None, description="Filter by priority (STAT, URGENT, ROUTINE)"),
    status: Optional[str] = Query(None, description="Filter by work item state"),
    assigned_radiologist_id: Optional[str] = Query(None, description="Filter by assigned clinician"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> WorkItemListResponse:
    all_items: List[WorkItem] = []

    # 1. Fetch from database if connected
    try:
        async with AsyncSessionLocal() as session:
            repo = WorkItemRepository(session)
            db_items, _ = await repo.filter_worklist(
                modality=modality,
                priority=priority,
                status=status,
                assigned_radiologist_id=assigned_radiologist_id,
                skip=skip,
                limit=limit,
            )
            all_items.extend(db_items)
    except Exception as db_err:
        logger.debug(f"Database query skipped in list_work_items: {db_err}")

    # 2. Add in-memory items
    seen_ids = {item.work_item_id for item in all_items}
    for item in IN_MEMORY_WORK_ITEMS.values():
        if item.work_item_id not in seen_ids:
            # Apply memory filters
            if modality:
                study = IN_MEMORY_STUDIES.get(item.study_id)
                if study and study.modality.value.upper() != modality.upper():
                    continue
            if priority and item.priority.value.upper() != priority.upper():
                continue
            if status and item.state.value.lower() != status.lower():
                continue
            if assigned_radiologist_id and item.assigned_radiologist_id != assigned_radiologist_id:
                continue
            all_items.append(item)

    # Sort by priority order (STAT > URGENT > ROUTINE) and deadline
    priority_order = {"STAT": 0, "URGENT": 1, "ROUTINE": 2}
    all_items.sort(key=lambda w: (priority_order.get(w.priority.value, 3), w.sla_deadline))

    total = len(all_items)
    paginated = all_items[skip : skip + limit]

    result_dtos = []
    for w in paginated:
        study = IN_MEMORY_STUDIES.get(w.study_id)
        mod = study.modality.value if study else "CT"
        result_dtos.append(
            WorkItemDetailDTO(
                work_item_id=w.work_item_id,
                study_id=w.study_id,
                modality=mod,
                priority=w.priority.value,
                state=w.state.value,
                assigned_radiologist_id=w.assigned_radiologist_id,
                sla_deadline=w.sla_deadline.isoformat(),
                version=w.version,
                created_at=w.created_at.isoformat(),
                updated_at=w.updated_at.isoformat(),
            )
        )

    return WorkItemListResponse(
        items=result_dtos,
        total_count=total,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# 2. GET /api/v1/work-items/{id}: Detail View + Case Concierge AI Summary
# =============================================================================
@router.get(
    "/{work_item_id}",
    response_model=WorkItemDetailDTO,
    summary="Get work item detail with Case Concierge AI summary",
)
async def get_work_item(
    work_item_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> WorkItemDetailDTO:
    work_item = IN_MEMORY_WORK_ITEMS.get(work_item_id)
    if not work_item:
        try:
            async with AsyncSessionLocal() as session:
                repo = WorkItemRepository(session)
                work_item = await repo.get_by_id(work_item_id)
        except Exception:
            pass

    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WorkItem '{work_item_id}' not found.",
        )

    study = IN_MEMORY_STUDIES.get(work_item.study_id)
    modality = study.modality.value if study else "CT"
    patient_id = (study.patient_id.value if hasattr(study.patient_id, "value") else str(study.patient_id)) if study else "PAT-DEFAULT"

    # Prepare Case Concierge AI Summary
    concierge_data = None
    try:
        brief = await case_concierge.prepare_case_brief(
            patient_id=str(patient_id),
            study_id=work_item.study_id,
            modality=modality,
            work_item_id=work_item.work_item_id,
        )
        concierge_data = {
            "referral_question": brief.referral_question,
            "clinical_alerts": brief.clinical_alerts,
            "relevant_priors_summary": brief.relevant_priors_summary,
            "patient_context_summary": brief.patient_context_summary,
            "sla_risk_explanation": brief.sla_risk_explanation,
            "concierge_brief_markdown": brief.concierge_brief_markdown,
        }
    except Exception as e:
        logger.warning(f"Could not generate Concierge brief: {e}")

    return WorkItemDetailDTO(
        work_item_id=work_item.work_item_id,
        study_id=work_item.study_id,
        modality=modality,
        priority=work_item.priority.value,
        state=work_item.state.value,
        assigned_radiologist_id=work_item.assigned_radiologist_id,
        sla_deadline=work_item.sla_deadline.isoformat(),
        version=work_item.version,
        created_at=work_item.created_at.isoformat(),
        updated_at=work_item.updated_at.isoformat(),
        concierge_brief=concierge_data,
    )


# =============================================================================
# 3. GET /api/v1/work-items/{id}/explainability: SHAP Attribution Metrics
# =============================================================================
@router.get(
    "/{work_item_id}/explainability",
    summary="Fetch SHAP feature attribution metrics for SLA turnaround risk",
)
async def get_work_item_explainability(
    work_item_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> Dict[str, Any]:
    try:
        explanation = compute_sla_risk_explanation.invoke({"work_item_id": work_item_id})
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute SHAP explanation: {e}",
        )


# =============================================================================
# 4. POST /api/v1/work-items/{id}/assignments: Assign / Reassign Study
# =============================================================================
@router.post(
    "/{work_item_id}/assignments",
    response_model=WorkItemDetailDTO,
    summary="Assign or reassign study with reason code",
)
async def assign_work_item(
    work_item_id: str,
    payload: AssignmentRequest,
    current_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_roles(
                UserRole.RADIOLOGY_DIRECTOR,
                UserRole.COORDINATOR,
                UserRole.ADMINISTRATOR,
                UserRole.REPORTING_RADIOLOGIST,
            )
        ),
    ],
) -> WorkItemDetailDTO:
    work_item = IN_MEMORY_WORK_ITEMS.get(work_item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WorkItem '{work_item_id}' not found.",
        )

    work_item.assign_to(payload.assigned_radiologist_id)

    # If work item was in ready state, transition to assigned
    if work_item.state == WorkItemState.READY:
        RadiologyStateMachine.transition(
            work_item=work_item,
            target_state=WorkItemState.ASSIGNED,
            expected_version=work_item.version,
            actor_id=current_user.user_id,
            reason=f"Assigned to {payload.assigned_radiologist_id} [{payload.reason_code}]",
        )

    work_item.updated_at = datetime.now(timezone.utc)
    IN_MEMORY_WORK_ITEMS[work_item_id] = work_item

    study = IN_MEMORY_STUDIES.get(work_item.study_id)
    modality = study.modality.value if study else "CT"

    logger.info(
        f"WorkItem '{work_item_id}' assigned to '{payload.assigned_radiologist_id}' "
        f"by '{current_user.user_id}' [Reason: {payload.reason_code}]"
    )

    return WorkItemDetailDTO(
        work_item_id=work_item.work_item_id,
        study_id=work_item.study_id,
        modality=modality,
        priority=work_item.priority.value,
        state=work_item.state.value,
        assigned_radiologist_id=work_item.assigned_radiologist_id,
        sla_deadline=work_item.sla_deadline.isoformat(),
        version=work_item.version,
        created_at=work_item.created_at.isoformat(),
        updated_at=work_item.updated_at.isoformat(),
    )


# =============================================================================
# 5. POST /api/v1/work-items/{id}/transitions: Request Workflow Transition
# =============================================================================
@router.post(
    "/{work_item_id}/transitions",
    response_model=WorkItemDetailDTO,
    summary="Request deterministic clinical workflow state transition",
)
async def transition_work_item(
    work_item_id: str,
    payload: TransitionRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> WorkItemDetailDTO:
    work_item = IN_MEMORY_WORK_ITEMS.get(work_item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WorkItem '{work_item_id}' not found.",
        )

    expected_v = payload.expected_version if payload.expected_version is not None else work_item.version

    try:
        target = WorkItemState(payload.target_state.lower())
        RadiologyStateMachine.transition(
            work_item=work_item,
            target_state=target,
            expected_version=expected_v,
            actor_id=current_user.user_id,
            reason=payload.reason or "State transition request",
        )
    except ConcurrencyVersionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ClinicalWritebackBlockedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown target state: '{payload.target_state}'",
        )

    study = IN_MEMORY_STUDIES.get(work_item.study_id)
    modality = study.modality.value if study else "CT"

    return WorkItemDetailDTO(
        work_item_id=work_item.work_item_id,
        study_id=work_item.study_id,
        modality=modality,
        priority=work_item.priority.value,
        state=work_item.state.value,
        assigned_radiologist_id=work_item.assigned_radiologist_id,
        sla_deadline=work_item.sla_deadline.isoformat(),
        version=work_item.version,
        created_at=work_item.created_at.isoformat(),
        updated_at=work_item.updated_at.isoformat(),
    )


# =============================================================================
# 6. POST /api/v1/work-items/{id}/report-drafts: Create / Update Report Draft
# =============================================================================
@router.post(
    "/{work_item_id}/report-drafts",
    response_model=ReportDraftResponse,
    summary="Create or update preliminary report draft using Deep Agents",
)
async def create_report_draft(
    work_item_id: str,
    payload: ReportDraftRequest,
    current_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_roles(
                UserRole.REPORTING_RADIOLOGIST,
                UserRole.RADIOLOGY_RESIDENT,
                UserRole.RADIOLOGY_DIRECTOR,
            )
        ),
    ],
) -> ReportDraftResponse:
    work_item = IN_MEMORY_WORK_ITEMS.get(work_item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WorkItem '{work_item_id}' not found.",
        )

    # Verify writeback invariant
    RadiologyStateMachine.validate_clinical_writeback_allowed(work_item)

    # Call Deep Agents report draft tool
    draft_dict = draft_structured_report.invoke({
        "work_item_id": work_item_id,
        "findings": payload.findings,
        "impression": payload.impression,
    })

    # Register draft in in-memory repository
    seed_in_memory_report(
        report_id=draft_dict["report_id"],
        work_item_id=work_item_id,
        version_number=draft_dict["version_number"],
        findings=payload.findings,
        impression=payload.impression,
        is_signed=False,
    )

    # Persist report draft to database if available
    try:
        async with AsyncSessionLocal() as session:
            r_repo = ReportRepository(session)
            db_report = Report(
                report_id=draft_dict["report_id"],
                work_item_id=work_item_id,
                status=ReportStatus.DRAFT,
            )
            await r_repo.create(db_report)
            v1 = ReportVersion(
                version_number=draft_dict["version_number"],
                structured_findings={"narrative": payload.findings},
                impression=payload.impression,
                author_id=current_user.user_id,
            )
            await r_repo.save_version(draft_dict["report_id"], v1)
            await session.commit()
    except Exception as db_err:
        logger.debug(f"DB draft persistence skipped: {db_err}")

    # Advance state to DRAFT_READY if in_progress or assigned
    if work_item.state in (WorkItemState.ASSIGNED, WorkItemState.IN_PROGRESS):
        if work_item.state == WorkItemState.ASSIGNED:
            work_item.state = WorkItemState.IN_PROGRESS
        RadiologyStateMachine.transition(
            work_item=work_item,
            target_state=WorkItemState.DRAFT_READY,
            expected_version=work_item.version,
            actor_id=current_user.user_id,
            reason="AI Report draft generated",
        )

    return ReportDraftResponse(
        status=draft_dict["status"],
        report_id=draft_dict["report_id"],
        work_item_id=draft_dict["work_item_id"],
        version_number=draft_dict["version_number"],
        author_id=current_user.user_id,
        structured_findings=draft_dict["structured_findings"],
        impression=draft_dict["impression"],
        is_signed=draft_dict["is_signed"],
        message=draft_dict["message"],
    )
