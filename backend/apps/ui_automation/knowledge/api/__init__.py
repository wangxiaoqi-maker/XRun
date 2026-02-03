"""
知识库 API 路由
"""
from .page_analysis import router as page_analysis_router
from .exploration import router as exploration_router
from .module import router as module_router

# 主路由（兼容旧的导入方式）
router = page_analysis_router

__all__ = ["router", "page_analysis_router", "exploration_router", "module_router"]
