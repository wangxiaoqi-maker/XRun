"""
大模型配置与用量统计数据模型
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from apps.ui_automation.database import Base


class ModelType(str, Enum):
    """模型类型"""
    CHAT = "chat"           # 对话模型
    VISION = "vision"       # 视觉模型
    EMBEDDING = "embedding" # 向量模型


class ModelStatus(str, Enum):
    """模型状态"""
    ENABLED = "enabled"
    DISABLED = "disabled"


class LLMProvider(Base):
    """
    大模型供应商配置
    对应图片中的"模型供应商"页面
    """
    __tablename__ = "llm_providers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="供应商名称，如：OpenAI、智谱、通义")
    code = Column(String(50), unique=True, nullable=False, comment="供应商代码，如：openai、zhipu、qwen")
    icon = Column(String(255), comment="图标URL或Base64")
    description = Column(Text, comment="描述")
    
    # API 配置
    base_url = Column(String(500), nullable=False, comment="API Base URL")
    api_key = Column(String(500), comment="API Key（加密存储）")
    litellm_prefix = Column(String(50), default="openai", comment="LiteLLM 路由前缀，如 deepseek、anthropic、openai")
    
    # 状态
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.ENABLED, comment="状态")
    
    # 统计（缓存，定期更新）
    total_requests = Column(Integer, default=0, comment="总请求数")
    total_tokens = Column(Integer, default=0, comment="总Token数")
    success_rate = Column(Float, default=100.0, comment="成功率")
    avg_latency = Column(Float, default=0.0, comment="平均延迟(秒)")
    
    # 时间（使用本地时间）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self, include_key=False):
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "icon": self.icon,
            "description": self.description,
            "base_url": self.base_url,
            "status": self.status.value if self.status else "enabled",
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "success_rate": self.success_rate,
            "avg_latency": self.avg_latency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_key:
            data["api_key"] = self.api_key
        return data


class LLMModel(Base):
    """
    具体模型配置
    一个供应商可以有多个模型
    """
    __tablename__ = "llm_models"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联供应商
    provider_id = Column(String(36), nullable=False, comment="供应商ID")
    
    # 模型信息
    name = Column(String(100), nullable=False, comment="模型显示名称")
    model_id = Column(String(100), nullable=False, comment="模型ID，如：gpt-4、qwen-vl-max")
    model_type = Column(SQLEnum(ModelType), default=ModelType.CHAT, comment="模型类型")
    
    # 能力配置
    context_window = Column(Integer, default=32768, comment="上下文窗口大小(tokens)，如 DeepSeek=65536, GPT-4o=128000")
    max_tokens = Column(Integer, default=4096, comment="最大输出Token数")
    supports_vision = Column(Boolean, default=False, comment="是否支持视觉")
    supports_function_call = Column(Boolean, default=False, comment="是否支持函数调用")
    
    # 价格配置（每1K Token）
    input_price = Column(Float, default=0.0, comment="输入价格")
    output_price = Column(Float, default=0.0, comment="输出价格")
    
    # 图标
    icon = Column(String(500), nullable=True, comment="模型图标URL")
    
    # 状态
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.ENABLED)
    is_default = Column(Boolean, default=False, comment="是否默认模型")
    
    # 额外配置
    config = Column(JSON, comment="额外配置参数")
    
    # 时间（使用本地时间）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "name": self.name,
            "model_id": self.model_id,
            "model_type": self.model_type.value if self.model_type else "chat",
            "context_window": self.context_window,
            "max_tokens": self.max_tokens,
            "supports_vision": self.supports_vision,
            "supports_function_call": self.supports_function_call,
            "input_price": self.input_price,
            "output_price": self.output_price,
            "icon": self.icon,
            "status": self.status.value if self.status else "enabled",
            "is_default": self.is_default,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LLMUsageLog(Base):
    """
    模型调用记录
    用于统计用量
    """
    __tablename__ = "llm_usage_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联
    provider_id = Column(String(36), nullable=False, index=True)
    model_id = Column(String(36), nullable=False, index=True)
    
    # 调用信息
    request_type = Column(String(50), comment="请求类型：analyze_page, generate_case, execute_step")
    
    # Token 统计
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # 性能
    latency_ms = Column(Integer, default=0, comment="延迟(毫秒)")
    success = Column(Boolean, default=True)
    error_message = Column(Text, comment="错误信息")
    
    # 费用
    cost = Column(Float, default=0.0, comment="本次调用费用")
    
    # 时间（使用本地时间）
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "request_type": self.request_type,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_message": self.error_message,
            "cost": self.cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
