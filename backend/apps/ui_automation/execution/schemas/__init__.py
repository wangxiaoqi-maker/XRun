"""
执行引擎 Pydantic 模式

用于 API 请求/响应验证
"""
from apps.ui_automation.execution.schemas.test_case import (
    StepSchema,
    VariableSchema,
    ElementRefSchema,
    TestCaseCreateRequest,
    TestCaseUpdateRequest,
    TestCaseResponse,
    TestCaseListResponse,
)
from apps.ui_automation.execution.schemas.execution import (
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatusResponse,
)
from apps.ui_automation.execution.schemas.config import (
    ExecutionConfigSchema,
    GlobalVariableSchema,
    CacheConfigSchema,
)

__all__ = [
    # 用例
    "StepSchema",
    "VariableSchema",
    "ElementRefSchema",
    "TestCaseCreateRequest",
    "TestCaseUpdateRequest",
    "TestCaseResponse",
    "TestCaseListResponse",
    # 执行
    "ExecutionRequest",
    "ExecutionResponse",
    "ExecutionStatusResponse",
    # 配置
    "ExecutionConfigSchema",
    "GlobalVariableSchema",
    "CacheConfigSchema",
]
