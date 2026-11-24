"""
SQLAlchemy 2.0 Async Persistence Models for the SIMS Radiology Platform.

Architecture Overview:
    Follows Clean Architecture and Domain-Driven Design (DDD) persistence patterns.
    These models define the relational mappings for PostgreSQL 16 using SQLAlchemy 2.0
    `Mapped` and `mapped_column` type annotations.

Key Database Invariants:
    1. Append-Only Report Versions:
       The `report_versions` table is strictly append-only. Rows represent immutable historical
       snapshots of diagnostic findings and impressions. Both SQLAlchemy ORM listeners
       (`before_update`, `before_delete`) and PostgreSQL database triggers prevent any modification
       or removal of existing versions once written.
    2. Transactional Outbox:
       The `outbox_events` table captures domain events in the same database transaction as the
       aggregate mutations. Background Celery workers poll and publish these events to Kestra
       pipelines and external EHR adapters using `FOR UPDATE SKIP LOCKED`.
    3. Multi-Tenant Referential Integrity:
       Cascade rules protect study, work item, report, and version relationships.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from core.domain.exceptions import ImmutableReportOverrideError


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 declarative models in SIMS Radiology."""
    pass


def get_utc_now() -> datetime:
    """Helper returning current timestamp in UTC timezone."""
    return datetime.now(timezone.utc)


class PatientModel(Base):
    """
    Relational persistence model for clinical patients.

    Table: `patients`
    Attributes:
        id (str): Primary key UUID representing the internal patient record.
        mrn (str): Medical Record Number issued by the hospital EHR/HMS (unique).
        identifier_namespace (str): System URI / authority that issued the MRN.
        reconciliation_status (str): Current reconciliation state (pending, reconciled, reconciliation_required).
        family_name (Optional[str]): Patient surname (subject to HIPAA scrubbing in external traces).
        given_name (Optional[str]): Patient first name (subject to HIPAA scrubbing).
        birth_date (Optional[str]): Patient date of birth in ISO YYYY-MM-DD format.
        gender (Optional[str]): Administrative sex code ('M', 'F', 'O', 'U').
        created_at (datetime): Record creation timestamp in UTC.
        updated_at (datetime): Record last modification timestamp in UTC.
        studies (List[StudyModel]): One-to-many relationship with imaging studies.
    """
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mrn: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    identifier_namespace: Mapped[str] = mapped_column(String(255), nullable=False)
    reconciliation_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    family_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    given_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    birth_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    studies: Mapped[List["StudyModel"]] = relationship(
        "StudyModel", back_populates="patient", cascade="all, delete-orphan"
    )


