"""
Database Seed Script: Populates synthetic CT, MRI, and X-Ray studies and clinical work items.
Adheres strictly to SIMS Radiology enterprise domain rules and models.
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.infrastructure.config import settings
from core.infrastructure.persistence.models import (
    PatientModel,
    StudyModel,
    WorkItemModel,
    ReportModel,
    ReportVersionModel,
    AuditEventModel,
    OutboxEventModel,
)
from core.domain.entities.study import Modality
from core.domain.entities.work_item import Priority
from core.domain.state_machine import WorkItemState


async def seed_synthetic_data() -> None:
    """Populates PostgreSQL with realistic synthetic radiology clinical data."""
    print("🌱 Connecting to database for synthetic seeding...")
    engine = create_async_engine(str(settings.POSTGRES_DSN), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(timezone.utc)

    async with async_session() as session:
        async with session.begin():
            # 1. Patients
            patients = [
                PatientModel(
                    id="PAT-001",
                    mrn="MRN-100234",
                    identifier_namespace="urn:oid:sims:hospital:mrn",
                    reconciliation_status="RECONCILED",
                    given_name="Eleanor",
                    family_name="Vance",
                    birth_date="1975-04-12",
                    gender="female",
                    created_at=now - timedelta(days=2),
                ),
                PatientModel(
                    id="PAT-002",
                    mrn="MRN-100567",
                    identifier_namespace="urn:oid:sims:hospital:mrn",
                    reconciliation_status="RECONCILED",
                    given_name="Arthur",
                    family_name="Pendelton",
                    birth_date="1988-09-23",
                    gender="male",
                    created_at=now - timedelta(days=1),
                ),
                PatientModel(
                    id="PAT-003",
                    mrn="MRN-100890",
                    identifier_namespace="urn:oid:sims:hospital:mrn",
                    reconciliation_status="PENDING",
                    given_name="Clara",
                    family_name="Oswin",
                    birth_date="1992-11-05",
                    gender="female",
                    created_at=now - timedelta(hours=6),
                ),
            ]
            for p in patients:
                await session.merge(p)

            # 2. Studies (CT, MRI, XRAY)
            studies = [
                # CT Head / Brain - STAT (Emergency)
                StudyModel(
                    id="STU-CT-001",
                    study_instance_uid="1.2.840.113619.2.55.3.1001.20261124.01",
                    accession_number="ACC-CT-9901",
                    patient_id="PAT-001",
                    modality=Modality.CT.value,
                    study_date=now - timedelta(hours=2),
                    source_system="PACS_GE_REVOLUTION_CT",
                    created_at=now - timedelta(hours=2),
                ),
                # MRI Lumbar Spine - URGENT
                StudyModel(
                    id="STU-MRI-002",
                    study_instance_uid="1.2.840.113619.2.55.3.1002.20261124.02",
                    accession_number="ACC-MR-4412",
                    patient_id="PAT-002",
                    modality=Modality.MRI.value,
                    study_date=now - timedelta(hours=5),
                    source_system="PACS_SIEMENS_SOLA_MRI",
                    created_at=now - timedelta(hours=5),
                ),
                # Chest X-Ray - ROUTINE
                StudyModel(
                    id="STU-XRAY-003",
                    study_instance_uid="1.2.840.113619.2.55.3.1003.20261124.03",
                    accession_number="ACC-XR-7731",
                    patient_id="PAT-003",
                    modality=Modality.XRAY.value,
                    study_date=now - timedelta(hours=8),
                    source_system="PACS_PHILIPS_DIGITAL_XR",
                    created_at=now - timedelta(hours=8),
                ),
            ]
            for s in studies:
                await session.merge(s)

            # 3. Work Items
            work_items = [
                # CT Work Item (STAT priority, Draft ready)
                WorkItemModel(
                    id="WI-CT-001",
                    study_id="STU-CT-001",
                    state=WorkItemState.DRAFT_READY.value,
                    priority=Priority.STAT.value,
                    assigned_radiologist_id="RAD-DOC-42",
                    sla_deadline=now + timedelta(minutes=45),
                    version=3,
                    created_at=now - timedelta(hours=2),
                    updated_at=now - timedelta(minutes=15),
                ),
                # MRI Work Item (URGENT priority, Assigned)
                WorkItemModel(
                    id="WI-MRI-002",
                    study_id="STU-MRI-002",
                    state=WorkItemState.ASSIGNED.value,
                    priority=Priority.URGENT.value,
                    assigned_radiologist_id="RAD-DOC-18",
                    sla_deadline=now + timedelta(hours=4),
                    version=2,
                    created_at=now - timedelta(hours=5),
                    updated_at=now - timedelta(hours=1),
                ),
                # X-Ray Work Item (ROUTINE priority, Ready for assignment)
                WorkItemModel(
                    id="WI-XRAY-003",
                    study_id="STU-XRAY-003",
                    state=WorkItemState.READY.value,
                    priority=Priority.ROUTINE.value,
                    assigned_radiologist_id=None,
                    sla_deadline=now + timedelta(hours=24),
                    version=1,
                    created_at=now - timedelta(hours=8),
                    updated_at=now - timedelta(hours=8),
                ),
            ]
            for wi in work_items:
                await session.merge(wi)

            # 4. Reports & Immutable Report Versions
            report_ct = ReportModel(
                id="REP-CT-001",
                work_item_id="WI-CT-001",
                status="DRAFT",
                current_version_id="VER-CT-001-v1",
                created_at=now - timedelta(minutes=20),
                updated_at=now - timedelta(minutes=15),
            )
            await session.merge(report_ct)

            rep_version_ct = ReportVersionModel(
                id="VER-CT-001-v1",
                report_id="REP-CT-001",
                version_number=1,
                structured_findings={
                    "technique": "Axial non-contrast CT brain reconstruction with multiplanar reformats.",
                    "findings": [
                        {"organ": "Brain Parenchyma", "description": "No acute intracranial hemorrhage or territorial infarction."},
                        {"organ": "Ventricles", "description": "Ventricles and basal cisterns are symmetric and normal in caliber for age."},
                        {"organ": "Calvarium", "description": "No calvarial fracture detected."}
                    ],
                    "ai_findings": {
                        "hemorrhage_probability": 0.002,
                        "midline_shift_mm": 0.0,
                        "dense_mca_sign": False
                    }
                },
                impression="Normal non-contrast head CT. No acute intracranial abnormality detected.",
                author_id="RAD-AGENT-NEURO",
                signature_hash="sha256_mock_hash_eleanor_vance_ct_001",
                signed_at=now - timedelta(minutes=15),
                created_at=now - timedelta(minutes=15),
            )
            await session.merge(rep_version_ct)

            # 5. Outbox Events & Audit Events
            outbox_events = [
                OutboxEventModel(
                    id=str(uuid.uuid4()),
                    aggregate_type="study",
                    aggregate_id="STU-CT-001",
                    event_type="study.ingested",
                    payload={
                        "study_instance_uid": "1.2.840.113619.2.55.3.1001.20261124.01",
                        "accession_number": "ACC-CT-9901",
                        "modality": "CT",
                        "priority": "STAT",
                    },
                    created_at=now - timedelta(hours=2),
                    processed_at=now - timedelta(hours=2),
                ),
                OutboxEventModel(
                    id=str(uuid.uuid4()),
                    aggregate_type="work_item",
                    aggregate_id="WI-CT-001",
                    event_type="work_item.draft_ready",
                    payload={
                        "work_item_id": "WI-CT-001",
                        "study_id": "STU-CT-001",
                        "report_id": "REP-CT-001",
                        "version": 1,
                    },
                    created_at=now - timedelta(minutes=15),
                    processed_at=None,  # Pending outbox event for worker verification
                ),
            ]
            for oe in outbox_events:
                await session.merge(oe)

            audit_events = [
                AuditEventModel(
                    id=str(uuid.uuid4()),
                    actor_id="INGESTION_SERVICE",
                    action="INGEST_STUDY",
                    resource_id="STU-CT-001",
                    correlation_id="corr-9901-seed",
                    details={"status": "SUCCESS", "modality": "CT"},
                    timestamp=now - timedelta(hours=2),
                ),
                AuditEventModel(
                    id=str(uuid.uuid4()),
                    actor_id="RAD-AGENT-NEURO",
                    action="DRAFT_REPORT",
                    resource_id="REP-CT-001",
                    correlation_id="corr-9901-draft",
                    details={"version": 1, "status": "DRAFT_READY"},
                    timestamp=now - timedelta(minutes=15),
                ),
            ]
            for ae in audit_events:
                await session.merge(ae)

    await engine.dispose()
    print("✅ Synthetic CT, MRI, and X-Ray studies and work items seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_synthetic_data())
