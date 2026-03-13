"""Skill 数据访问层"""
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Skill


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Skill:
        skill = Skill(**kwargs)
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def get_by_id(self, skill_id: str) -> Optional[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def get_by_key(self, key: str) -> Optional[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.key == key))
        return result.scalar_one_or_none()

    async def get_by_keys(self, keys: List[str]) -> List[Skill]:
        if not keys:
            return []
        result = await self.db.execute(
            select(Skill).where(Skill.key.in_(keys)).order_by(Skill.sort_order, Skill.name)
        )
        return list(result.scalars().all())

    async def list_by_categories(
        self,
        categories: List[str],
        enabled_only: bool = True,
    ) -> List[Skill]:
        if not categories:
            return []
        q = select(Skill).where(Skill.category.in_(categories))
        if enabled_only:
            q = q.where(Skill.is_enabled == True)
        q = q.order_by(Skill.sort_order, Skill.name)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def list_all(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[Skill]:
        q = select(Skill)
        if category:
            q = q.where(Skill.category == category)
        if enabled_only:
            q = q.where(Skill.is_enabled == True)
        q = q.order_by(Skill.sort_order, Skill.name)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def update(self, skill_id: str, **kwargs) -> Optional[Skill]:
        skill = await self.get_by_id(skill_id)
        if not skill:
            return None
        for k, v in kwargs.items():
            if hasattr(skill, k):
                setattr(skill, k, v)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def delete(self, skill_id: str) -> bool:
        skill = await self.get_by_id(skill_id)
        if not skill:
            return False
        await self.db.delete(skill)
        await self.db.commit()
        return True

    async def exists_key(self, key: str, exclude_id: Optional[str] = None) -> bool:
        q = select(Skill).where(Skill.key == key)
        if exclude_id:
            q = q.where(Skill.id != exclude_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none() is not None
