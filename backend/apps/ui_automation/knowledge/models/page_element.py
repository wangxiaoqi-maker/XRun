"""
页面元素模型
"""
import uuid
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import relationship

from .base import KnowledgeBase
from ..utils.timezone import beijing_now_naive


class PageElement(KnowledgeBase):
    """页面元素表 - 核心知识库数据，存储可交互元素的详细信息"""
    __tablename__ = 'kb_page_element'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联页面
    page_id = Column(
        String(36),
        ForeignKey('kb_page_analysis.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="关联的页面分析 ID"
    )
    
    # ========== 元素基本信息 ==========
    element_name = Column(String(200), nullable=False, comment="元素名称：转账、扫一扫、付款码")
    element_type = Column(String(50), nullable=False, index=True, comment="元素类型：button/icon/link/input")
    text_content = Column(String(500), comment="元素上的文字内容")
    
    # ========== 详细视觉描述（核心：用于 MidScene 定位）==========
    # 简短描述（同步到向量库）
    description = Column(Text, nullable=False, comment="简短描述：首页底部的转账按钮")
    
    # 详细视觉描述（icon 颜色、字体、形状等）
    visual_description = Column(Text, comment="详细视觉描述：蓝色的手机 icon，下方是黑色「手机充值」文字")
    
    # 完整 MidScene 定位器（组合所有信息生成的最佳定位描述）
    midscene_locator = Column(Text, comment="MidScene 定位描述：首页九宫格中，蓝色手机图标下方写着「手机充值」的入口")
    
    # ========== 位置关系 ==========
    # 绝对位置
    position_area = Column(String(100), comment="位置区域：顶部/底部/中央/左上/右下")
    position_in_container = Column(String(200), comment="容器内位置：九宫格第二行第一个 / 导航栏最右侧")
    
    # bbox 坐标（用于界面框选）
    # 格式：[left%, top%, width%, height%]，均为百分比值
    bbox = Column(JSON, comment="元素位置坐标 [left%, top%, width%, height%]")
    
    # 元素切图 URL（从页面截图中裁剪出的元素图片，用于以图找图定位）
    crop_image_url = Column(String(500), comment="元素切图 URL（MinIO）")
    
    # 相对位置关系（JSON 数组，存储与其他元素的关系）
    # 格式：[{"target": "付款码", "relation": "right_of", "description": "在付款码的右方"}, ...]
    relative_positions = Column(JSON, comment="相对位置关系")
    
    # ========== 导航跳转关系 ==========
    is_navigation = Column(Boolean, default=False, index=True, comment="是否是导航元素（可跳转）")
    target_page_id = Column(
        String(36), 
        ForeignKey('kb_page_analysis.id', ondelete='SET NULL'),
        comment="跳转目标页面 ID"
    )
    target_page_name = Column(String(200), comment="跳转目标页面名称（冗余，方便查询）")
    navigation_description = Column(Text, comment="跳转描述：点击后跳转到转账页面")
    
    # ========== 视觉特征详情 ==========
    icon_description = Column(Text, comment="icon 描述：蓝色手机图标 / 绿色扫码图标")
    text_style = Column(JSON, comment='文字样式：{"color": "黑色", "size": "小", "weight": "normal"}')
    background_style = Column(JSON, comment='背景样式：{"color": "白色", "shape": "圆形"}')
    
    # ========== 测试相关 ==========
    midscene_operations = Column(JSON, comment='支持的 MidScene 操作：["aiTap", "aiAssert"]')
    test_scenarios = Column(JSON, comment='测试场景：["点击进入转账页面", "验证转账入口存在"]')
    functionality = Column(String(500), comment="功能说明")
    interaction_state = Column(String(50), default='clickable', comment="交互状态：clickable/disabled/hidden")
    
    # ========== 质量评估 ==========
    confidence_score = Column(DECIMAL(5, 2), default=Decimal("0.00"), comment="元素识别置信度")
    is_testable = Column(Boolean, default=True, index=True, comment="是否可测试")
    test_priority = Column(String(20), default='medium', comment="测试优先级：high/medium/low")
    
    # ========== 时间戳（北京时间 UTC+8）==========
    created_at = Column(DateTime, default=beijing_now_naive, comment="创建时间")
    
    # ========== 关系 ==========
    # 所属页面
    page = relationship(
        "PageAnalysis", 
        back_populates="elements",
        foreign_keys=[page_id]
    )
    
    # 跳转目标页面
    target_page = relationship(
        "PageAnalysis",
        foreign_keys=[target_page_id]
    )
    
    # ========== 索引 ==========
    __table_args__ = (
        Index('idx_element_type', 'element_type'),
        Index('idx_element_testable', 'is_testable'),
        Index('idx_element_navigation', 'is_navigation'),
        Index('idx_element_target_page', 'target_page_id'),
    )
    
    def __repr__(self):
        return f"<PageElement(id={self.id}, name={self.element_name}, type={self.element_type})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "page_id": self.page_id,
            "element_name": self.element_name,
            "element_type": self.element_type,
            "text_content": self.text_content,
            "description": self.description,
            "visual_description": self.visual_description,
            "midscene_locator": self.midscene_locator,
            "position_area": self.position_area,
            "position_in_container": self.position_in_container,
            "bbox": self.bbox,
            "crop_image_url": self.crop_image_url,
            "relative_positions": self.relative_positions,
            "is_navigation": self.is_navigation,
            "target_page_id": self.target_page_id,
            "target_page_name": self.target_page_name,
            "navigation_description": self.navigation_description,
            "icon_description": self.icon_description,
            "text_style": self.text_style,
            "background_style": self.background_style,
            "midscene_operations": self.midscene_operations,
            "test_scenarios": self.test_scenarios,
            "functionality": self.functionality,
            "interaction_state": self.interaction_state,
            "confidence_score": float(self.confidence_score) if self.confidence_score else 0.0,
            "is_testable": self.is_testable,
            "test_priority": self.test_priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_vector_data(self, app_name: str, page_name: str, platform: str) -> dict:
        """转换为向量数据库格式"""
        return {
            "id": self.id,
            "description": self.midscene_locator or self.description,  # 优先使用 MidScene 定位器
            "metadata": {
                "app_name": app_name,
                "page_id": self.page_id,
                "page_name": page_name,
                "element_name": self.element_name,
                "element_type": self.element_type,
                "platform": platform,
                "is_testable": self.is_testable,
                "test_priority": self.test_priority,
                "text_content": self.text_content,
                "visual_desc": self.visual_description,
                "position_area": self.position_area,
                "is_navigation": self.is_navigation,
                "target_page_name": self.target_page_name,
            }
        }


class ElementRelation(KnowledgeBase):
    """元素空间关系表 - 存储元素之间的位置关系"""
    __tablename__ = 'kb_element_relation'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关系双方
    source_element_id = Column(
        String(36),
        ForeignKey('kb_page_element.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="源元素 ID"
    )
    target_element_id = Column(
        String(36),
        ForeignKey('kb_page_element.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="目标元素 ID"
    )
    
    # 关系信息
    relation_type = Column(String(50), nullable=False, index=True, comment="关系类型：right_of/left_of/above/below")
    relation_description = Column(Text, comment="关系描述：扫一扫在付款码的右方")
    distance = Column(String(50), comment="距离描述：adjacent/near/far")
    
    # 时间戳（北京时间 UTC+8）
    created_at = Column(DateTime, default=beijing_now_naive)
    
    # 关系
    source_element = relationship("PageElement", foreign_keys=[source_element_id])
    target_element = relationship("PageElement", foreign_keys=[target_element_id])
    
    # 索引
    __table_args__ = (
        Index('idx_relation_source', 'source_element_id'),
        Index('idx_relation_target', 'target_element_id'),
        Index('idx_relation_type', 'relation_type'),
    )
    
    def __repr__(self):
        return f"<ElementRelation(source={self.source_element_id}, target={self.target_element_id}, type={self.relation_type})>"
