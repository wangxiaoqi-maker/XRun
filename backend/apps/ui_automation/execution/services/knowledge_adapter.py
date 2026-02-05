"""
知识库适配器

将知识库服务适配为执行引擎可用的接口
实现依赖倒置原则，解耦执行引擎与知识库
"""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.ui_automation.knowledge.models.page_element import PageElement


class KnowledgeAdapter:
    """
    知识库适配器
    
    为执行引擎提供知识库访问能力，实现以下功能：
    - 根据 ID 获取元素信息
    - 根据名称搜索元素
    - 批量获取元素
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        初始化适配器
        
        Args:
            session: 异步数据库会话
        """
        self._session = session
    
    async def get_element_by_id(self, element_id: str) -> PageElement | None:
        """
        根据 ID 获取元素
        
        Args:
            element_id: 元素 ID
            
        Returns:
            元素对象或 None
        """
        result = await self._session.execute(
            select(PageElement).where(PageElement.id == element_id)
        )
        return result.scalar_one_or_none()
    
    async def get_elements_by_ids(self, element_ids: list[str]) -> dict[str, PageElement]:
        """
        批量获取元素
        
        Args:
            element_ids: 元素 ID 列表
            
        Returns:
            ID -> 元素对象的映射
        """
        if not element_ids:
            return {}
        
        result = await self._session.execute(
            select(PageElement).where(PageElement.id.in_(element_ids))
        )
        elements = result.scalars().all()
        
        return {e.id: e for e in elements}
    
    async def search_elements_by_name(
        self,
        page_id: str,
        element_name: str,
    ) -> list[PageElement]:
        """
        根据名称在页面中搜索元素
        
        Args:
            page_id: 页面 ID
            element_name: 元素名称（支持模糊匹配）
            
        Returns:
            匹配的元素列表
        """
        result = await self._session.execute(
            select(PageElement).where(
                PageElement.page_id == page_id,
                PageElement.element_name.contains(element_name),
            )
        )
        return list(result.scalars().all())
    
    async def get_elements_by_page(self, page_id: str) -> list[PageElement]:
        """
        获取页面的所有元素
        
        Args:
            page_id: 页面 ID
            
        Returns:
            元素列表
        """
        result = await self._session.execute(
            select(PageElement).where(PageElement.page_id == page_id)
        )
        return list(result.scalars().all())
    
    async def get_locator(self, element_id: str) -> str | None:
        """
        获取元素的最佳定位描述
        
        优先返回 midscene_locator，其次是 description，最后是 element_name
        
        Args:
            element_id: 元素 ID
            
        Returns:
            定位描述字符串或 None
        """
        element = await self.get_element_by_id(element_id)
        
        if not element:
            return None
        
        # 优先级：midscene_locator > description > element_name
        if element.midscene_locator:
            return element.midscene_locator
        if element.description:
            return element.description
        return element.element_name
    
    async def get_locators_batch(self, element_ids: list[str]) -> dict[str, str]:
        """
        批量获取元素的定位描述
        
        Args:
            element_ids: 元素 ID 列表
            
        Returns:
            ID -> 定位描述的映射
        """
        elements = await self.get_elements_by_ids(element_ids)
        
        result = {}
        for element_id, element in elements.items():
            if element.midscene_locator:
                result[element_id] = element.midscene_locator
            elif element.description:
                result[element_id] = element.description
            else:
                result[element_id] = element.element_name
        
        return result
    
    def to_element_info(self, element: PageElement) -> dict[str, Any]:
        """
        转换为前端使用的元素信息格式
        
        Args:
            element: 元素对象
            
        Returns:
            元素信息字典
        """
        return {
            "id": element.id,
            "name": element.element_name,
            "type": element.element_type,
            "locator": element.midscene_locator or element.description or element.element_name,
            "textContent": element.text_content,
            "position": element.position_area,
            "bbox": element.bbox,
            "cropImageUrl": element.crop_image_url,
            "isNavigation": element.is_navigation,
            "targetPageId": element.target_page_id,
            "targetPageName": element.target_page_name,
            "pageId": element.page_id,
        }
