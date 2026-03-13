from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TcgInputFile


class FileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> TcgInputFile:
        f = TcgInputFile(**kwargs)
        self.db.add(f)
        await self.db.commit()
        await self.db.refresh(f)
        return f

    async def get_by_id(self, file_id: str) -> Optional[TcgInputFile]:
        result = await self.db.execute(
            select(TcgInputFile).where(TcgInputFile.id == file_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> List[TcgInputFile]:
        result = await self.db.execute(
            select(TcgInputFile)
            .where(TcgInputFile.project_id == project_id)
            .order_by(TcgInputFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, file_id: str, status: str,
                             parsed_content: str = None, error_message: str = None):
        f = await self.get_by_id(file_id)
        if not f:
            return
        f.status = status
        if parsed_content is not None:
            f.parsed_content = parsed_content
        if error_message is not None:
            f.error_message = error_message
        await self.db.commit()

    async def delete(self, file_id: str) -> bool:
        f = await self.get_by_id(file_id)
        if not f:
            return False
        await self.db.delete(f)
        await self.db.commit()
        return True
