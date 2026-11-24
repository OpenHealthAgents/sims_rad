"""
Unit Tests: RadiologyStudy Domain Entity.
Validates required PRD attributes, Modalities (CT, MRI, XRAY), and Priority Escalation.
"""
from datetime import datetime, timezone
import pytest
from core.domain.entities.study import ImagingSeries, Modality, RadiologyStudy, StudyLifecycleState
from core.domain.values.triage_priority import TriagePriority


def test_radiology_study_creation():
    study = RadiologyStudy(
        study_id="std-12345",
        study_instance_uid="1.2.840.10008.5.1.4.1.1.2.20261124.500",
        accession_number="ACC-500",
        modality=Modality.CT,
        study_date=datetime(2026, 11, 24, 10, 0, tzinfo=timezone.utc),
        source_system="GE-PACS-CENTRICITY",
    )

    assert study.study_id == "std-12345"
    assert study.study_instance_uid == "1.2.840.10008.5.1.4.1.1.2.20261124.500"
    assert study.accession_number == "ACC-500"
    assert study.modality == Modality.CT
    assert study.source_system == "GE-PACS-CENTRICITY"
    assert study.priority == TriagePriority.ROUTINE
    assert study.state == StudyLifecycleState.RECEIVED


def test_modality_enum_values_and_aliases():
    # Direct enum values
    assert Modality.CT.value == "CT"
    assert Modality.MRI.value == "MRI"
    assert Modality.XRAY.value == "XRAY"

    # String parsing and aliases
    assert Modality("CT") == Modality.CT
    assert Modality("MRI") == Modality.MRI
    assert Modality("XRAY") == Modality.XRAY
    assert Modality("MR") == Modality.MRI
    assert Modality("XR") == Modality.XRAY


def test_study_priority_escalation():
    study = RadiologyStudy(
        study_id="std-urgent",
        study_instance_uid="1.2.840.10008.5.1.4.1.1.2.999",
        accession_number="ACC-999",
        modality=Modality.MRI,
        study_date=datetime.now(timezone.utc),
        priority=TriagePriority.ROUTINE,
    )

    # Escalate to URGENT
    study.escalate_priority(TriagePriority.URGENT)
    assert study.priority == TriagePriority.URGENT

    # Escalate to STAT
    study.escalate_priority(TriagePriority.STAT)
    assert study.priority == TriagePriority.STAT

    # STAT should not downgrade back to URGENT via escalate
    study.escalate_priority(TriagePriority.URGENT)
    assert study.priority == TriagePriority.STAT


def test_study_series_association():
    study = RadiologyStudy(
        study_id="std-with-series",
        study_instance_uid="1.2.840.10008.5.1.4.1.1.2.888",
        accession_number="ACC-888",
        modality=Modality.XRAY,
        study_date=datetime.now(timezone.utc),
        series=[
            ImagingSeries(
                series_uid="1.2.840.10008.5.1.4.1.1.2.888.1",
                series_number=1,
                modality=Modality.XRAY,
                description="PA Chest",
                number_of_instances=1,
            )
        ],
    )
    assert len(study.series) == 1
    assert study.series[0].description == "PA Chest"
