"""
执行引擎数据库模型

包含用例、执行配置、数据集、执行记录等核心模型
"""
from apps.ui_automation.execution.models.enums import (
    Platform,
    CaseStatus,
    ExecutionStatus,
    ConfigScope,
    DataSourceType,
    CacheStrategy,
    VariableType,
    OnErrorAction,
)
from apps.ui_automation.execution.models.test_case import TestCaseV2
from apps.ui_automation.execution.models.test_suite import TestSuite
from apps.ui_automation.execution.models.execution_config import ExecutionConfig
from apps.ui_automation.execution.models.data_set import DataSet
from apps.ui_automation.execution.models.execution_record import ExecutionRecord
from apps.ui_automation.execution.models.global_variable import GlobalVariable
from apps.ui_automation.execution.models.cache_config import CacheConfig

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
    "TestSuite",
    "ExecutionConfig",
    "DataSet",
    "ExecutionRecord",
    "GlobalVariable",
    "CacheConfig",
]
