"""
步骤生成策略基类

定义步骤代码生成的接口，使用策略模式实现扩展性
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseStepStrategy(ABC):
    """
    步骤生成策略基类
    
    使用策略模式，每种步骤类型对应一个具体策略
    """
    
    @property
    @abstractmethod
    def step_type(self) -> str:
        """步骤类型标识"""
        pass
    
    @abstractmethod
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        """
        生成步骤代码
        
        Args:
            step: 步骤定义
            context: 编译上下文 {platform, variables, ...}
            
        Returns:
            生成的 TypeScript 代码
        """
        pass
    
    def validate(self, step: dict[str, Any]) -> list[str]:
        """
        验证步骤定义
        
        Args:
            step: 步骤定义
            
        Returns:
            错误信息列表（空表示验证通过）
        """
        return []
    
    def _escape_string(self, value: str) -> str:
        """转义字符串中的特殊字符"""
        if not value:
            return ""
        return (
            value
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
    
    def _resolve_locator(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        """
        解析定位描述
        
        优先使用 elementRef 中的 midscene_locator，否则使用 locator
        """
        # 优先使用元素引用
        element_ref = step.get("elementRef")
        if element_ref:
            # 从上下文中获取解析后的 locator
            resolved = context.get("resolved_elements", {}).get(element_ref.get("elementId"))
            if resolved:
                return self._escape_string(resolved)
            # 回退到元素名称
            return self._escape_string(element_ref.get("elementName", ""))
        
        # 使用直接定位
        locator = step.get("locator", "")
        
        # 变量替换 ${varName} -> ${varName}（保持原样，由 TS 运行时处理）
        return self._escape_string(locator)
    
    def _generate_options(self, step: dict[str, Any], include_keys: list[str] | None = None) -> str:
        """
        生成选项对象字符串
        
        Args:
            step: 步骤定义
            include_keys: 要包含的选项键（None 表示全部）
        """
        options = step.get("options", {})
        if not options:
            return ""
        
        parts = []
        for key, value in options.items():
            if include_keys and key not in include_keys:
                continue
            
            if isinstance(value, bool):
                parts.append(f"{key}: {str(value).lower()}")
            elif isinstance(value, (int, float)):
                parts.append(f"{key}: {value}")
            elif isinstance(value, str):
                parts.append(f"{key}: '{self._escape_string(value)}'")
            elif value is None:
                continue
            else:
                # JSON 对象
                import json
                parts.append(f"{key}: {json.dumps(value)}")
        
        if not parts:
            return ""
        
        return "{ " + ", ".join(parts) + " }"
