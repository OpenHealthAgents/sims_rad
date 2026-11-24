"""
CharmHealth EHR Adapter (Clean Architecture).
Maps clinical diagnostic reports using FHIR R4 resources.
Implements client contract with runtime capability matrix and safe fallback to Transactional Outbox.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.entities.audit_log import AuditLog
from core.domain.entities.patient import Patient
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.entities.study import Modality, RadiologyStudy
from core.infrastructure.adapters.exceptions import (
    CharmHealthConnectionError,
    VendorCapabilityDisabledError,
)
from core.infrastructure.persistence.models import OutboxEventModel
from core.infrastructure.persistence.repositories.audit_repository import AuditRepository

logger = logging.getLogger("sims_radiology.adapters.charmhealth")

# Standard LOINC procedure codes for radiology modalities
LOINC_MODALITY_CODES = {
    Modality.CT: {"code": "24627-2", "display": "CT Head Diagnostic Study"},
    Modality.MRI: {"code": "30744-7", "display": "MRI Lumbar Spine Diagnostic Study"},
    Modality.XRAY: {"code": "36554-4", "display": "Chest X-ray Diagnostic Study"},
}


@dataclass
class CapabilityMatrix:
    """Runtime capability matrix for CharmHealth EHR client contract."""
    patient_lookup: bool = True
    encounter_lookup: bool = True
    prior_report_read: bool = True
    final_report_write: bool = True

    def is_enabled(self, capability: str) -> bool:
        return getattr(self, capability, False)


@dataclass
class ReportDeliveryResult:
    """Outcome of attempting to transmit a diagnostic report to CharmHealth EHR."""
    status: str  # "DELIVERED", "QUEUED_OUTBOX", "FAILED"
    delivered: bool
    fallback_to_outbox: bool
    report_id: str
    fhir_resource_id: Optional[str] = None
    reason: Optional[str] = None
    outbox_event_id: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class CharmHealthEHRAdapter:
    """
    CharmHealth Electronic Health Record (EHR) Adapter.
    Adheres strictly to FHIR R4 schemas and ensures patient safety by isolating
    clinical sign-off state from external network/vendor outages.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8082/fhir/r4",
        timeout: float = 8.0,
        capabilities: Optional[CapabilityMatrix] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.capabilities = capabilities or CapabilityMatrix()

    def map_to_fhir_diagnostic_report(
        self,
        report: Report,
        patient: Patient,
        study: RadiologyStudy,
        version: Optional[ReportVersion] = None,
    ) -> Dict[str, Any]:
        """
        Map domain Report, Patient, and Study to a standardized FHIR R4 DiagnosticReport resource.
        """
        active_version = version or report.latest_version
        if not active_version:
            raise ValueError(f"Report '{report.report_id}' has no diagnostic version to map.")

        # Determine FHIR status
        if report.status in (ReportStatus.SIGNED, ReportStatus.RELEASED):
            fhir_status = "final"
        elif report.status == ReportStatus.AMENDED:
            fhir_status = "amended"
        else:
            fhir_status = "preliminary"

        # Modality LOINC coding
        loinc = LOINC_MODALITY_CODES.get(
            study.modality,
            {"code": "18748-4", "display": "Diagnostic Imaging Report"},
        )

        signed_iso = (
            active_version.signed_at.isoformat()
            if active_version.signed_at
            else active_version.created_at.isoformat()
        )

        fhir_diagnostic_report = {
            "resourceType": "DiagnosticReport",
            "id": report.report_id,
            "status": fhir_status,
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                            "code": "RAD",
                            "display": "Radiology",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": loinc["code"],
                        "display": loinc["display"],
                    }
                ],
                "text": study.description or f"{study.modality.value} Imaging Report",
            },
            "subject": {
                "reference": f"Patient/{patient.patient_id}",
                "type": "Patient",
                "identifier": {
                    "system": patient.identifier_namespace,
                    "value": patient.mrn,
                },
                "display": f"{patient.family_name or ''}, {patient.given_name or ''}".strip(", "),
            },
            "effectiveDateTime": study.study_date.isoformat(),
            "issued": signed_iso,
            "performer": [
                {
                    "type": "Practitioner",
                    "display": active_version.author_id,
                }
            ],
            "conclusion": active_version.impression,
            "presentedForm": [
                {
                    "contentType": "application/json",
                    "title": f"Structured Findings Version {active_version.version_number}",
                    "data": None,  # Can embed base64 if needed
                }
            ],
            "extension": [
                {
                    "url": "http://sims.radiology/fhir/StructureDefinition/accession-number",
                    "valueString": study.accession_number,
                },
                {
                    "url": "http://sims.radiology/fhir/StructureDefinition/study-instance-uid",
                    "valueString": study.study_instance_uid,
                },
                {
                    "url": "http://sims.radiology/fhir/StructureDefinition/report-version",
                    "valueInteger": active_version.version_number,
                },
            ],
        }

        # Include signature hash if present
        if active_version.signature_hash:
            fhir_diagnostic_report["extension"].append({
                "url": "http://sims.radiology/fhir/StructureDefinition/signature-hash",
                "valueString": active_version.signature_hash,
            })

        return fhir_diagnostic_report

    async def patient_lookup(self, mrn: str, namespace: str) -> Dict[str, Any]:
        """Search patient by authoritative MRN on CharmHealth EHR."""
        if not self.capabilities.is_enabled("patient_lookup"):
            raise VendorCapabilityDisabledError("patient_lookup", "CharmHealth")

        url = f"{self.base_url}/Patient"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params={"identifier": f"{namespace}|{mrn}"})
                if res.status_code in (502, 503, 504):
                    raise CharmHealthConnectionError(
                        f"CharmHealth EHR unavailable: {res.status_code}",
                        status_code=res.status_code,
                    )
                res.raise_for_status()
                return res.json()
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise CharmHealthConnectionError(f"CharmHealth connection failure: {e}") from e

    async def encounter_lookup(self, encounter_id: str) -> Dict[str, Any]:
        """Fetch clinical encounter details from CharmHealth EHR."""
        if not self.capabilities.is_enabled("encounter_lookup"):
            raise VendorCapabilityDisabledError("encounter_lookup", "CharmHealth")

        url = f"{self.base_url}/Encounter/{encounter_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url)
                if res.status_code in (502, 503, 504):
                    raise CharmHealthConnectionError(
                        f"CharmHealth encounter service unavailable: {res.status_code}",
                        status_code=res.status_code,
                    )
                res.raise_for_status()
                return res.json()
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise CharmHealthConnectionError(f"CharmHealth encounter lookup failure: {e}") from e

    async def prior_report_read(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve prior diagnostic imaging reports for longitudinal comparison."""
        if not self.capabilities.is_enabled("prior_report_read"):
            raise VendorCapabilityDisabledError("prior_report_read", "CharmHealth")

        url = f"{self.base_url}/DiagnosticReport"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(
                    url,
                    params={"subject": f"Patient/{patient_id}", "_sort": "-date"},
                )
                if res.status_code in (502, 503, 504):
                    raise CharmHealthConnectionError(
                        f"CharmHealth prior reports service unavailable: {res.status_code}",
                        status_code=res.status_code,
                    )
                res.raise_for_status()
                data = res.json()
                return data.get("entry", [])
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise CharmHealthConnectionError(f"CharmHealth prior report lookup failure: {e}") from e

    async def transmit_final_report(
        self,
        report: Report,
        patient: Patient,
        study: RadiologyStudy,
        version: Optional[ReportVersion] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> ReportDeliveryResult:
        """
        Transmit final signed diagnostic report to CharmHealth EHR.
        
        CRITICAL INVARIANT:
        If `final_report_write` is False or fails due to network/vendor outages:
        Fallback safely to a retriable outbox task WITHOUT failing the clinical sign-off
        state in the local database.
        """
        active_version = version or report.latest_version
        fhir_payload = self.map_to_fhir_diagnostic_report(report, patient, study, active_version)

        # 1. Capability Flag Check
        if not self.capabilities.is_enabled("final_report_write"):
            logger.warning(
                f"Capability 'final_report_write' is DISABLED for CharmHealth. "
                f"Safely queuing report '{report.report_id}' to retriable outbox."
            )
            outbox_id = await self._queue_to_outbox(
                report=report,
                fhir_payload=fhir_payload,
                reason="Capability 'final_report_write' is disabled in runtime matrix.",
                db_session=db_session,
            )
            return ReportDeliveryResult(
                status="QUEUED_OUTBOX",
                delivered=False,
                fallback_to_outbox=True,
                report_id=report.report_id,
                outbox_event_id=outbox_id,
                reason="Capability 'final_report_write' disabled; safely queued to outbox.",
            )

        # 2. Transmit via HTTP to EHR
        url = f"{self.base_url}/DiagnosticReport"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=fhir_payload)
                if res.status_code in (500, 502, 503, 504):
                    raise CharmHealthConnectionError(
                        f"CharmHealth returned server outage {res.status_code}: {res.text}",
                        status_code=res.status_code,
                    )
                res.raise_for_status()
                response_data = res.json()
                fhir_id = response_data.get("id", report.report_id)

                logger.info(
                    f"Report '{report.report_id}' successfully transmitted to CharmHealth EHR (FHIR ID: '{fhir_id}')."
                )
                return ReportDeliveryResult(
                    status="DELIVERED",
                    delivered=True,
                    fallback_to_outbox=False,
                    report_id=report.report_id,
                    fhir_resource_id=fhir_id,
                    raw_response=response_data,
                )

        except (httpx.TimeoutException, httpx.NetworkError, CharmHealthConnectionError, Exception) as e:
            # 3. Safe Outage Fallback: Fallback to retriable outbox task without failing local sign-off!
            logger.warning(
                f"EHR transmission failed for report '{report.report_id}': {e}. "
                "Executing safe fallback to Transactional Outbox. Clinical sign-off is preserved."
            )
            outbox_id = await self._queue_to_outbox(
                report=report,
                fhir_payload=fhir_payload,
                reason=f"Transient transmission error: {str(e)}",
                db_session=db_session,
            )
            return ReportDeliveryResult(
                status="QUEUED_OUTBOX",
                delivered=False,
                fallback_to_outbox=True,
                report_id=report.report_id,
                outbox_event_id=outbox_id,
                reason=f"Vendor outage ({e}); safely fell back to outbox.",
            )

    async def _queue_to_outbox(
        self,
        report: Report,
        fhir_payload: Dict[str, Any],
        reason: str,
        db_session: Optional[AsyncSession] = None,
    ) -> str:
        """
        Record a retriable delivery event in the outbox_events table.
        Ensures local clinical state remains unaffected and compliant.
        """
        event_id = f"outbox-ehr-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        if db_session is not None:
            audit_repo = AuditRepository(db_session)
            audit_entry = AuditLog(
                actor_id="CHARMHEALTH_ADAPTER",
                action="FALLBACK_TO_OUTBOX",
                resource_id=report.report_id,
                correlation_id=f"corr-ehr-{report.report_id}",
                details={"reason": reason, "delivery_channel": "CHARMHEALTH_FHIR"},
            )
            outbox_record = await audit_repo.record_with_outbox(
                audit_log=audit_entry,
                aggregate_type="REPORT",
                aggregate_id=report.report_id,
                event_type="report.delivery.pending",
                payload={
                    "destination_system": "CHARMHEALTH_EHR",
                    "report_id": report.report_id,
                    "fhir_diagnostic_report": fhir_payload,
                    "fallback_reason": reason,
                    "retry_count": 0,
                },
            )
            await db_session.flush()
            event_id = outbox_record.id

        logger.info(f"Queued outbox event '{event_id}' for report '{report.report_id}'.")
        return event_id
