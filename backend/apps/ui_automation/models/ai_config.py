"""
AI 模型配置
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from apps.ui_automation.database import Base

class AIConfig(Base):
    """AI 模型配置表"""
    __tablename__ = "ai_configs"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)  # 配置名称
    base_url = Column(String(500), nullable=False)  # API 地址
    api_key = Column(String(500), nullable=False)  # API Key（加密存储）
    model_name = Column(String(100), nullable=False)  # 模型名称
    model_family = Column(String(100), nullable=True)  # 模型系列
    is_active = Column(Boolean, default=False)  # 是否激活
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

