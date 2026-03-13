from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""


class PageResult(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int


# --- Project ---
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    case_count: int = 0
    conversation_count: int = 0

    model_config = {"from_attributes": True}


# --- Test Case ---
class TestCaseOut(BaseModel):
    id: str
    project_id: str
    conversation_id: Optional[str] = None
    module_name: Optional[str] = None
    creator: Optional[str] = None
    case_no: str
    name: str
    description: Optional[str] = None
    test_type: Optional[str] = None
    priority: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Any = None
    tags: Any = None
    review_status: str = "pending"
    review_comment: Optional[str] = None
    quality_scores: Any = None
    source_ref: Any = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TestCaseDetailOut(TestCaseOut):
    """用例详情，用于执行弹窗"""
    updated_at: Optional[datetime] = None
    version: int = 1

class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[str] = None
    priority: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    module_name: Optional[str] = None


# --- Review ---
class ReviewItem(BaseModel):
    case_id: str
    status: str
    comment: Optional[str] = None

class BatchReview(BaseModel):
    reviews: List[ReviewItem]


# --- Export ---
class ExcelExportRequest(BaseModel):
    case_ids: Optional[List[str]] = None
    project_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None

class ExportTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    columns: List[Dict[str, Any]]
    style_config: Optional[Dict[str, Any]] = None

class ExportTemplateOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_default: bool = False
    columns: Any = None
    style_config: Any = None

    model_config = {"from_attributes": True}


# --- File ---
class FileOut(BaseModel):
    id: str
    project_id: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str = "uploaded"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Knowledge ---
class KnowledgeSearchRequest(BaseModel):
    query: str
    project_id: str
    top_k: int = 5


# --- Execution ---
class StepResultItem(BaseModel):
    step: int
    status: str = "pending"
    actual_result: Optional[str] = None
    remark: Optional[str] = None

class ExecutionCreate(BaseModel):
    case_id: str
    project_id: str

class StepResultUpdate(BaseModel):
    status: str
    actual_result: Optional[str] = None
    remark: Optional[str] = None

class ExecutionComplete(BaseModel):
    remark: Optional[str] = None

class ExecutionOut(BaseModel):
    id: str
    project_id: str
    case_id: str
    case_name: Optional[str] = None
    executor: Optional[str] = None
    status: str = "in_progress"
    step_results: Any = None
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    blocked_steps: int = 0
    remark: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
