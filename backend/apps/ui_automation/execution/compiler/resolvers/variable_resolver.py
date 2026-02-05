"""
变量解析器

负责解析和合并各级变量：全局变量 -> 用例变量 -> 数据集变量 -> 运行时变量
"""
from typing import Any
from apps.ui_automation.execution.models.enums import VariableType


class VariableResolver:
    """
    变量解析器
    
    支持多级变量覆盖和类型转换
    """
    
    def __init__(self) -> None:
        """初始化"""
        self._global_vars: dict[str, Any] = {}
        self._case_vars: dict[str, Any] = {}
        self._data_vars: dict[str, Any] = {}
        self._runtime_vars: dict[str, Any] = {}
    
    def set_global_variables(self, variables: list[dict[str, Any]]) -> None:
        """
        设置全局变量
        
        Args:
            variables: 全局变量列表 [{name, value, value_type, is_secret}]
        """
        self._global_vars = {}
        for var in variables:
            name = var.get("name", "")
            if name:
                self._global_vars[name] = self._convert_value(
                    var.get("value"),
                    var.get("value_type", VariableType.STRING.value)
                )
    
    def set_case_variables(self, variables: list[dict[str, Any]] | None) -> None:
        """
        设置用例输入变量的默认值
        
        Args:
            variables: 用例变量定义 [{name, type, defaultValue}]
        """
        self._case_vars = {}
        if not variables:
            return
        
        for var in variables:
            name = var.get("name", "")
            default_value = var.get("defaultValue")
            if name and default_value is not None:
                self._case_vars[name] = self._convert_value(
                    default_value,
                    var.get("type", "string")
                )
    
    def set_data_row(self, data_row: dict[str, Any] | None) -> None:
        """
        设置数据驱动的当前行数据
        
        Args:
            data_row: 数据行 {col1: val1, col2: val2}
        """
        self._data_vars = data_row or {}
    
    def set_runtime_variables(self, variables: dict[str, Any] | None) -> None:
        """
        设置运行时传入的变量覆盖
        
        Args:
            variables: 运行时变量 {name: value}
        """
        self._runtime_vars = variables or {}
    
    def resolve(self, name: str) -> Any:
        """
        解析变量值
        
        优先级：运行时 > 数据集 > 用例默认值 > 全局
        
        Args:
            name: 变量名
            
        Returns:
            变量值（如果找不到返回 None）
        """
        # 按优先级查找
        if name in self._runtime_vars:
            return self._runtime_vars[name]
        if name in self._data_vars:
            return self._data_vars[name]
        if name in self._case_vars:
            return self._case_vars[name]
        if name in self._global_vars:
            return self._global_vars[name]
        
        return None
    
    def resolve_all(self) -> dict[str, Any]:
        """
        解析所有变量
        
        Returns:
            合并后的变量字典
        """
        result = {}
        
        # 按优先级合并（低优先级在前，高优先级覆盖）
        result.update(self._global_vars)
        result.update(self._case_vars)
        result.update(self._data_vars)
        result.update(self._runtime_vars)
        
        return result
    
    def to_env_dict(self) -> dict[str, str]:
        """
        转换为环境变量字典
        
        环境变量名格式: VAR_{NAME}
        
        Returns:
            环境变量字典
        """
        result = {}
        for name, value in self.resolve_all().items():
            env_name = f"VAR_{name.upper()}"
            result[env_name] = str(value) if value is not None else ""
        
        return result
    
    def get_variable_definitions(self) -> list[dict[str, Any]]:
        """
        获取变量定义（用于模板渲染）
        
        Returns:
            变量定义列表 [{name, default_value}]
        """
        all_vars = self.resolve_all()
        return [
            {"name": name, "default_value": str(value) if value is not None else ""}
            for name, value in all_vars.items()
        ]
    
    def _convert_value(self, value: Any, value_type: str) -> Any:
        """转换变量值类型"""
        if value is None:
            return None
        
        if value_type == VariableType.NUMBER.value or value_type == "number":
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return value
        
        elif value_type == VariableType.BOOLEAN.value or value_type == "boolean":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes")
        
        elif value_type == VariableType.JSON.value or value_type == "json":
            if isinstance(value, (dict, list)):
                return value
            import json
            try:
                return json.loads(str(value))
            except json.JSONDecodeError:
                return value
        
        # 默认字符串
        return str(value)
