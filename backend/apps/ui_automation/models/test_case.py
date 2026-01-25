"""
测试用例模型
"""
from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from apps.ui_automation.database import Base
import enum

class Platform(str, enum.Enum):
    ANDROID = "android"
    IOS = "ios"

class TestCase(Base):
    """测试用例表"""
    __tablename__ = "test_cases"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    platform = Column(String(20), nullable=False)  # android / ios
    yaml_content = Column(Text, nullable=False)  # YAML 格式的用例内容
    tags = Column(Text, nullable=True)  # JSON 格式的标签
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
