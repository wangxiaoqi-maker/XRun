"""
元素解析器

负责从知识库中解析元素引用，获取 midscene_locator
"""
from typing import Any, Protocol


class KnowledgeServiceProtocol(Protocol):
    """知识库服务协议（依赖倒置）"""
    
    async def get_element_by_id(self, element_id: str) -> Any | None:
        """根据 ID 获取元素"""
        ...


class ElementResolver:
    """
    元素解析器
    
    从知识库中解析元素引用，获取最佳的 Midscene 定位描述
    """
    
    def __init__(self, knowledge_service: KnowledgeServiceProtocol | None = None) -> None:
        """
        初始化
        
        Args:
            knowledge_service: 知识库服务（依赖注入）
        """
        self._knowledge_service = knowledge_service
        self._cache: dict[str, str] = {}
    
    def set_knowledge_service(self, service: KnowledgeServiceProtocol) -> None:
        """设置知识库服务"""
        self._knowledge_service = service
    
    async def resolve(self, element_ref: dict[str, Any]) -> str:
        """
        解析元素引用
        
        Args:
            element_ref: 元素引用 {elementId, elementName, pageId, pageName}
            
        Returns:
            Midscene 定位描述
        """
        element_id = element_ref.get("elementId", "")
        
        if not element_id:
            # 没有 ID，返回元素名称作为回退
            return element_ref.get("elementName", "")
        
        # 检查缓存
        if element_id in self._cache:
            return self._cache[element_id]
        
        # 从知识库获取
        if self._knowledge_service:
            try:
                element = await self._knowledge_service.get_element_by_id(element_id)
                if element:
                    # 优先使用 midscene_locator
                    locator = getattr(element, "midscene_locator", None)
                    if locator:
                        self._cache[element_id] = locator
                        return locator
                    
                    # 回退到 description
                    desc = getattr(element, "description", None)
                    if desc:
                        self._cache[element_id] = desc
                        return desc
            except Exception as e:
                # 记录错误但不中断编译
                print(f"Warning: Failed to resolve element {element_id}: {e}")
        
        # 最终回退到元素名称
        fallback = element_ref.get("elementName", element_id)
        self._cache[element_id] = fallback
        return fallback
    
    async def resolve_all(self, steps: list[dict[str, Any]]) -> dict[str, str]:
        """
        批量解析所有步骤中的元素引用
        
        Args:
            steps: 步骤列表
            
        Returns:
            元素 ID 到定位描述的映射
        """
        result: dict[str, str] = {}
        
        for step in steps:
            element_ref = step.get("elementRef")
            if element_ref:
                element_id = element_ref.get("elementId", "")
                if element_id and element_id not in result:
                    result[element_id] = await self.resolve(element_ref)
            
            # 递归处理嵌套步骤
            for nested_key in ["thenSteps", "elseSteps", "bodySteps", "trySteps", "catchSteps", "finallySteps"]:
                nested_steps = step.get(nested_key, [])
                if nested_steps:
                    nested_result = await self.resolve_all(nested_steps)
                    result.update(nested_result)
        
        return result
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
