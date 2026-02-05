"""
测试套件/目录 Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TestSuiteCreate(BaseModel):
    """创建套件请求"""
    name: str = Field(..., min_length=1, max_length=200, description="套件名称")
    description: str | None = Field(None, description="描述")
    parent_id: str | None = Field(None, alias="parentId", description="父目录 ID")
    project_id: str | None = Field(None, alias="projectId", description="项目 ID")
    
    model_config = ConfigDict(populate_by_name=True)


class TestSuiteUpdate(BaseModel):
    """更新套件请求"""
    name: str | None = Field(None, min_length=1, max_length=200, description="套件名称")
    description: str | None = Field(None, description="描述")
    parent_id: str | None = Field(None, alias="parentId", description="父目录 ID")
    sort_order: int | None = Field(None, alias="sortOrder", description="排序顺序")
    
    model_config = ConfigDict(populate_by_name=True)


class TestSuiteResponse(BaseModel):
    """套件响应"""
    id: str
    name: str
    description: str | None = None
    parent_id: str | None = Field(None, alias="parentId")
    project_id: str | None = Field(None, alias="projectId")
    sort_order: int = Field(0, alias="sortOrder")
    depth: int = 0
    path: str | None = None
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    created_by: str | None = Field(None, alias="createdBy")
    
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class TestSuiteTreeNode(BaseModel):
    """套件树节点"""
    id: str
    name: str
    description: str | None = None
    parent_id: str | None = Field(None, alias="parentId")
    depth: int = 0
    sort_order: int = Field(0, alias="sortOrder")
    has_children: bool = Field(False, alias="hasChildren")
    children: list["TestSuiteTreeNode"] = []
    case_count: int = Field(0, alias="caseCount", description="用例数量")
    
    model_config = ConfigDict(populate_by_name=True)
