"""
执行相关 Pydantic 模式
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from apps.ui_automation.execution.models.enums import Platform, ExecutionStatus


class ExecutionRequest(BaseModel):
    """执行请求"""
    model_config = ConfigDict(populate_by_name=True)
    
    case_id: str = Field(..., alias="caseId", description="用例 ID")
    device_id: str = Field(..., alias="deviceId", description="设备 ID")
    
    # 变量覆盖
    variables: dict[str, Any] | None = Field(None, description="变量覆盖")
    
    # 配置覆盖
    config_overrides: dict[str, Any] | None = Field(None, alias="configOverrides", description="配置覆盖")
    
    # 数据驱动
    data_row_index: int | None = Field(None, alias="dataRowIndex", description="数据行索引（-1 表示全部）")


class SuiteExecutionRequest(BaseModel):
    """套件执行请求"""
    model_config = ConfigDict(populate_by_name=True)
    
    suite_id: str = Field(..., alias="suiteId", description="套件 ID")
    device_id: str = Field(..., alias="deviceId", description="设备 ID")
    
    # 变量覆盖
    variables: dict[str, Any] | None = Field(None, description="变量覆盖")
    
    # 配置覆盖
    config_overrides: dict[str, Any] | None = Field(None, alias="configOverrides")
    
    # 并行执行
    parallel: bool = Field(False, description="是否并行执行")


class ExecutionResponse(BaseModel):
    """执行响应"""
    model_config = ConfigDict(populate_by_name=True)
    
    execution_id: str = Field(..., alias="executionId", description="执行记录 ID")
    status: str = Field(..., description="状态")
    websocket_url: str = Field(..., alias="websocketUrl", description="WebSocket 日志地址")
    estimated_duration: int | None = Field(None, alias="estimatedDuration", description="预估时长（毫秒）")


class StepResultSchema(BaseModel):
    """步骤执行结果"""
    model_config = ConfigDict(populate_by_name=True)
    
    step_id: str = Field(..., alias="stepId")
    step_name: str | None = Field(None, alias="stepName")
    status: str
    duration_ms: int | None = Field(None, alias="durationMs")
    error: str | None = None
    screenshot_url: str | None = Field(None, alias="screenshotUrl")


class ExecutionStatusResponse(BaseModel):
    """执行状态响应"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
    id: str
    case_id: str = Field(..., alias="caseId")
    device_id: str = Field(..., alias="deviceId")
    device_name: str | None = Field(None, alias="deviceName")
    platform: str
    
    status: str
    started_at: datetime | None = Field(None, alias="startedAt")
    finished_at: datetime | None = Field(None, alias="finishedAt")
    duration_ms: int | None = Field(None, alias="durationMs")
    
    # 结果
    report_url: str | None = Field(None, alias="reportUrl")
    error_message: str | None = Field(None, alias="errorMessage")
    
    # 步骤统计
    total_steps: int | None = Field(None, alias="totalSteps")
    passed_steps: int | None = Field(None, alias="passedSteps")
    failed_steps: int | None = Field(None, alias="failedSteps")
    skipped_steps: int | None = Field(None, alias="skippedSteps")
    
    # 步骤详情
    steps_result: list[StepResultSchema] | None = Field(None, alias="stepsResult")
