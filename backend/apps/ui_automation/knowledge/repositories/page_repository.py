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
    
    async def count_valid_pages(self) -> int:
        """
        统计有效页面数量（elements_count > 0）
        
        Returns:
            有效页面数量
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(PageAnalysis)
            .where(PageAnalysis.elements_count > 0)
        )
        return result.scalar() or 0
    
    async def count_unique_pages(self) -> int:
        """
        统计去重后的有效页面数量
        同一应用下同名页面只计算一次
        
        Returns:
            去重后的页面数量
        """
        # 使用 COUNT(DISTINCT) 统计唯一组合数
        result = await self.session.execute(
            select(func.count(func.distinct(
                func.concat(PageAnalysis.app_id, '_', PageAnalysis.page_name)
            )))
            .select_from(PageAnalysis)
            .where(PageAnalysis.elements_count > 0)
        )
        return result.scalar() or 0
    
    async def get_recent_valid_pages(self, limit: int = 5) -> List[PageAnalysis]:
        """
        获取最近的有效页面（elements_count > 0）
        
        Args:
            limit: 数量限制
            
        Returns:
            页面列表
        """
        result = await self.session.execute(
            select(PageAnalysis)
            .where(PageAnalysis.elements_count > 0)
            .order_by(PageAnalysis.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_unique_pages(
        self,
        offset: int = 0,
        limit: int = 12,
        app_name: Optional[str] = None,
        include_failed: bool = False
    ) -> List[PageAnalysis]:
        """
        获取去重后的页面列表（SQL层面去重，高效）
        每个 (app_id, page_name) 组合只返回最新的一条
        
        性能优化：
        - 使用索引友好的子查询
        - 先获取最新 ID，再关联获取完整数据
        - 避免在窗口函数中处理所有列
        
        Args:
            offset: 偏移量
            limit: 数量限制
            app_name: 应用名称过滤
            include_failed: 是否包含解析失败的页面
            
        Returns:
            去重后的页面列表
        """
        from sqlalchemy import text
        
        # 构建过滤条件
        inner_conditions = []
        outer_conditions = ["1=1"]
        params = {"offset": offset, "limit": limit}
        
        if not include_failed:
            inner_conditions.append("elements_count > 0")
        
        if app_name:
            outer_conditions.append("a.app_name = :app_name")
            params["app_name"] = app_name
        
        inner_where = " AND ".join(inner_conditions) if inner_conditions else "1=1"
        outer_where = " AND ".join(outer_conditions)
        
        # 优化查询：先用轻量查询获取最新 ID，再关联获取完整数据
        sql = text(f"""
            WITH latest_pages AS (
                SELECT id, app_id, page_name, created_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY app_id, page_name 
                           ORDER BY created_at DESC
                       ) as rn
                FROM kb_page_analysis
                WHERE {inner_where}
            )
            SELECT p.*, a.app_name
            FROM kb_page_analysis p
            INNER JOIN latest_pages lp ON p.id = lp.id AND lp.rn = 1
            LEFT JOIN kb_app_info a ON p.app_id = a.id
            WHERE {outer_where}
            ORDER BY p.created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = await self.session.execute(sql, params)
        rows = result.fetchall()
        
        # 映射到 PageAnalysis 对象
        pages = []
        for row in rows:
            page = PageAnalysis(
                id=row.id,
                app_id=row.app_id,
                page_name=row.page_name,
                page_type=row.page_type,
                page_description=row.page_description,
                user_context=row.user_context,
                navigation_source=row.navigation_source,
                screenshot_hash=row.screenshot_hash,
                screenshot_url=row.screenshot_url,
                device_udid=row.device_udid,
                device_resolution=row.device_resolution,
                elements_count=row.elements_count,
                confidence_score=row.confidence_score,
                processing_time=row.processing_time,
                page_signature=row.page_signature,
                depth=row.depth,
                visit_count=row.visit_count,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            page._app_name = row.app_name
            pages.append(page)
        
        return pages
