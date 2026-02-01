"""
页面跳转关系模型
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import KnowledgeBase
from ..utils.timezone import beijing_now_naive


class PageTransition(KnowledgeBase):
    """页面跳转关系表 - 构建 App 导航地图"""
    __tablename__ = 'kb_page_transition'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 页面关系
    from_page_id = Column(
        String(36),
        ForeignKey('kb_page_analysis.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="起始页面 ID"
    )
    to_page_id = Column(
        String(36),
        ForeignKey('kb_page_analysis.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="目标页面 ID"
    )
    
    # 冗余字段（方便查询）
    from_page_name = Column(String(200), comment="起始页面名称")
    to_page_name = Column(String(200), comment="目标页面名称")
    
    # 触发元素
    trigger_element_id = Column(
        String(36),
        ForeignKey('kb_page_element.id', ondelete='SET NULL'),
        comment="触发跳转的元素 ID"
    )
    trigger_element_name = Column(String(200), comment="触发元素名称：转账 / 扫一扫")
    trigger_element_locator = Column(Text, comment="触发元素的 MidScene 定位描述")
    
    # 跳转类型
    transition_type = Column(String(50), comment="跳转类型：push/pop/replace/modal/tab")
    transition_description = Column(Text, comment="跳转描述：在首页点击转账按钮，跳转到转账页面")
    
    # 验证状态
    is_confirmed = Column(Boolean, default=False, comment="是否已人工确认")
    confirmed_at = Column(DateTime, comment="确认时间")
    
    # 时间戳（北京时间 UTC+8）
    created_at = Column(DateTime, default=beijing_now_naive)
    
    # 关系
    from_page = relationship("PageAnalysis", foreign_keys=[from_page_id])
    to_page = relationship("PageAnalysis", foreign_keys=[to_page_id])
    trigger_element = relationship("PageElement", foreign_keys=[trigger_element_id])
    
    # 索引和约束
    __table_args__ = (
        Index('idx_transition_from', 'from_page_id'),
        Index('idx_transition_to', 'to_page_id'),
        Index('idx_transition_trigger', 'trigger_element_id'),
        # 唯一约束：同一触发元素只能有一个跳转目标
        UniqueConstraint('trigger_element_id', name='uq_trigger_element'),
    )
    
    def __repr__(self):
        return f"<PageTransition(from={self.from_page_name}, to={self.to_page_name}, trigger={self.trigger_element_name})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "from_page_id": self.from_page_id,
            "to_page_id": self.to_page_id,
            "from_page_name": self.from_page_name,
            "to_page_name": self.to_page_name,
            "trigger_element_id": self.trigger_element_id,
            "trigger_element_name": self.trigger_element_name,
            "trigger_element_locator": self.trigger_element_locator,
            "transition_type": self.transition_type,
            "transition_description": self.transition_description,
            "is_confirmed": self.is_confirmed,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
