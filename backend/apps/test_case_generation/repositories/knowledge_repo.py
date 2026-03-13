from typing import Optional, List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TcgKbDocumentChunk


class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chunk(self, **kwargs) -> TcgKbDocumentChunk:
        chunk = TcgKbDocumentChunk(**kwargs)
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk

    async def batch_create_chunks(self, chunks_data: List[dict]) -> int:
        chunks = [TcgKbDocumentChunk(**data) for data in chunks_data]
        self.db.add_all(chunks)
        await self.db.commit()
        return len(chunks)

    async def get_by_file_id(self, file_id: str) -> List[TcgKbDocumentChunk]:
        result = await self.db.execute(
            select(TcgKbDocumentChunk).where(TcgKbDocumentChunk.file_id == file_id)
        )
        return list(result.scalars().all())

    async def delete_by_file_id(self, file_id: str) -> int:
        result = await self.db.execute(
            delete(TcgKbDocumentChunk).where(TcgKbDocumentChunk.file_id == file_id)
        )
        await self.db.commit()
        return result.rowcount

    async def get_stats(self, project_id: str) -> dict:
        count_result = await self.db.execute(
            select(func.count(TcgKbDocumentChunk.id)).where(
                TcgKbDocumentChunk.project_id == project_id
            )
        )
        return {"chunk_count": count_result.scalar() or 0}

    async def clear_project(self, project_id: str) -> int:
        result = await self.db.execute(
            delete(TcgKbDocumentChunk).where(TcgKbDocumentChunk.project_id == project_id)
        )
        await self.db.commit()
        return result.rowcount
