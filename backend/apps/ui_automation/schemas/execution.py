"""
执行相关 Schema
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExecutionRequest(BaseModel):
    """执行请求"""
    case_id: str
    device_id: str

class ExecutionResponse(BaseModel):
    """执行响应"""
    id: str
    case_id: str
    device_id: str
    platform: str
    status: str
    logs: Optional[str] = None
    report_path: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExecutionList(BaseModel):
    """执行列表"""
    total: int
    items: List[ExecutionResponse]
