from typing import Optional, List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TcgProject, TcgTestCase, TcgConversation


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> TcgProject:
        project = TcgProject(**kwargs)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_by_id(self, project_id: str) -> Optional[TcgProject]:
        result = await self.db.execute(
            select(TcgProject).where(TcgProject.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, page_size: int = 20) -> tuple[List[TcgProject], int]:
        count_result = await self.db.execute(
            select(func.count(TcgProject.id))
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(TcgProject)
            .order_by(TcgProject.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def update(self, project_id: str, **kwargs) -> Optional[TcgProject]:
        project = await self.get_by_id(project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(project, key, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: str) -> bool:
        project = await self.get_by_id(project_id)
        if not project:
            return False
        await self.db.delete(project)
        await self.db.commit()
        return True

    async def get_stats(self, project_id: str) -> dict:
        case_count = await self.db.execute(
            select(func.count(TcgTestCase.id)).where(TcgTestCase.project_id == project_id)
        )
        conversation_count = await self.db.execute(
            select(func.count(TcgConversation.id)).where(
                TcgConversation.project_id == project_id
            )
        )
        return {
            "case_count": case_count.scalar() or 0,
            "conversation_count": conversation_count.scalar() or 0,
        }
