"""
Unit Tests: Enterprise Domain Rules and Entities (Clean Architecture).
Zero external dependency verification.
"""
from datetime import datetime, timezone
import pytest
from core.domain.entities.study import ImagingSeries, RadiologyStudy, StudyLifecycleState
from core.domain.entities.report import Finding, RadiologyReport
from core.domain.values.identifiers import AccessionNumber, PatientIdentifier, StudyUID
from core.domain.values.triage_priority import Modality, TriagePriority
from core.domain.exceptions import InvalidDICOMMetadataError


def test_study_uid_valid():
    uid = StudyUID("1.2.840.10008.5.1.4.1.1.2.20261124.001")
    assert uid.value == "1.2.840.10008.5.1.4.1.1.2.20261124.001"


def test_study_uid_invalid_format():
    with pytest.raises(InvalidDICOMMetadataError):
        StudyUID("not-a-valid-dicom-uid!")


def test_triage_priority_sla():
    assert TriagePriority.STAT.max_turnaround_minutes == 15
    assert TriagePriority.URGENT.max_turnaround_minutes == 60
    assert TriagePriority.ROUTINE.max_turnaround_minutes == 240


def test_study_escalation_and_lifecycle():
    study = RadiologyStudy(
        uid=StudyUID("1.2.840.10008.5.1.4.1.1.2.100"),
        accession=AccessionNumber("ACC-2026-001"),
        patient_id=PatientIdentifier("PAT-999"),
        modality=Modality.CT,
        study_date=datetime.now(timezone.utc),
        description="Head CT without contrast",
        priority=TriagePriority.ROUTINE,
        state=StudyLifecycleState.RECEIVED,
    )

    assert study.priority == TriagePriority.ROUTINE
    assert study.state == StudyLifecycleState.RECEIVED

    study.escalate_priority(TriagePriority.STAT)
    assert study.priority == TriagePriority.STAT

    study.transition_to(StudyLifecycleState.ANALYSIS_IN_PROGRESS)
    assert study.state == StudyLifecycleState.ANALYSIS_IN_PROGRESS


def test_radiology_report_critical_finding():
    report = RadiologyReport(
        id="rep-01",
        study_uid="1.2.840.10008.5.1.4.1.1.2.100",
        created_at=datetime.now(timezone.utc),
        clinical_history="Headache and sudden neurological deficit",
        technique="Axial brain CT",
    )
    assert not report.has_critical_findings

    report.add_finding(
        Finding(
            id="f-01",
            label="Intracranial Hemorrhage",
            confidence=0.95,
            anatomical_location="Right temporal lobe",
            is_critical=True,
        )
    )
    assert report.has_critical_findings
