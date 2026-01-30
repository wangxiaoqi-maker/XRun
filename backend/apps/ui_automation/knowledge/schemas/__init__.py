"""
知识库 API Schema 定义

使用 Pydantic 定义请求/响应模型
"""
from .page_analysis import (
    # 请求
    PageAnalyzeRequest,
    ElementSearchRequest,
    
    # 响应
    PageAnalyzeResponse,
    ElementSearchResponse,
    ElementInfo,
    ElementMatchResult,
    PageSummary,
    AppSummary,
    KnowledgeBaseStats,
)

__all__ = [
    "PageAnalyzeRequest",
    "ElementSearchRequest",
    "PageAnalyzeResponse",
    "ElementSearchResponse",
    "ElementInfo",
    "ElementMatchResult",
    "PageSummary",
    "AppSummary",
    "KnowledgeBaseStats",
]