class StudyModel(Base):
    """
    Relational persistence model for radiology imaging studies.

    Table: `studies`
    Attributes:
        id (str): Internal surrogate primary key UUID.
        study_instance_uid (str): Globally unique DICOM Study Instance UID (ISO/IEC 8824 standard).
        accession_number (str): Order accession number assigned by the hospital ordering system.
        patient_id (str): Foreign key reference to `patients.id`.
        modality (str): Imaging modality code (e.g. 'CT', 'MR', 'XR', 'US', 'NM').
        study_date (datetime): Acquisition timestamp from the DICOM header.
        source_system (str): Originating imaging system or PACS archive identifier.
        description (str): Procedure description (e.g. 'CT Chest with IV Contrast').
        priority (str): Clinical urgency priority ('STAT', 'URGENT', 'ROUTINE').
        state (str): Workflow lifecycle status of the study.
        storage_path (Optional[str]): Object storage URI or archive path for DICOM instances.
        created_at (datetime): Database record insertion timestamp.
        updated_at (datetime): Last update timestamp.
        patient (PatientModel): Parent patient relation.
        work_items (List[WorkItemModel]): Worklist operational items linked to this study.
    """
    __tablename__ = "studies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_instance_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    accession_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    modality: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    study_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), default="PACS-DEFAULT", nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    priority: Mapped[str] = mapped_column(String(16), default="ROUTINE", index=True)
    state: Mapped[str] = mapped_column(String(32), default="received", index=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    patient: Mapped["PatientModel"] = relationship("PatientModel", back_populates="studies")
    work_items: Mapped[List["WorkItemModel"]] = relationship(
        "WorkItemModel", back_populates="study", cascade="all, delete-orphan"
    )


class WorkItemModel(Base):
    """
    Operational worklist item model representing a task in the reading queue.

    Table: `work_items`
    Attributes:
        id (str): Primary key work item UUID.
        study_id (str): Foreign key reference to `studies.id`.
        state (str): Current deterministic state machine status (e.g. 'ready', 'assigned', 'draft_ready').
        priority (str): Triage urgency level determining SLA target.
        assigned_radiologist_id (Optional[str]): Clinician ID currently assigned to interpret the study.
        sla_deadline (Optional[datetime]): Target completion deadline in UTC.
        version (int): Optimistic locking concurrency token incremented on each transition.
        created_at (datetime): Work item creation timestamp.
        updated_at (datetime): Last modification timestamp.
        study (StudyModel): Associated imaging study entity.
        report (Optional[ReportModel]): Linked diagnostic report aggregate.
    """
    __tablename__ = "work_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), default="received", index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="ROUTINE", index=True, nullable=False)
    assigned_radiologist_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    study: Mapped["StudyModel"] = relationship("StudyModel", back_populates="work_items")
    report: Mapped[Optional["ReportModel"]] = relationship(
        "ReportModel", back_populates="work_item", uselist=False, cascade="all, delete-orphan"
    )


class ReportModel(Base):
    """
    Root entity model for a clinical diagnostic report.

    Table: `reports`
    Attributes:
        id (str): Primary key report UUID.
        work_item_id (str): One-to-one foreign key link to `work_items.id`.
        status (str): High-level report status ('DRAFT', 'SUBMITTED', 'SIGNED', 'RELEASED', 'AMENDED').
        current_version_id (Optional[str]): Pointer to the most recent report version snapshot.
        created_at (datetime): Initial draft creation timestamp.
        updated_at (datetime): Timestamp of latest amendment or sign-off.
        work_item (WorkItemModel): Parent worklist item.
        versions (List[ReportVersionModel]): Ordered collection of immutable version records.
        deliveries (List[ReportDeliveryModel]): Downstream EHR dispatch logs.
    """
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    work_item_id: Mapped[str] = mapped_column(ForeignKey("work_items.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True, nullable=False)
    current_version_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    work_item: Mapped["WorkItemModel"] = relationship("WorkItemModel", back_populates="report")
    versions: Mapped[List["ReportVersionModel"]] = relationship(
        "ReportVersionModel",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportVersionModel.version_number",
    )
    deliveries: Mapped[List["ReportDeliveryModel"]] = relationship(
        "ReportDeliveryModel", back_populates="report", cascade="all, delete-orphan"
    )


class ReportVersionModel(Base):
    """
    Append-only snapshot representing a specific iteration of a diagnostic report.

    Table: `report_versions`
    Invariants:
        - Strictly Append-Only: Rows cannot be altered (UPDATE) or deleted (DELETE).
        - Enforced via unique constraint on (report_id, version_number).
        - Backed by SQLAlchemy ORM listeners and PostgreSQL database-level triggers.

    Attributes:
        id (str): Primary key version identifier (e.g. 'REP-001-v1').
        report_id (str): Foreign key reference to parent `reports.id`.
        version_number (int): Monotonically increasing version counter (1, 2, 3...).
        structured_findings (Dict[str, Any]): JSONB payload containing anatomical findings.
        impression (str): High-level diagnostic conclusion and synthesis.
        author_id (str): Clinician ID or AI agent name who prepared this draft.
        signature_hash (Optional[str]): Cryptographic HMAC-SHA256 signature when signed.
        signed_at (Optional[datetime]): Timestamp of clinical sign-off.
        created_at (datetime): Version generation timestamp in UTC.
        report (ReportModel): Parent report relation.
    """
    __tablename__ = "report_versions"
    __table_args__ = (
        UniqueConstraint("report_id", "version_number", name="uq_report_version_number"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    structured_findings: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    impression: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    report: Mapped["ReportModel"] = relationship("ReportModel", back_populates="versions")


# ==============================================================================
# ORM Listeners Enforcing Medical-Legal Immutability on ReportVersionModel
# ==============================================================================
@event.listens_for(ReportVersionModel, "before_update")
def receive_before_update(mapper, connection, target):
    """Intercept and block any SQL UPDATE statements on ReportVersionModel rows."""
    raise ImmutableReportOverrideError(
        f"Database violation: ReportVersion rows are strictly append-only. "
        f"Attempted to UPDATE report_version ID '{target.id}', version {target.version_number}."
    )


@event.listens_for(ReportVersionModel, "before_delete")
def receive_before_delete(mapper, connection, target):
    """Intercept and block any SQL DELETE statements on ReportVersionModel rows."""
    raise ImmutableReportOverrideError(
        f"Database violation: ReportVersion rows are strictly append-only and cannot be deleted. "
        f"Attempted to DELETE report_version ID '{target.id}', version {target.version_number}."
    )


class ReportDeliveryModel(Base):
    """
    Tracks asynchronous dispatch of finalized reports to downstream EHR / HMS systems.

    Table: `report_deliveries`
    Attributes:
        id (str): Primary key delivery record UUID.
        report_id (str): Foreign key to the parent `reports.id`.
        destination_system (str): Name of destination EHR (e.g. 'CharmHealth EHR', 'Epic', 'Cerner').
        status (str): Current delivery status ('PENDING', 'DELIVERED', 'FAILED').
        delivery_channel (str): Protocol used ('FHIR_R4', 'HL7_ORU_R01', 'DICOM_SR').
        delivered_at (Optional[datetime]): Timestamp of successful delivery acknowledgment.
        error_message (Optional[str]): Error text if delivery failed.
        retry_count (int): Number of attempted retry dispatches.
        created_at (datetime): Initial queuing timestamp in UTC.
        report (ReportModel): Parent report relation.
    """
    __tablename__ = "report_deliveries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_system: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    delivery_channel: Mapped[str] = mapped_column(String(32), default="HL7_ORU_R01", nullable=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    report: Mapped["ReportModel"] = relationship("ReportModel", back_populates="deliveries")


class AuditEventModel(Base):
    """
    Append-only compliance audit trail record.

    Table: `audit_events`
    Attributes:
        id (str): Unique audit record UUID.
        actor_id (str): Authenticated user ID or system service performing the action.
        action (str): Specific action code ('STATE_TRANSITION', 'REPORT_SIGNOFF', 'RECONCILIATION_FLAG').
        resource_id (str): Target entity ID affected by this operation.
        timestamp (datetime): UTC microsecond timestamp when event occurred.
        correlation_id (str): Distributed tracing correlation ID.
        details (Optional[Dict[str, Any]]): JSONB payload capturing pre/post state changes.
    """
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, default="")
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)


class OutboxEventModel(Base):
    """
    Transactional Outbox record guaranteeing at-least-once message delivery.

    Table: `outbox_events`
    Attributes:
        id (str): Primary key event UUID.
        aggregate_type (str): Type of aggregate modified ('WORK_ITEM', 'STUDY', 'REPORT').
        aggregate_id (str): Identifier of the aggregate.
        event_type (str): Domain event type ('STUDY_INGESTED', 'REPORT_FINALIZED').
        payload (Dict[str, Any]): JSONB payload containing event details.
        created_at (datetime): Database insertion timestamp.
        processed_at (Optional[datetime]): Timestamp when Celery worker successfully published the event.
    """
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    aggregate_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
