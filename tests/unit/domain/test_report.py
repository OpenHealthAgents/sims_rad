"""
Unit Tests: Report & ReportVersion Domain Entities.
Validates immutability invariants, versioning, authorized sign-off, and amendments.
"""
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import pytest
from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.exceptions import ImmutableReportOverrideError, UnauthorizedSignoffError


def test_report_creation():
    report = Report(
        report_id="rep-101",
        work_item_id="wi-101",
        status=ReportStatus.DRAFT,
    )
    assert report.report_id == "rep-101"
    assert report.work_item_id == "wi-101"
    assert report.status == ReportStatus.DRAFT
    assert report.current_version_id is None
    assert len(report.versions) == 0


def test_report_version_immutability():
    """Validates ReportVersion cannot be mutated once instantiated."""
    ver = ReportVersion(
        version_number=1,
        structured_findings={"hemorrhage": True, "location": "temporal"},
        impression="Acute hemorrhage identified.",
        author_id="agent-pathology-v1",
    )

    with pytest.raises(FrozenInstanceError):
        ver.impression = "Mutated impression"  # type: ignore

    with pytest.raises(FrozenInstanceError):
        ver.author_id = "other-author"  # type: ignore


def test_adding_and_overriding_versions():
    report = Report(report_id="rep-102", work_item_id="wi-102")

    ver1 = ReportVersion(
        version_number=1,
        structured_findings={"lobe": "frontal"},
        impression="Normal frontal lobe.",
        author_id="ai-model-1",
    )
    v1_id = report.add_version(ver1)
    assert v1_id == "rep-102-v1"
    assert report.current_version_id == "rep-102-v1"

    # Attempting to re-add version 1 (override attempt) must raise ImmutableReportOverrideError
    dup_ver1 = ReportVersion(
        version_number=1,
        structured_findings={"lobe": "frontal"},
        impression="Changed impression attempt",
        author_id="ai-model-2",
    )
    with pytest.raises(ImmutableReportOverrideError, match="strictly immutable"):
        report.add_version(dup_ver1)


def test_non_monotonic_version_increment_rejected():
    report = Report(report_id="rep-103", work_item_id="wi-103")

    ver3 = ReportVersion(
        version_number=3,  # Invalid jump: Expected version 1
        structured_findings={},
        impression="Jump impression",
        author_id="ai-1",
    )
    with pytest.raises(ImmutableReportOverrideError, match="Invalid version increment"):
        report.add_version(ver3)


def test_report_submission_and_signoff():
    report = Report(report_id="rep-104", work_item_id="wi-104")
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={"fracture": False},
        impression="No acute fracture.",
        author_id="resident-1",
    )
    report.add_version(ver1)

    # Submit
    report.submit_for_review()
    assert report.status == ReportStatus.SUBMITTED

    # Signoff with authorized radiologist
    authorized = ["rad-attending-dr-adams", "rad-attending-dr-baker"]
    signed_ver = report.sign_and_release(
        radiologist_id="rad-attending-dr-adams",
        signature_hash="sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        authorized_radiologists=authorized,
    )

    assert report.status == ReportStatus.SIGNED
    assert signed_ver.signature_hash is not None
    assert signed_ver.signed_at is not None

    # Release
    report.release()
    assert report.status == ReportStatus.RELEASED


def test_unauthorized_signoff_rejected():
    report = Report(report_id="rep-105", work_item_id="wi-105")
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={},
        impression="Impression text",
        author_id="resident-1",
    )
    report.add_version(ver1)

    authorized = ["rad-dr-official"]

    with pytest.raises(UnauthorizedSignoffError, match="not authorized"):
        report.sign_and_release(
            radiologist_id="imposter-user",
            signature_hash="sha256:abc12345",
            authorized_radiologists=authorized,
        )

    with pytest.raises(UnauthorizedSignoffError, match="signature_hash is mandatory"):
        report.sign_and_release(
            radiologist_id="rad-dr-official",
            signature_hash="",
            authorized_radiologists=authorized,
        )


def test_report_amendment_lifecycle():
    report = Report(report_id="rep-106", work_item_id="wi-106")
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={},
        impression="Initial released report",
        author_id="dr-jones",
    )
    report.add_version(ver1)
    report.sign_and_release(
        radiologist_id="dr-jones",
        signature_hash="sha256:sig111",
    )
    report.release()
    assert report.status == ReportStatus.RELEASED

    # Amend with version 2
    ver2 = ReportVersion(
        version_number=2,
        structured_findings={"addendum": "Delayed subdural hematoma observed on re-read"},
        impression="ADDENDUM: Subdural hematoma noted on coronal view.",
        author_id="dr-jones",
    )
    v2_id = report.amend(ver2)
    assert v2_id == "rep-106-v2"
    assert report.status == ReportStatus.AMENDED
    assert len(report.versions) == 2


def test_amend_draft_report_rejected():
    """Amend is only valid for SIGNED, RELEASED, or AMENDED reports."""
    report = Report(report_id="rep-107", work_item_id="wi-107")
    ver1 = ReportVersion(
        version_number=1,
        structured_findings={},
        impression="Draft impression",
        author_id="resident-1",
    )
    report.add_version(ver1)

    ver2 = ReportVersion(
        version_number=2,
        structured_findings={},
        impression="Amendment attempt",
        author_id="resident-1",
    )
    with pytest.raises(ImmutableReportOverrideError, match="Cannot amend report in 'DRAFT' status"):
        report.amend(ver2)
