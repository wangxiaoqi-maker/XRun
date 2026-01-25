"""
AI 配置 Schema
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AIConfigCreate(BaseModel):
    """创建 AI 配置"""
    name: str
    base_url: str
    api_key: str
    model_name: str
    model_family: Optional[str] = None
    description: Optional[str] = None

class AIConfigUpdate(BaseModel):
    """更新 AI 配置"""
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    model_family: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AIConfigResponse(BaseModel):
    """AI 配置响应"""
    id: str
    name: str
    base_url: str
    api_key: str  # 返回时会脱敏
    model_name: str
    model_family: Optional[str]
    is_active: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AIConfigList(BaseModel):
    """AI 配置列表"""
    items: List[AIConfigResponse]

