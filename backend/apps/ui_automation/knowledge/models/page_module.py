"""
页面模块/功能分组模型

支持按业务功能组织页面：
- 转账模块
  - 转账首页
  - 转到银行卡
  - 转到翼支付账户
  - 预约转账
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import KnowledgeBase
from ..utils.timezone import beijing_now_naive


class PageModule(KnowledgeBase):
    """
    页面模块表 - 按功能/业务组织页面
    
    支持层级结构：
    - 一级模块：首页、我的、发现
    - 二级模块：余额、设置
    - 三级模块：转账、充值
    """
    __tablename__ = 'kb_page_module'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联应用
    app_id = Column(
        String(36),
        ForeignKey('kb_app_info.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="关联的应用 ID"
    )
    
    # 父模块（支持层级）
    parent_id = Column(
        String(36),
        ForeignKey('kb_page_module.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
        comment="父模块 ID（NULL 表示顶级模块）"
    )
    
    # 模块信息
    module_name = Column(String(100), nullable=False, comment="模块名称（如：转账、充值）")
    module_code = Column(String(50), index=True, comment="模块代码（如：transfer、recharge）")
    description = Column(Text, comment="模块描述")
    icon = Column(String(100), comment="模块图标（可选）")
    
    # 排序
    sort_order = Column(Integer, default=0, comment="排序顺序")
    
    # 层级深度（方便查询）
    depth = Column(Integer, default=0, comment="层级深度（0=顶级）")
    
    # 路径（物化路径，方便查询所有祖先/后代）
    # 格式：/parent_id/parent_id/current_id/
    path = Column(String(500), index=True, comment="物化路径")
    
    # 时间戳
    created_at = Column(DateTime, default=beijing_now_naive, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now_naive, onupdate=beijing_now_naive, comment="更新时间")
    
    # ========== 关系 ==========
    # 所属应用
    app = relationship("AppInfo", back_populates="modules")
    
    # 父模块
    parent = relationship(
        "PageModule",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id]
    )
    
    # 子模块
    children = relationship(
        "PageModule",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )
    
    # 模块下的页面（使用 lazy="dynamic" 避免自动加载）
    pages = relationship(
        "PageAnalysis",
        back_populates="module",
        foreign_keys="PageAnalysis.module_id",
        lazy="dynamic"
    )
    
    # ========== 索引 ==========
    __table_args__ = (
        Index('idx_module_app_name', 'app_id', 'module_name'),
        Index('idx_module_parent', 'parent_id'),
        Index('idx_module_path', 'path'),
    )
    
    def __repr__(self):
        return f"<PageModule(id={self.id}, name={self.module_name}, depth={self.depth})>"
    
    def to_dict(self, include_children: bool = False, pages_count: int = None) -> dict:
        """
        转换为字典
        
        Args:
            include_children: 是否包含子模块
            pages_count: 页面数量（需要外部传入，避免在异步上下文中访问关系）
        """
        result = {
            "id": self.id,
            "app_id": self.app_id,
            "parent_id": self.parent_id,
            "module_name": self.module_name,
            "module_code": self.module_code,
            "description": self.description,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "depth": self.depth,
            "path": self.path,
            "pages_count": pages_count if pages_count is not None else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_children:
            # 注意：在异步上下文中，children 需要预先加载
            children = getattr(self, '_children_cache', None)
            if children:
                result["children"] = [
                    child.to_dict(include_children=True)
                    for child in sorted(children, key=lambda x: x.sort_order)
                ]
        
        return result
    
    def get_full_path_name(self, parent_names: list = None) -> str:
        """
        获取完整路径名称，如：我的 > 余额 > 转账
        
        Args:
            parent_names: 父模块名称列表（需要外部传入，避免在异步上下文中访问关系）
        """
        if parent_names:
            return " > ".join(parent_names + [self.module_name])
        return self.module_name
