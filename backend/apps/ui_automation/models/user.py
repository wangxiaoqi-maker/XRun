"""
用户模型
"""
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship

from ..database import Base

# 北京时间 UTC+8
def beijing_now():
    return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"      # 管理员
    USER = "user"        # 普通用户


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=True, index=True, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    nickname = Column(String(50), comment="昵称")
    avatar = Column(String(500), comment="头像 URL")
    role = Column(SQLEnum(UserRole), default=UserRole.USER, comment="用户角色")
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_login = Column(DateTime, comment="最后登录时间")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, comment="更新时间")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "nickname": self.nickname or self.username,
            "avatar": self.avatar,
            "role": self.role.value,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        return data
