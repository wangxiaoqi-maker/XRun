"""
解析器模块

负责解析变量、元素引用、用例引用等
"""
from apps.ui_automation.execution.compiler.resolvers.variable_resolver import VariableResolver
from apps.ui_automation.execution.compiler.resolvers.element_resolver import ElementResolver

__all__ = [
    "VariableResolver",
    "ElementResolver",
]
