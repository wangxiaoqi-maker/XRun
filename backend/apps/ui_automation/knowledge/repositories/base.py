"""
Repository 基类

提供通用的 CRUD 操作抽象
"""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """
    通用 Repository 基类
    
    提供基础的 CRUD 操作，子类可以扩展特定的查询方法
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, obj: ModelType) -> ModelType:
        """
        创建记录
        
        Args:
            obj: 模型实例
            
        Returns:
            创建后的实例
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
    
    async def create_many(self, objs: List[ModelType]) -> List[ModelType]:
        """
        批量创建记录
        
        Args:
            objs: 模型实例列表
            
        Returns:
            创建后的实例列表
        """
        self.session.add_all(objs)
        await self.session.flush()
        for obj in objs:
            await self.session.refresh(obj)
        return objs
    
    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """
        根据 ID 获取记录
        
        Args:
            id: 主键 ID
            
        Returns:
            模型实例或 None
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> List[ModelType]:
        """
        获取所有记录（分页）
        
        Args:
            offset: 偏移量
            limit: 数量限制
            order_by: 排序字段
            
        Returns:
            模型实例列表
        """
        query = select(self.model)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """
        更新记录
        
        Args:
            id: 主键 ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的实例或 None
        """
        await self.session.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        return await self.get_by_id(id)
    
    async def delete(self, id: str) -> bool:
        """
        删除记录
        
        Args:
            id: 主键 ID
            
        Returns:
            是否成功删除
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def delete_many(self, ids: List[str]) -> int:
        """
        批量删除记录
        
        Args:
            ids: ID 列表
            
        Returns:
            删除的数量
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id.in_(ids))
        )
        return result.rowcount
    
    async def exists(self, id: str) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 主键 ID
            
        Returns:
            是否存在
        """
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None
    
    async def count(self) -> int:
        """
        获取记录总数
        
        Returns:
            记录数量
        """
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0
