"""
全局变量模型

支持多级作用域的变量管理，包括敏感数据标记
"""
import uuid
from typing import Any

from sqlalchemy import Column, String, DateTime, Text, Enum, JSON, Index, Boolean
from sqlalchemy.sql import func

from apps.ui_automation.database import Base
from apps.ui_automation.execution.models.enums import ConfigScope, VariableType


class GlobalVariable(Base):
    """全局变量表 - 支持多级作用域"""
    __tablename__ = "global_variable"
    
    # ========== 主键 ==========
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="变量 ID"
    )
    
    # ========== 作用域 ==========
    scope = Column(
        Enum(ConfigScope),
        nullable=False,
        default=ConfigScope.GLOBAL,
        comment="作用域"
    )
    scope_id = Column(String(36), comment="关联的 project_id 或 app_id")
    
    # ========== 变量定义 ==========
    name = Column(String(100), nullable=False, comment="变量名")
    value = Column(Text, comment="变量值")
    value_type = Column(
        Enum(VariableType),
        default=VariableType.STRING,
        comment="值类型"
    )
    
    # ========== 安全配置 ==========
    is_secret = Column(
        Boolean,
        default=False,
        index=True,
        comment="是否敏感数据（不在日志中显示）"
    )
    
    # ========== 元信息 ==========
    description = Column(String(500), comment="变量描述")
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    
    # ========== 时间戳 ==========
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), comment="创建人")
    
    # ========== 唯一约束 ==========
    __table_args__ = (
        Index("uk_var_scope_name", "scope", "scope_id", "name", unique=True),
        Index("idx_var_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<GlobalVariable(name={self.name}, scope={self.scope})>"
    
    def to_dict(self, mask_secret: bool = True) -> dict[str, Any]:
        """
        转换为字典
        
        Args:
            mask_secret: 是否掩码敏感数据
        """
        value = self.value
        if mask_secret and self.is_secret and value:
            # 敏感数据只显示前后各2个字符
            if len(value) > 6:
                value = f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
            else:
                value = "*" * len(value)
        
        return {
            "id": self.id,
            "scope": self.scope.value if self.scope else None,
            "scope_id": self.scope_id,
            "name": self.name,
            "value": value,
            "value_type": self.value_type.value if self.value_type else None,
            "is_secret": self.is_secret,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_typed_value(self) -> Any:
        """获取类型化的值"""
        if self.value is None:
            return None
        
        if self.value_type == VariableType.NUMBER:
            try:
                # 尝试整数
                return int(self.value)
            except ValueError:
                try:
                    # 尝试浮点数
                    return float(self.value)
                except ValueError:
                    return self.value
        
        elif self.value_type == VariableType.BOOLEAN:
            return self.value.lower() in ("true", "1", "yes")
        
        elif self.value_type == VariableType.JSON:
            import json
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return self.value
        
        return self.value
