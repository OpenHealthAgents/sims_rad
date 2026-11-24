"""
Concrete WorkItemRepository implementing async queries, filtering, and pagination.
"""
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.entities.work_item import Priority, WorkItem, WorkItemState
from core.infrastructure.persistence.models import StudyModel, WorkItemModel


class WorkItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: WorkItemModel) -> WorkItem:
        return WorkItem(
            work_item_id=model.id,
            study_id=model.study_id,
            state=WorkItemState(model.state),
            priority=Priority(model.priority),
            assigned_radiologist_id=model.assigned_radiologist_id,
            sla_deadline=model.sla_deadline,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def create(self, work_item: WorkItem) -> WorkItem:
        model = WorkItemModel(
            id=work_item.work_item_id,
            study_id=work_item.study_id,
            state=work_item.state.value,
            priority=work_item.priority.value,
            assigned_radiologist_id=work_item.assigned_radiologist_id,
            sla_deadline=work_item.sla_deadline,
            version=work_item.version,
            created_at=work_item.created_at,
            updated_at=work_item.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def get_by_id(self, work_item_id: str) -> Optional[WorkItem]:
        query = select(WorkItemModel).where(WorkItemModel.id == work_item_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_study_id(self, study_id: str) -> Optional[WorkItem]:
        query = select(WorkItemModel).where(WorkItemModel.study_id == study_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, work_item: WorkItem) -> WorkItem:
        query = select(WorkItemModel).where(WorkItemModel.id == work_item.work_item_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"WorkItem '{work_item.work_item_id}' not found.")

        model.state = work_item.state.value
        model.priority = work_item.priority.value
        model.assigned_radiologist_id = work_item.assigned_radiologist_id
        model.sla_deadline = work_item.sla_deadline
        model.version = work_item.version
        model.updated_at = work_item.updated_at

        await self.session.flush()
        return self._to_domain(model)

    async def filter_worklist(
        self,
        modality: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        assigned_radiologist_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WorkItem], int]:
        """
        Query worklist items with filters, joined on studies table for modality filtering,
        ordered by priority and SLA deadline.
        Returns: (items, total_count)
        """
        query = select(WorkItemModel).join(StudyModel, WorkItemModel.study_id == StudyModel.id)

        if modality:
            query = query.where(StudyModel.modality == modality.upper())
        if priority:
            query = query.where(WorkItemModel.priority == priority.upper())
        if status:
            query = query.where(WorkItemModel.state == status.lower())
        if assigned_radiologist_id:
            query = query.where(WorkItemModel.assigned_radiologist_id == assigned_radiologist_id)

        # Count query
        count_query = select(func.count()).select_from(query.subquery())
        count_res = await self.session.execute(count_query)
        total_count = count_res.scalar() or 0

        # Order by priority weight & deadline
        query = query.order_by(
            WorkItemModel.sla_deadline.asc().nulls_last(),
            WorkItemModel.created_at.desc(),
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total_count
