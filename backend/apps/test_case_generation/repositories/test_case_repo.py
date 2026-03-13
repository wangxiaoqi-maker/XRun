from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TcgTestCase


class TestCaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> TcgTestCase:
        case = TcgTestCase(**kwargs)
        self.db.add(case)
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def batch_create(self, cases_data: List[dict]) -> List[TcgTestCase]:
        cases = [TcgTestCase(**data) for data in cases_data]
        self.db.add_all(cases)
        await self.db.commit()
        for c in cases:
            await self.db.refresh(c)
        return cases

    async def get_by_id(self, case_id: str) -> Optional[TcgTestCase]:
        result = await self.db.execute(
            select(TcgTestCase).where(TcgTestCase.id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, case_ids: List[str]) -> List[TcgTestCase]:
        result = await self.db.execute(
            select(TcgTestCase).where(TcgTestCase.id.in_(case_ids))
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: str, page: int = 1,
                               page_size: int = 20, **filters) -> tuple[List[TcgTestCase], int]:
        query = select(TcgTestCase).where(TcgTestCase.project_id == project_id)

        if filters.get("review_status"):
            query = query.where(TcgTestCase.review_status == filters["review_status"])
        if filters.get("priority"):
            query = query.where(TcgTestCase.priority.in_(filters["priority"]))
        if filters.get("module_name"):
            query = query.where(TcgTestCase.module_name == filters["module_name"])
        if filters.get("search"):
            query = query.where(TcgTestCase.name.contains(filters["search"]))

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            query.order_by(TcgTestCase.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def list_by_conversation(self, conversation_id: str) -> List[TcgTestCase]:
        result = await self.db.execute(
            select(TcgTestCase)
            .where(TcgTestCase.conversation_id == conversation_id)
            .order_by(TcgTestCase.case_no)
        )
        return list(result.scalars().all())

    async def update(self, case_id: str, **kwargs) -> Optional[TcgTestCase]:
        case = await self.get_by_id(case_id)
        if not case:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(case, key, value)
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def batch_update_review(self, reviews: List[dict]):
        for r in reviews:
            await self.db.execute(
                update(TcgTestCase)
                .where(TcgTestCase.id == r["case_id"])
                .values(
                    review_status=r["status"],
                    review_comment=r.get("comment"),
                )
            )
        await self.db.commit()

    async def delete(self, case_id: str) -> bool:
        case = await self.get_by_id(case_id)
        if not case:
            return False
        await self.db.delete(case)
        await self.db.commit()
        return True

    async def batch_delete(self, case_ids: List[str]) -> int:
        """批量删除用例，返回删除数量"""
        if not case_ids:
            return 0
        result = await self.db.execute(
            select(TcgTestCase).where(TcgTestCase.id.in_(case_ids))
        )
        cases = result.scalars().all()
        count = len(cases)
        for case in cases:
            await self.db.delete(case)
        await self.db.commit()
        return count
