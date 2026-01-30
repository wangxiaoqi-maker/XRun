"""
页面分析 Repository
"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models import PageAnalysis


class PageRepository(BaseRepository[PageAnalysis]):
    """
    页面分析数据访问
    
    提供 PageAnalysis 的 CRUD 操作及特定查询
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(PageAnalysis, session)
    
    async def get_by_id_with_elements(self, id: str) -> Optional[PageAnalysis]:
        """
        根据 ID 获取页面（含元素）
        
        Args:
            id: 页面 ID
            
        Returns:
            页面分析实例或 None
        """
        result = await self.session.execute(
            select(PageAnalysis)
            .options(selectinload(PageAnalysis.elements))
            .where(PageAnalysis.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_screenshot_hash(
        self,
        app_id: str,
        screenshot_hash: str
    ) -> Optional[PageAnalysis]:
        """
        根据截图哈希获取页面（用于去重）
        
        Args:
            app_id: 应用 ID
            screenshot_hash: 截图 MD5 哈希
            
        Returns:
            页面分析实例或 None
        """
        result = await self.session.execute(
            select(PageAnalysis).where(
                PageAnalysis.app_id == app_id,
                PageAnalysis.screenshot_hash == screenshot_hash
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_app(
        self,
        app_id: str,
        page_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[PageAnalysis]:
        """
        获取应用的页面列表
        
        Args:
            app_id: 应用 ID
            page_type: 页面类型（可选）
            offset: 偏移量
            limit: 数量限制
            
        Returns:
            页面列表
        """
        query = select(PageAnalysis).where(PageAnalysis.app_id == app_id)
        
        if page_type:
            query = query.where(PageAnalysis.page_type == page_type)
        
        query = query.order_by(PageAnalysis.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_app_name(
        self,
        app_name: str,
        platform: Optional[str] = None,
        page_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[PageAnalysis]:
        """
        根据应用名称获取页面列表
        
        Args:
            app_name: 应用名称
            platform: 平台（可选）
            page_type: 页面类型（可选）
            offset: 偏移量
            limit: 数量限制
            
        Returns:
            页面列表
        """
        from ..models import AppInfo
        
        query = (
            select(PageAnalysis)
            .join(AppInfo, PageAnalysis.app_id == AppInfo.id)
            .where(AppInfo.app_name == app_name)
        )
        
        if platform:
            query = query.where(AppInfo.platform == platform)
        
        if page_type:
            query = query.where(PageAnalysis.page_type == page_type)
        
        query = query.order_by(PageAnalysis.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_by_name(
        self,
        keyword: str,
        app_id: Optional[str] = None,
        limit: int = 20
    ) -> List[PageAnalysis]:
        """
        根据名称模糊搜索页面
        
        Args:
            keyword: 搜索关键词
            app_id: 应用 ID（可选）
            limit: 数量限制
            
        Returns:
            页面列表
        """
        query = select(PageAnalysis).where(
            PageAnalysis.page_name.ilike(f"%{keyword}%")
        )
        
        if app_id:
            query = query.where(PageAnalysis.app_id == app_id)
        
        query = query.order_by(PageAnalysis.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_app(self, app_id: str) -> int:
        """
        获取应用的页面数量
        
        Args:
            app_id: 应用 ID
            
        Returns:
            页面数量
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(PageAnalysis)
            .where(PageAnalysis.app_id == app_id)
        )
        return result.scalar() or 0
    
    async def get_page_types_stats(self, app_id: str) -> dict:
        """
        获取应用的页面类型统计
        
        Args:
            app_id: 应用 ID
            
        Returns:
            页面类型统计 {page_type: count}
        """
        result = await self.session.execute(
            select(PageAnalysis.page_type, func.count())
            .where(PageAnalysis.app_id == app_id)
            .group_by(PageAnalysis.page_type)
        )
        return dict(result.all())
    
    async def get_recent_pages(
        self,
        app_id: Optional[str] = None,
        limit: int = 10
    ) -> List[PageAnalysis]:
        """
        获取最近分析的页面
        
        Args:
            app_id: 应用 ID（可选）
            limit: 数量限制
            
        Returns:
            页面列表
        """
        query = select(PageAnalysis)
        
        if app_id:
            query = query.where(PageAnalysis.app_id == app_id)
        
        query = query.order_by(PageAnalysis.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
