"""
知识库数据模型层

包含以下模型：
- AppInfo: 应用信息
- PageAnalysis: 页面分析结果
- PageElement: 页面元素
- ElementRelation: 元素空间关系
- PageTransition: 页面跳转关系
"""
from .base import KnowledgeBase
from .app_info import AppInfo
from .page_analysis import PageAnalysis
from .page_element import PageElement, ElementRelation
from .page_transition import PageTransition
from .enums import ElementType, RelationType, PageType, Platform

__all__ = [
    "KnowledgeBase",
    "AppInfo",
    "PageAnalysis", 
    "PageElement",
    "ElementRelation",
    "PageTransition",
    "ElementType",
    "RelationType",
    "PageType",
    "Platform",
]
