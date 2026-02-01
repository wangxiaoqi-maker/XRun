"""
页面分析结果模型
"""
import uuid
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Index, JSON
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import relationship

from .base import KnowledgeBase
from ..utils.timezone import beijing_now_naive


class PageAnalysis(KnowledgeBase):
    """页面分析结果表 - 存储单次页面分析的完整结果"""
    __tablename__ = 'kb_page_analysis'
    
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
    
    # ========== 页面信息 ==========
    page_name = Column(String(200), nullable=False, index=True, comment="AI 生成的页面名称")
    page_type = Column(String(50), default='unknown', index=True, comment="页面类型：login/home/list/detail/form")
    page_description = Column(Text, comment="页面功能描述（AI 生成）")
    
    # 用户输入的上下文提示（如"点击财富tab后跳转到该页面"）
    user_context = Column(Text, comment="用户提供的上下文描述（页面来源、功能说明等）")
    
    # 页面导航来源（记录如何到达这个页面）
    navigation_source = Column(String(500), comment="导航来源描述（如：首页 > 财富tab）")
    
    # 页面特征签名（用于去重判断，基于页面结构而非截图）
    page_signature = Column(String(64), index=True, comment="页面特征签名（用于判断是否是同一个页面）")
    
    # 页面深度（从首页的导航深度）
    depth = Column(Integer, default=0, comment="从首页的导航深度")
    
    # 访问次数
    visit_count = Column(Integer, default=1, comment="被访问次数")
    
    # ========== 截图信息 ==========
    screenshot_hash = Column(String(64), index=True, comment="截图 MD5 哈希（用于去重判断）")
    screenshot_url = Column(String(500), comment="截图 URL（存储在 MinIO）")
    device_udid = Column(String(100), comment="设备 UDID")
    device_resolution = Column(String(50), comment="设备分辨率（仅记录）")
    
    # ========== 分析结果 ==========
    elements_count = Column(Integer, default=0, comment="识别的元素数量")
    confidence_score = Column(DECIMAL(5, 2), default=Decimal("0.00"), comment="整体置信度分数")
    raw_response = Column(JSON, comment="LLM 原始返回（JSON）")
    analysis_metadata = Column(JSON, comment="分析元数据（模型版本、耗时等）")
    processing_time = Column(DECIMAL(10, 3), comment="处理耗时（秒）")
    
    # ========== 时间戳（北京时间 UTC+8）==========
    created_at = Column(DateTime, default=beijing_now_naive, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now_naive, onupdate=beijing_now_naive, comment="更新时间")
    
    # ========== 关系 ==========
    # 所属应用
    app = relationship("AppInfo", back_populates="pages")
    
    # 页面元素（一对多）
    elements = relationship(
        "PageElement",
        back_populates="page",
        cascade="all, delete-orphan",
        foreign_keys="PageElement.page_id",
        lazy="dynamic"
    )
    
    # ========== 索引 ==========
    __table_args__ = (
        Index('idx_page_app_name', 'app_id', 'page_name'),
        Index('idx_page_type', 'page_type'),
        Index('idx_page_hash', 'screenshot_hash'),
        # 性能优化：去重查询专用复合索引
        Index('idx_page_dedup', 'app_id', 'page_name', 'created_at'),
        Index('idx_page_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<PageAnalysis(id={self.id}, name={self.page_name}, type={self.page_type})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "app_id": self.app_id,
            "app_name": getattr(self, '_app_name', None) or (self.app.app_name if self.app else None),
            "page_name": self.page_name,
            "page_type": self.page_type,
            "page_description": self.page_description,
            "user_context": self.user_context,
            "navigation_source": self.navigation_source,
            "screenshot_hash": self.screenshot_hash,
            "screenshot_url": self.screenshot_url,
            "device_udid": self.device_udid,
            "device_resolution": self.device_resolution,
            "elements_count": self.elements_count,
            "confidence_score": float(self.confidence_score) if self.confidence_score else 0.0,
            "processing_time": float(self.processing_time) if self.processing_time else 0.0,
            "page_signature": self.page_signature,
            "depth": self.depth,
            "visit_count": self.visit_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
