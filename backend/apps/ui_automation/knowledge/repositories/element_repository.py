"""
页面元素 Repository
"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models import PageElement


class ElementRepository(BaseRepository[PageElement]):
    """
    页面元素数据访问
    
    提供 PageElement 的 CRUD 操作及特定查询
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(PageElement, session)
    
    async def list_by_page(
        self,
        page_id: str,
        element_type: Optional[str] = None,
        testable_only: bool = False,
        offset: int = 0,
        limit: int = 100
    ) -> List[PageElement]:
        """
        获取页面的元素列表
        
        Args:
            page_id: 页面 ID
            element_type: 元素类型（可选）
            testable_only: 只返回可测试元素
            offset: 偏移量
            limit: 数量限制
            
        Returns:
            元素列表
        """
        query = select(PageElement).where(PageElement.page_id == page_id)
        
        if element_type:
            query = query.where(PageElement.element_type == element_type)
        
        if testable_only:
            query = query.where(PageElement.is_testable == True)
        
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_navigation_elements(
        self,
        page_id: str
    ) -> List[PageElement]:
        """
        获取页面的导航元素（可跳转元素）
        
        Args:
            page_id: 页面 ID
            
        Returns:
            导航元素列表
        """
        result = await self.session.execute(
            select(PageElement).where(
                PageElement.page_id == page_id,
                PageElement.is_navigation == True
            )
        )
        return list(result.scalars().all())
    
    async def search_by_name(
        self,
        keyword: str,
        page_id: Optional[str] = None,
        limit: int = 20
    ) -> List[PageElement]:
        """
        根据名称模糊搜索元素
        
        Args:
            keyword: 搜索关键词
            page_id: 页面 ID（可选）
            limit: 数量限制
            
        Returns:
            元素列表
        """
        query = select(PageElement).where(
            PageElement.element_name.ilike(f"%{keyword}%")
        )
        
        if page_id:
            query = query.where(PageElement.page_id == page_id)
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_page(self, page_id: str) -> int:
        """
        获取页面的元素数量
        
        Args:
            page_id: 页面 ID
            
        Returns:
            元素数量
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(PageElement)
            .where(PageElement.page_id == page_id)
        )
        return result.scalar() or 0
    
    async def get_element_types_stats(self, page_id: str) -> dict:
        """
        获取页面的元素类型统计
        
        Args:
            page_id: 页面 ID
            
        Returns:
            元素类型统计 {element_type: count}
        """
        result = await self.session.execute(
            select(PageElement.element_type, func.count())
            .where(PageElement.page_id == page_id)
            .group_by(PageElement.element_type)
        )
        return dict(result.all())
    
    async def delete_by_page(self, page_id: str) -> int:
        """
        删除页面的所有元素
        
        Args:
            page_id: 页面 ID
            
        Returns:
            删除的数量
        """
        from sqlalchemy import delete as sql_delete
        
        result = await self.session.execute(
            sql_delete(PageElement).where(PageElement.page_id == page_id)
        )
        return result.rowcount
    
    async def get_by_priority(
        self,
        page_id: str,
        priority: str,
        limit: int = 50
    ) -> List[PageElement]:
        """
        根据测试优先级获取元素
        
        Args:
            page_id: 页面 ID
            priority: 测试优先级（high/medium/low）
            limit: 数量限制
            
        Returns:
            元素列表
        """
        result = await self.session.execute(
            select(PageElement).where(
                PageElement.page_id == page_id,
                PageElement.test_priority == priority,
                PageElement.is_testable == True
            ).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_elements_with_target_page(
        self,
        page_id: str
    ) -> List[PageElement]:
        """
        获取有跳转目标的元素
        
        Args:
            page_id: 页面 ID
            
        Returns:
            元素列表
        """
        result = await self.session.execute(
            select(PageElement).where(
                PageElement.page_id == page_id,
                PageElement.target_page_id.isnot(None)
            )
        )
        return list(result.scalars().all())
