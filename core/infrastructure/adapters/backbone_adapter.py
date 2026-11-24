"""
BackBone HMS Adapter (Clean Architecture).
Interfaces for study/worklist ingestion, order reconciliation, and out-of-order event handling.
Enforces RULE-01 authoritative patient identification and robust error recovery.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid
import httpx

from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.study import Modality, RadiologyStudy, StudyLifecycleState
from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.domain.exceptions import PatientMismatchError
from core.infrastructure.adapters.exceptions import (
    BackBoneHMSConnectionError,
    MissingAccessionNumberError,
    OutOfOrderEventError,
)

logger = logging.getLogger("sims_radiology.adapters.backbone")


@dataclass
class OrderReconciliationResult:
    """Outcome of order and patient reconciliation between HMS and PACS."""
    status: ReconciliationStatus
    is_reconciled: bool
    accession_number: str
    mrn: str
    namespace: str
    study_id: Optional[str] = None
    discrepancy_reasons: List[str] = field(default_factory=list)


class BackBoneHMSAdapter:
    """
    BackBone Hospital Management System (HMS) Adapter.
    Handles clinical orders, study scheduling, worklist ingestion, and HL7/FHIR reconciliation.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8081/api/hms/v1",
        timeout: float = 8.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # In-memory buffer for sequencing out-of-order events
        self._processed_events: Dict[str, datetime] = {}
        self._buffered_events: Dict[str, List[Dict[str, Any]]] = {}

    def ingest_order(
        self,
        order_payload: Dict[str, Any],
    ) -> Tuple[RadiologyStudy, WorkItem, Patient]:
        """
        Ingest a clinical order from BackBone HMS and convert to domain entities.
        Enforces validation for Accession Number and RULE-01 for Patient.
        """
        # 1. Accession Number Validation
        accession = order_payload.get("accession_number") or order_payload.get("accession")
        if not accession or not str(accession).strip():
            logger.error("Order ingestion rejected: Accession Number is missing.")
            raise MissingAccessionNumberError(
                "Accession Number is required for BackBone HMS order ingestion."
            )
        accession = str(accession).strip()

        # 2. Extract & Validate Patient (RULE-01)
        patient_info = order_payload.get("patient", {})
        mrn = patient_info.get("mrn") or order_payload.get("patient_mrn")
        namespace = (
            patient_info.get("namespace")
            or order_payload.get("identifier_namespace")
            or "urn:oid:sims:hospital:mrn"
        )
        patient_id = patient_info.get("id") or order_payload.get("patient_id") or f"PAT-{mrn}"

        if not mrn or not str(mrn).strip():
            logger.warning(f"Order '{accession}' missing authoritative MRN. Flagging reconciliation required.")
            reconciliation_status = ReconciliationStatus.RECONCILIATION_REQUIRED
            mrn = f"UNRECONCILED-{accession}"
        else:
            reconciliation_status = ReconciliationStatus.RECONCILED

        patient = Patient(
            patient_id=str(patient_id),
            mrn=str(mrn),
            identifier_namespace=str(namespace),
            reconciliation_status=reconciliation_status,
            family_name=patient_info.get("family_name") or patient_info.get("last_name"),
            given_name=patient_info.get("given_name") or patient_info.get("first_name"),
            birth_date=patient_info.get("birth_date") or patient_info.get("dob"),
            gender=patient_info.get("gender"),
        )

        # 3. Modality & Priority Parsing
        raw_modality = order_payload.get("modality", "CT").upper()
        try:
            modality = Modality(raw_modality)
        except ValueError:
            modality = Modality.CT

        raw_priority = str(order_payload.get("priority", "ROUTINE")).upper()
        if raw_priority in ("STAT", "EMERGENCY"):
            priority = Priority.STAT
        elif raw_priority in ("URGENT", "ASAP"):
            priority = Priority.URGENT
        else:
            priority = Priority.ROUTINE

        # 4. Construct RadiologyStudy
        study_uid = (
            order_payload.get("study_instance_uid")
            or f"1.2.840.113619.2.55.3.{uuid.uuid4().hex[:12]}"
        )
        study_id = f"STU-{accession}"
        now = datetime.now(timezone.utc)

        study = RadiologyStudy(
            study_id=study_id,
            study_instance_uid=study_uid,
            accession_number=accession,
            modality=modality,
            study_date=now,
            source_system="BACKBONE_HMS",
            patient_id=patient.patient_id,
            description=order_payload.get("exam_description", f"{modality.value} Clinical Exam"),
            state=StudyLifecycleState.RECEIVED,
        )

        # 5. Construct WorkItem
        sla_deadline = now + timedelta(minutes=priority.max_turnaround_minutes)
        requested_state = order_payload.get("initial_state") or order_payload.get("state")
        if requested_state:
            initial_state = WorkItemState(str(requested_state).lower())
        elif reconciliation_status == ReconciliationStatus.RECONCILIATION_REQUIRED:
            initial_state = WorkItemState.RECONCILIATION_REQUIRED
        else:
            initial_state = WorkItemState.READY

        work_item = WorkItem(
            work_item_id=f"WI-{accession}",
            study_id=study_id,
            state=initial_state,
            priority=priority,
            assigned_radiologist_id=order_payload.get("assigned_radiologist_id"),
            sla_deadline=sla_deadline,
            version=1,
            created_at=now,
            updated_at=now,
        )

        return study, work_item, patient

    def reconcile_order(
        self,
        accession_number: str,
        hms_patient: Patient,
        pacs_study: RadiologyStudy,
        pacs_patient: Optional[Patient] = None,
    ) -> OrderReconciliationResult:
        """
        Reconcile order data between BackBone HMS and PACS image arrival.
        Enforces RULE-01: Matching must succeed on authoritative identifier namespace + MRN.
        Never matches solely on Name or Date of Birth.
        """
        discrepancies: List[str] = []

        # 1. Accession check
        if pacs_study.accession_number != accession_number:
            discrepancies.append(
                f"Accession mismatch: HMS='{accession_number}' vs PACS='{pacs_study.accession_number}'"
            )

        # 2. Patient Authoritative Matching (RULE-01)
        if pacs_patient is not None:
            try:
                matches_rule_01 = hms_patient.match_with(
                    candidate_mrn=pacs_patient.mrn,
                    candidate_namespace=pacs_patient.identifier_namespace,
                    candidate_name=pacs_patient.family_name,
                    candidate_dob=pacs_patient.birth_date,
                )
                if not matches_rule_01:
                    discrepancies.append(
                        f"Patient RULE-01 Mismatch: HMS MRN='{hms_patient.mrn}' ({hms_patient.identifier_namespace}) "
                        f"does not match PACS MRN='{pacs_patient.mrn}' ({pacs_patient.identifier_namespace})."
                    )
            except PatientMismatchError as pme:
                discrepancies.append(f"Patient RULE-01 Mismatch: {pme}")

        if discrepancies:
            logger.warning(
                f"Reconciliation required for accession '{accession_number}': {discrepancies}"
            )
            return OrderReconciliationResult(
                status=ReconciliationStatus.RECONCILIATION_REQUIRED,
                is_reconciled=False,
                accession_number=accession_number,
                mrn=hms_patient.mrn,
                namespace=hms_patient.identifier_namespace,
                study_id=pacs_study.study_id,
                discrepancy_reasons=discrepancies,
            )

        logger.info(f"Order '{accession_number}' successfully reconciled.")
        return OrderReconciliationResult(
            status=ReconciliationStatus.RECONCILED,
            is_reconciled=True,
            accession_number=accession_number,
            mrn=hms_patient.mrn,
            namespace=hms_patient.identifier_namespace,
            study_id=pacs_study.study_id,
            discrepancy_reasons=[],
        )

    def handle_out_of_order_event(
        self,
        event_id: str,
        accession_number: str,
        event_type: str,
        event_timestamp: datetime,
        payload: Dict[str, Any],
        current_work_item: Optional[WorkItem] = None,
    ) -> Dict[str, Any]:
        """
        Handle out-of-order or duplicate HMS events gracefully.
        Examples:
        - Image arrives (PACS) before Order is created in HMS.
        - Order cancelled arrives after study is already finalized.
        - Duplicate event delivery.
        """
        # Idempotency check: Already processed event
        last_seen = self._processed_events.get(event_id)
        if last_seen is not None:
            logger.info(f"Duplicate event '{event_id}' detected for accession '{accession_number}'. Skipping.")
            return {"status": "SKIPPED_DUPLICATE", "event_id": event_id}

        # Sequence validation against current work item state
        if current_work_item is not None:
            # Case: Order update arrived when study is already finalized
            if current_work_item.state in (WorkItemState.FINALIZED, WorkItemState.DELIVERED):
                if event_type in ("ORDER_UPDATED", "ORDER_CANCELLED"):
                    logger.warning(
                        f"Out-of-order event: Cannot apply '{event_type}' to finalized work item '{current_work_item.work_item_id}'."
                    )
                    # Buffer event for audit/amendment review rather than corrupting state
                    self._buffered_events.setdefault(accession_number, []).append(payload)
                    self._processed_events[event_id] = event_timestamp
                    return {
                        "status": "BUFFERED_POST_FINALIZATION",
                        "event_id": event_id,
                        "reason": f"Study already in state '{current_work_item.state.value}'.",
                    }

        # Record processed event
        self._processed_events[event_id] = event_timestamp
        return {"status": "APPLIED", "event_id": event_id}

    async def fetch_order_details(self, accession_number: str) -> Dict[str, Any]:
        """
        Fetch clinical order details from BackBone HMS API.
        Handles vendor outages by raising retriable BackBoneHMSConnectionError.
        """
        url = f"{self.base_url}/orders/{accession_number}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url)
                if res.status_code in (502, 503, 504):
                    raise BackBoneHMSConnectionError(
                        f"BackBone HMS unavailable with status {res.status_code}",
                        status_code=res.status_code,
                    )
                res.raise_for_status()
                return res.json()
        except httpx.TimeoutException as te:
            raise BackBoneHMSConnectionError(f"BackBone HMS request timed out: {te}") from te
        except httpx.NetworkError as ne:
            raise BackBoneHMSConnectionError(f"BackBone HMS network connection failure: {ne}") from ne
        except BackBoneHMSConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch order from HMS: {e}", exc_info=True)
            raise BackBoneHMSConnectionError(f"HMS communication error: {e}") from e
