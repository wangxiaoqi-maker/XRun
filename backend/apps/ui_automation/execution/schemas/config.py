"""
配置相关 Pydantic 模式
"""
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from apps.ui_automation.execution.models.enums import ConfigScope, CacheStrategy, VariableType


class ModelConfigSchema(BaseModel):
    """模型配置"""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str | None = Field(None, description="模型名称")
    base_url: str | None = Field(None, alias="baseUrl", description="API 地址")
    family: str | None = Field(None, description="模型家族")
    
    # 分任务模型
    planning_name: str | None = Field(None, alias="planningName", description="规划模型")
    insight_name: str | None = Field(None, alias="insightName", description="定位模型")


class ExecutionConfigSchema(BaseModel):
    """执行配置"""
    model_config = ConfigDict(populate_by_name=True)
    
    # 作用域
    scope: ConfigScope = Field(ConfigScope.GLOBAL)
    scope_id: str | None = Field(None, alias="scopeId")
    
    # 超时配置
    test_timeout_ms: int | None = Field(None, alias="testTimeoutMs")
    step_timeout_ms: int | None = Field(None, alias="stepTimeoutMs")
    hook_timeout_ms: int | None = Field(None, alias="hookTimeoutMs")
    wait_timeout_ms: int | None = Field(None, alias="waitTimeoutMs")
    wait_interval_ms: int | None = Field(None, alias="waitIntervalMs")
    
    # 重试配置
    default_retry_count: int | None = Field(None, alias="defaultRetryCount")
    retry_delay_ms: int | None = Field(None, alias="retryDelayMs")
    retry_backoff: bool | None = Field(None, alias="retryBackoff")
    
    # AI 上下文
    ai_action_context: str | None = Field(None, alias="aiActionContext")
    replanning_cycle_limit: int | None = Field(None, alias="replanningCycleLimit")
    
    # 模型配置（注意：不能使用 model_config 作为字段名）
    llm_config: ModelConfigSchema | None = Field(None, alias="modelConfig")
    
    # 执行后操作
    wait_after_action_ms: int | None = Field(None, alias="waitAfterActionMs")
    auto_dismiss_keyboard: bool | None = Field(None, alias="autoDismissKeyboard")
    
    # 报告配置
    generate_report: bool | None = Field(None, alias="generateReport")


class GlobalVariableSchema(BaseModel):
    """全局变量"""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, max_length=100, description="变量名")
    value: str | None = Field(None, description="变量值")
    value_type: VariableType = Field(VariableType.STRING, alias="valueType")
    is_secret: bool = Field(False, alias="isSecret", description="是否敏感数据")
    description: str | None = Field(None, description="描述")
    
    # 作用域
    scope: ConfigScope = Field(ConfigScope.GLOBAL)
    scope_id: str | None = Field(None, alias="scopeId")


class GlobalVariableListResponse(BaseModel):
    """全局变量列表响应"""
    total: int
    items: list[dict[str, Any]]


class CacheConfigSchema(BaseModel):
    """缓存配置"""
    model_config = ConfigDict(populate_by_name=True)
    
    scope: ConfigScope = Field(ConfigScope.GLOBAL)
    scope_id: str | None = Field(None, alias="scopeId")
    
    strategy: CacheStrategy = Field(CacheStrategy.DISABLED)
    cache_id_pattern: str | None = Field(None, alias="cacheIdPattern")
    cache_dir: str | None = Field(None, alias="cacheDir")
    auto_cleanup: bool = Field(False, alias="autoCleanup")
    cleanup_after_days: str | None = Field(None, alias="cleanupAfterDays")
