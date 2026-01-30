"""
应用信息 Repository
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models import AppInfo


class AppRepository(BaseRepository[AppInfo]):
    """
    应用信息数据访问
    
    提供 AppInfo 的 CRUD 操作及特定查询
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(AppInfo, session)
    
    async def get_by_package_name(self, package_name: str) -> Optional[AppInfo]:
        """
        根据包名获取应用
        
        Args:
            package_name: 包名（Android）或 Bundle ID（iOS）
            
        Returns:
            应用信息或 None
        """
        result = await self.session.execute(
            select(AppInfo).where(AppInfo.package_name == package_name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, app_name: str) -> Optional[AppInfo]:
        """
        根据应用名称获取应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            应用信息或 None
        """
        result = await self.session.execute(
            select(AppInfo).where(AppInfo.app_name == app_name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name_and_platform(
        self,
        app_name: str,
        platform: str
    ) -> Optional[AppInfo]:
        """
        根据应用名称和平台获取应用
        
        Args:
            app_name: 应用名称
            platform: 平台（android/ios）
            
        Returns:
            应用信息或 None
        """
        result = await self.session.execute(
            select(AppInfo).where(
                AppInfo.app_name == app_name,
                AppInfo.platform == platform
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_platform(
        self,
        platform: str,
        offset: int = 0,
        limit: int = 100
    ) -> List[AppInfo]:
        """
        根据平台获取应用列表
        
        Args:
            platform: 平台（android/ios）
            offset: 偏移量
            limit: 数量限制
            
        Returns:
            应用列表
        """
        result = await self.session.execute(
            select(AppInfo)
            .where(AppInfo.platform == platform)
            .order_by(AppInfo.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def search_by_name(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[AppInfo]:
        """
        根据名称模糊搜索应用
        
        Args:
            keyword: 搜索关键词
            limit: 数量限制
            
        Returns:
            应用列表
        """
        result = await self.session.execute(
            select(AppInfo)
            .where(AppInfo.app_name.ilike(f"%{keyword}%"))
            .order_by(AppInfo.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_or_create(
        self,
        app_name: str,
        platform: str,
        package_name: Optional[str] = None,
        **kwargs
    ) -> tuple[AppInfo, bool]:
        """
        获取或创建应用
        
        Args:
            app_name: 应用名称
            platform: 平台
            package_name: 包名
            **kwargs: 其他字段
            
        Returns:
            (应用实例, 是否新创建)
        """
        # 优先用包名查找
        if package_name:
            app = await self.get_by_package_name(package_name)
            if app:
                return app, False
        
        # 用名称和平台查找
        app = await self.get_by_name_and_platform(app_name, platform)
        if app:
            return app, False
        
        # 创建新应用
        app = AppInfo(
            app_name=app_name,
            platform=platform,
            package_name=package_name,
            **kwargs
        )
        await self.create(app)
        return app, True
