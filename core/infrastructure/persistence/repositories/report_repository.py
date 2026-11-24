"""
Concrete ReportRepository enforcing append-only versioning and snapshot retrieval.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.domain.entities.report import Report, ReportStatus, ReportVersion
from core.domain.exceptions import ImmutableReportOverrideError
from core.infrastructure.persistence.models import ReportModel, ReportVersionModel


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _version_to_domain(m: ReportVersionModel) -> ReportVersion:
        return ReportVersion(
            version_number=m.version_number,
            structured_findings=m.structured_findings,
            impression=m.impression,
            author_id=m.author_id,
            signature_hash=m.signature_hash,
            signed_at=m.signed_at,
            created_at=m.created_at,
        )

    def _to_domain(self, m: ReportModel) -> Report:
        versions_dict = {
            v.version_number: self._version_to_domain(v)
            for v in (m.versions or [])
        }
        return Report(
            report_id=m.id,
            work_item_id=m.work_item_id,
            status=ReportStatus(m.status),
            current_version_id=m.current_version_id,
            versions=versions_dict,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def create(self, report: Report) -> Report:
        model = ReportModel(
            id=report.report_id,
            work_item_id=report.work_item_id,
            status=report.status.value,
            current_version_id=report.current_version_id,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )
        self.session.add(model)
        await self.session.flush()

        # Add any initial versions
        for ver in report.versions.values():
            await self.save_version(report.report_id, ver)

        return await self.get_by_id(report.report_id)  # type: ignore

    async def get_by_id(self, report_id: str) -> Optional[Report]:
        query = (
            select(ReportModel)
            .where(ReportModel.id == report_id)
            .options(selectinload(ReportModel.versions))
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_work_item_id(self, work_item_id: str) -> Optional[Report]:
        query = (
            select(ReportModel)
            .where(ReportModel.work_item_id == work_item_id)
            .options(selectinload(ReportModel.versions))
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save_version(self, report_id: str, version: ReportVersion) -> str:
        """
        Append an immutable version to the report.
        Guarantees that existing version numbers cannot be overwritten.
        """
        # Check if version already exists
        check_query = select(ReportVersionModel).where(
            ReportVersionModel.report_id == report_id,
            ReportVersionModel.version_number == version.version_number,
        )
        existing = (await self.session.execute(check_query)).scalar_one_or_none()
        if existing:
            raise ImmutableReportOverrideError(
                f"Version {version.version_number} already exists for report {report_id}. "
                "Report versions are strictly append-only."
            )

        version_id = f"{report_id}-v{version.version_number}"
        v_model = ReportVersionModel(
            id=version_id,
            report_id=report_id,
            version_number=version.version_number,
            structured_findings=version.structured_findings,
            impression=version.impression,
            author_id=version.author_id,
            signature_hash=version.signature_hash,
            signed_at=version.signed_at,
            created_at=version.created_at,
        )
        self.session.add(v_model)

        # Update current_version_id on report
        rep_query = select(ReportModel).where(ReportModel.id == report_id)
        rep = (await self.session.execute(rep_query)).scalar_one()
        rep.current_version_id = version_id

        await self.session.flush()
        return version_id

    async def get_versions(self, report_id: str) -> List[ReportVersion]:
        query = (
            select(ReportVersionModel)
            .where(ReportVersionModel.report_id == report_id)
            .order_by(ReportVersionModel.version_number.asc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._version_to_domain(m) for m in models]

    async def get_version(self, report_id: str, version_number: int) -> Optional[ReportVersion]:
        query = select(ReportVersionModel).where(
            ReportVersionModel.report_id == report_id,
            ReportVersionModel.version_number == version_number,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._version_to_domain(model) if model else None

    async def update_status(
        self,
        report_id: str,
        status: ReportStatus,
        current_version_id: Optional[str] = None,
    ) -> Report:
        query = select(ReportModel).where(ReportModel.id == report_id).options(selectinload(ReportModel.versions))
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Report '{report_id}' not found.")

        model.status = status.value
        if current_version_id:
            model.current_version_id = current_version_id

        await self.session.flush()
        return self._to_domain(model)
