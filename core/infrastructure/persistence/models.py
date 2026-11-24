"""
SQLAlchemy 2.0 Async Persistence Models for SIMS Radiology Platform.
Implements table mappings, relations, constraints, and append-only listeners.
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
    """Base class for all persistence models."""
    pass


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PatientModel(Base):
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


# ORM Listeners enforcing append-only invariant on ReportVersionModel
@event.listens_for(ReportVersionModel, "before_update")
def receive_before_update(mapper, connection, target):
    raise ImmutableReportOverrideError(
        f"Database violation: ReportVersion rows are strictly append-only. "
        f"Attempted to UPDATE report_version ID '{target.id}', version {target.version_number}."
    )


@event.listens_for(ReportVersionModel, "before_delete")
def receive_before_delete(mapper, connection, target):
    raise ImmutableReportOverrideError(
        f"Database violation: ReportVersion rows are strictly append-only and cannot be deleted. "
        f"Attempted to DELETE report_version ID '{target.id}', version {target.version_number}."
    )


class ReportDeliveryModel(Base):
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
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, default="")
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)


class OutboxEventModel(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    aggregate_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
