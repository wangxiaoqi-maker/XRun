"""模块 Repository"""
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TcgModule


class ModuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_project(self, project_id: str) -> list[TcgModule]:
        result = await self.db.execute(
            select(TcgModule)
            .where(TcgModule.project_id == project_id)
            .order_by(TcgModule.sort_order, TcgModule.created_at)
        )
        return list(result.scalars().all())

    async def create(self, project_id: str, name: str, parent_id: str = None) -> TcgModule:
        existing = await self.db.execute(
            select(TcgModule).where(
                TcgModule.project_id == project_id,
                TcgModule.name == name,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"模块 '{name}' 已存在")

        max_order = await self.db.execute(
            select(func.coalesce(func.max(TcgModule.sort_order), 0))
            .where(TcgModule.project_id == project_id)
        )
        next_order = max_order.scalar() + 1

        module = TcgModule(
            project_id=project_id,
            name=name.strip(),
            parent_id=parent_id,
            sort_order=next_order,
        )
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        return module

    async def rename(self, module_id: str, new_name: str) -> TcgModule:
        result = await self.db.execute(
            select(TcgModule).where(TcgModule.id == module_id)
        )
        module = result.scalar_one_or_none()
        if not module:
            raise ValueError("模块不存在")
        module.name = new_name.strip()
        await self.db.commit()
        await self.db.refresh(module)
        return module

    async def delete(self, module_id: str):
        await self.db.execute(
            delete(TcgModule).where(TcgModule.id == module_id)
        )
        await self.db.commit()
