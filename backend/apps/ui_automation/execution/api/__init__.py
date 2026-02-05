"""
执行引擎 API 路由模块
"""
from apps.ui_automation.execution.api.cases_v2 import router as cases_router
from apps.ui_automation.execution.api.config_v2 import router as config_router
from apps.ui_automation.execution.api.execution_v2 import router as execution_router
from apps.ui_automation.execution.api.suites import router as suites_router

__all__ = [
    "cases_router",
    "config_router",
    "execution_router",
    "suites_router",
]
