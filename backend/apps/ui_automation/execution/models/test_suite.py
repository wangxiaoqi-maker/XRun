"""
测试套件/目录模型

支持多级目录结构，用于组织测试用例
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from apps.ui_automation.database import Base


class TestSuite(Base):
    """测试套件/目录"""
    __tablename__ = "test_suite"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    name = Column(String(200), nullable=False, comment="套件/目录名称")
    description = Column(Text, comment="描述")
    
    # 层级结构
    parent_id = Column(String(36), ForeignKey("test_suite.id", ondelete="CASCADE"), index=True, comment="父目录 ID")
    project_id = Column(String(36), index=True, comment="所属项目 ID")
    
    # 排序和深度
    sort_order = Column(Integer, default=0, comment="排序顺序")
    depth = Column(Integer, default=0, comment="目录深度，根目录为 0")
    path = Column(String(500), comment="完整路径，如: /root/sub1/sub2")
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    created_by = Column(String(100), comment="创建人")
    
    # 关系 - 自引用父子关系
    children = relationship(
        "TestSuite",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )
    parent = relationship(
        "TestSuite",
        back_populates="children",
        remote_side=[id],
        foreign_keys=[parent_id]
    )
    
    __table_args__ = (
        Index("idx_suite_project_parent", "project_id", "parent_id"),
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parentId": self.parent_id,
            "projectId": self.project_id,
            "sortOrder": self.sort_order,
            "depth": self.depth,
            "path": self.path,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "createdBy": self.created_by
        }
    
    def to_tree_node(self, children_list: list = None) -> dict:
        """转换为树节点格式"""
        node = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parentId": self.parent_id,
            "depth": self.depth,
            "sortOrder": self.sort_order,
            "hasChildren": bool(children_list),
            "children": children_list or []
        }
        return node
