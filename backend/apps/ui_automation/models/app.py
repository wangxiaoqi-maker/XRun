"""
应用管理模型
"""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from ..database import Base

# 北京时间 UTC+8
def beijing_now():
    return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)


class AppPlatform(enum.Enum):
    """应用平台"""
    ANDROID = "android"
    IOS = "ios"


class App(Base):
    """被测应用"""
    __tablename__ = "apps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="应用名称")
    name_en = Column(String(100), nullable=True, comment="英文名称")
    package_name = Column(String(200), nullable=False, unique=True, comment="包名/Bundle ID")
    platform = Column(SQLEnum(AppPlatform), nullable=False, comment="平台")
    icon_url = Column(Text, nullable=True, comment="应用图标URL或Base64")
    
    # 版本信息
    latest_version = Column(String(50), nullable=True, comment="最新版本")
    
    # 自动化配置
    launch_activity = Column(String(200), nullable=True, comment="启动Activity (Android)")
    
    # 统计（可选，也可以实时计算）
    ui_element_count = Column(String(20), default="0", comment="UI元素数量")
    case_count = Column(String(20), default="0", comment="关联用例数")
    
    # 项目关联
    project_id = Column(String(36), nullable=True, comment="所属项目ID")
    
    # 元数据
    description = Column(Text, nullable=True, comment="应用描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(String(36), nullable=True, comment="创建人ID")
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "package_name": self.package_name,
            "platform": self.platform.value if self.platform else None,
            "icon_url": self.icon_url,
            "latest_version": self.latest_version,
            "launch_activity": self.launch_activity,
            "ui_element_count": self.ui_element_count,
            "case_count": self.case_count,
            "project_id": self.project_id,
            "description": self.description,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
