"""
测试用例 Pydantic 模式
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from apps.ui_automation.execution.models.enums import Platform, CaseStatus, Priority, OnErrorAction


class ElementRefSchema(BaseModel):
    """元素引用"""
    model_config = ConfigDict(populate_by_name=True)
    
    element_id: str = Field(..., alias="elementId", description="元素 ID")
    element_name: str = Field(..., alias="elementName", description="元素名称")
    page_id: str = Field(..., alias="pageId", description="页面 ID")
    page_name: str = Field(..., alias="pageName", description="页面名称")


class StepOptionsSchema(BaseModel):
    """步骤选项"""
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    deep_think: bool | None = Field(None, alias="deepThink", description="深度思考")
    cacheable: bool | None = Field(None, description="是否可缓存")
    timeout_ms: int | None = Field(None, alias="timeoutMs", description="超时时间")


class StepSchema(BaseModel):
    """步骤定义"""
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(..., description="步骤 ID")
    type: str = Field(..., description="步骤类型")
    name: str | None = Field(None, description="步骤名称")
    
    # 定位
    locator: str | None = Field(None, description="定位描述")
    element_ref: ElementRefSchema | None = Field(None, alias="elementRef", description="元素引用")
    
    # 步骤参数
    value: str | None = Field(None, description="输入值（aiInput）")
    mode: str | None = Field(None, description="输入模式（replace/clear/typeOnly）")
    prompt: str | None = Field(None, description="AI 提示词（aiAct/aiQuery）")
    query: str | None = Field(None, description="查询表达式（aiQuery）")
    assertion: str | None = Field(None, description="断言描述（aiAssert/aiWaitFor）")
    output_var: str | None = Field(None, alias="outputVar", description="输出变量名")
    
    # 选项
    options: StepOptionsSchema | None = Field(None, description="步骤选项")
    
    # 错误处理
    on_error: OnErrorAction | None = Field(None, alias="onError", description="错误处理动作")
    retry_count: int | None = Field(None, alias="retryCount", description="重试次数")
    retry_delay_ms: int | None = Field(None, alias="retryDelayMs", description="重试间隔")
    
    # 嵌套步骤（条件/循环/try-catch）
    then_steps: list["StepSchema"] | None = Field(None, alias="thenSteps")
    else_steps: list["StepSchema"] | None = Field(None, alias="elseSteps")
    body_steps: list["StepSchema"] | None = Field(None, alias="bodySteps")
    try_steps: list["StepSchema"] | None = Field(None, alias="trySteps")
    catch_steps: list["StepSchema"] | None = Field(None, alias="catchSteps")
    finally_steps: list["StepSchema"] | None = Field(None, alias="finallySteps")


class VariableSchema(BaseModel):
    """变量定义"""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., description="变量名")
    type: str = Field("string", description="变量类型")
    required: bool = Field(False, description="是否必填")
    default_value: str | None = Field(None, alias="defaultValue", description="默认值")
    description: str | None = Field(None, description="变量描述")


class RefCaseSchema(BaseModel):
    """用例引用"""
    model_config = ConfigDict(populate_by_name=True)
    
    case_id: str = Field(..., alias="caseId", description="用例 ID")
    alias: str | None = Field(None, description="别名")
    input_mapping: dict[str, str] | None = Field(None, alias="inputMapping", description="输入映射")


class TestCaseCreateRequest(BaseModel):
    """创建用例请求"""
    name: str = Field(..., min_length=1, max_length=200, description="用例名称")
    description: str | None = Field(None, description="用例描述")
    app_id: str = Field(..., description="应用 ID")
    project_id: str | None = Field(None, description="项目 ID")
    suite_id: str | None = Field(None, description="套件 ID")
    platform: Platform = Field(..., description="目标平台")
    
    steps_json: list[StepSchema] = Field(..., description="步骤列表")
    input_variables: list[VariableSchema] | None = Field(None, description="输入变量")
    refs: list[RefCaseSchema] | None = Field(None, description="引用用例")
    
    config_override: dict[str, Any] | None = Field(None, description="配置覆盖")
    data_set_id: str | None = Field(None, description="数据集 ID")
    launch_target: str | None = Field(None, description="启动目标")
    
    tags: list[str] | None = Field(None, description="标签")
    priority: Priority = Field(Priority.MEDIUM, description="优先级")


class TestCaseUpdateRequest(BaseModel):
    """更新用例请求"""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    
    steps_json: list[StepSchema] | None = None
    input_variables: list[VariableSchema] | None = None
    refs: list[RefCaseSchema] | None = None
    
    config_override: dict[str, Any] | None = None
    data_set_id: str | None = None
    launch_target: str | None = None
    
    tags: list[str] | None = None
    priority: Priority | None = None
    status: CaseStatus | None = None


class TestCaseResponse(BaseModel):
    """用例响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: str | None
    app_id: str
    project_id: str | None
    suite_id: str | None
    platform: str
    
    steps_json: list[dict[str, Any]]
    input_variables: list[dict[str, Any]] | None
    refs: list[dict[str, Any]] | None
    
    config_override: dict[str, Any] | None
    data_set_id: str | None
    launch_target: str | None
    
    tags: list[str] | None
    priority: str
    status: str
    version: str
    
    step_count: int
    variable_names: list[str]
    
    created_at: datetime | None
    updated_at: datetime | None
    created_by: str | None


class TestCaseListResponse(BaseModel):
    """用例列表响应"""
    total: int
    items: list[TestCaseResponse]
    page: int
    page_size: int
