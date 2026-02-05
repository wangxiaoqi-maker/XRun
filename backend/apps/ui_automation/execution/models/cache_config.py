"""
缓存配置模型

管理 Midscene AI 缓存策略
"""
import uuid
from typing import Any

from sqlalchemy import Column, String, DateTime, Enum, Index, Boolean
from sqlalchemy.sql import func

from apps.ui_automation.database import Base
from apps.ui_automation.execution.models.enums import ConfigScope, CacheStrategy


class CacheConfig(Base):
    """缓存配置表 - 管理 AI 缓存策略"""
    __tablename__ = "cache_config"
    
    # ========== 主键 ==========
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="配置 ID"
    )
    
    # ========== 作用域 ==========
    scope = Column(
        Enum(ConfigScope),
        nullable=False,
        comment="作用域 (global/project/app/case)"
    )
    scope_id = Column(String(36), comment="关联的 ID")
    
    # ========== 缓存策略 ==========
    strategy = Column(
        Enum(CacheStrategy),
        default=CacheStrategy.DISABLED,
        comment="缓存策略"
    )
    
    # ========== 缓存 ID 模式 ==========
    cache_id_pattern = Column(
        String(200),
        default="${case_id}",
        comment="缓存 ID 模式（支持变量替换）"
    )
    
    # ========== 缓存目录 ==========
    cache_dir = Column(
        String(500),
        default="./midscene_run/cache",
        comment="缓存目录"
    )
    
    # ========== 自动清理 ==========
    auto_cleanup = Column(
        Boolean,
        default=False,
        comment="是否自动清理未使用缓存"
    )
    cleanup_after_days = Column(
        String(10),
        default="7",
        comment="清理 N 天前的缓存"
    )
    
    # ========== 时间戳 ==========
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ========== 唯一约束 ==========
    __table_args__ = (
        Index("uk_cache_scope", "scope", "scope_id", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<CacheConfig(scope={self.scope}, strategy={self.strategy})>"
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "scope": self.scope.value if self.scope else None,
            "scope_id": self.scope_id,
            "strategy": self.strategy.value if self.strategy else None,
            "cache_id_pattern": self.cache_id_pattern,
            "cache_dir": self.cache_dir,
            "auto_cleanup": self.auto_cleanup,
            "cleanup_after_days": self.cleanup_after_days,
        }
    
    def get_cache_id(self, context: dict[str, Any]) -> str:
        """
        根据上下文生成缓存 ID
        
        Args:
            context: 上下文变量 {case_id, case_name, ...}
            
        Returns:
            解析后的缓存 ID
        """
        pattern = self.cache_id_pattern or "${case_id}"
        result = pattern
        
        for key, value in context.items():
            placeholder = f"${{{key}}}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def is_read_enabled(self) -> bool:
        """是否启用缓存读取"""
        return self.strategy in [CacheStrategy.READ_ONLY, CacheStrategy.READ_WRITE]
    
    def is_write_enabled(self) -> bool:
        """是否启用缓存写入"""
        return self.strategy in [CacheStrategy.WRITE_ONLY, CacheStrategy.READ_WRITE]
