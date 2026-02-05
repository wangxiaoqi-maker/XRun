"""
执行引擎模块

企业级 TypeScript 执行引擎，支持：
- JSON 用例定义 → TypeScript 代码编译
- Android/iOS 分平台模板
- 数据参数化和变量注入
- Vitest 执行和报告生成
"""
from apps.ui_automation.execution.models import (
    # 枚举
    Platform,
    CaseStatus,
    ExecutionStatus,
    ConfigScope,
    DataSourceType,
    CacheStrategy,
    VariableType,
    OnErrorAction,
    # 模型
    TestCaseV2,
    ExecutionConfig,
    DataSet,
    ExecutionRecord,
    GlobalVariable,
    CacheConfig,
)

__all__ = [
    # 枚举
    "Platform",
    "CaseStatus",
    "ExecutionStatus",
    "ConfigScope",
    "DataSourceType",
    "CacheStrategy",
    "VariableType",
    "OnErrorAction",
    # 模型
    "TestCaseV2",
    "ExecutionConfig",
    "DataSet",
    "ExecutionRecord",
    "GlobalVariable",
    "CacheConfig",
]
