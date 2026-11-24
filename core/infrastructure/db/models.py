"""
SQLAlchemy 2.0 Database Models for PostgreSQL.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RadiologyStudyModel(Base):
    __tablename__ = "radiology_studies"

    study_uid: Mapped[str] = mapped_column(String(64), primary_key=True)
    accession_number: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    modality: Mapped[str] = mapped_column(String(16), nullable=False)
    study_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    description: Mapped[str] = mapped_column(String(255), default="")
    priority: Mapped[str] = mapped_column(String(32), default="ROUTINE", index=True)
    state: Mapped[str] = mapped_column(String(32), default="RECEIVED", index=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    series: Mapped[List["ImagingSeriesModel"]] = relationship(
        "ImagingSeriesModel", back_populates="study", cascade="all, delete-orphan"
    )
    reports: Mapped[List["RadiologyReportModel"]] = relationship(
        "RadiologyReportModel", back_populates="study", cascade="all, delete-orphan"
    )


class ImagingSeriesModel(Base):
    __tablename__ = "imaging_series"

    series_uid: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_uid: Mapped[str] = mapped_column(ForeignKey("radiology_studies.study_uid"), nullable=False)
    series_number: Mapped[int] = mapped_column(Integer, default=1)
    modality: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    number_of_instances: Mapped[int] = mapped_column(Integer, default=1)

    study: Mapped[RadiologyStudyModel] = relationship("RadiologyStudyModel", back_populates="series")


class RadiologyReportModel(Base):
    __tablename__ = "radiology_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_uid: Mapped[str] = mapped_column(ForeignKey("radiology_studies.study_uid"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    clinical_history: Mapped[str] = mapped_column(Text, default="")
    technique: Mapped[str] = mapped_column(Text, default="")
    impression: Mapped[str] = mapped_column(Text, default="")
    findings_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_verified_by_guardrails: Mapped[bool] = mapped_column(Boolean, default=False)
    is_signed_off: Mapped[bool] = mapped_column(Boolean, default=False)

    study: Mapped[RadiologyStudyModel] = relationship("RadiologyStudyModel", back_populates="reports")
