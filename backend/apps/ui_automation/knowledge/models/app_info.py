"""
应用信息模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship

from .base import KnowledgeBase


class AppInfo(KnowledgeBase):
    """应用信息表 - 存储被测应用的基本信息"""
    __tablename__ = 'kb_app_info'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 应用基本信息
    app_name = Column(String(100), nullable=False, index=True, comment="应用名称")
    package_name = Column(String(200), unique=True, comment="包名（Android）或 Bundle ID（iOS）")
    platform = Column(String(20), nullable=False, comment="平台：android/ios")
    version = Column(String(50), comment="App 版本号")
    
    # 扩展信息
    icon_path = Column(String(500), comment="应用图标路径")
    description = Column(Text, comment="应用描述")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系：一个应用有多个页面
    pages = relationship(
        "PageAnalysis", 
        back_populates="app", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<AppInfo(id={self.id}, name={self.app_name}, platform={self.platform})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "app_name": self.app_name,
            "package_name": self.package_name,
            "platform": self.platform,
            "version": self.version,
            "icon_path": self.icon_path,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
