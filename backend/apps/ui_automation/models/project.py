"""
项目模型
"""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base

# 北京时间 UTC+8
def beijing_now():
    return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)


class Project(Base):
    """项目表"""
    __tablename__ = 'projects'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="项目名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="项目代码（唯一标识）")
    description = Column(Text, comment="项目描述")
    icon = Column(String(50), default="📁", comment="项目图标（emoji）")
    color = Column(String(20), default="#184BFA", comment="项目主题色")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(String(36), ForeignKey('users.id'), comment="创建人ID")
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)
    
    # 关联
    creator = relationship("User", foreign_keys=[created_by])
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ProjectMember(Base):
    """项目成员表（用于权限控制）"""
    __tablename__ = 'project_members'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), default="member", comment="角色: owner/admin/member")
    joined_at = Column(DateTime, default=beijing_now)
    
    # 关联
    project = relationship("Project")
    user = relationship("User")
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None
        }
