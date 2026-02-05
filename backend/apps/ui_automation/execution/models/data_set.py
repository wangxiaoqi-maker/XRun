"""
数据集模型

支持内联数据、CSV 文件、API 端点等多种数据源
"""
import uuid
from typing import Any

from sqlalchemy import Column, String, DateTime, Text, Enum, JSON, Index, Boolean
from sqlalchemy.sql import func

from apps.ui_automation.database import Base
from apps.ui_automation.execution.models.enums import DataSourceType


class DataSet(Base):
    """数据集表 - 支持多种数据源"""
    __tablename__ = "data_set"
    
    # ========== 主键 ==========
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="数据集 ID"
    )
    
    # ========== 基本信息 ==========
    name = Column(String(200), nullable=False, comment="数据集名称")
    description = Column(Text, comment="数据集描述")
    
    # ========== 关联 ==========
    app_id = Column(String(36), index=True, comment="关联应用 ID")
    project_id = Column(String(36), index=True, comment="关联项目 ID")
    
    # ========== 数据源配置 ==========
    source_type = Column(
        Enum(DataSourceType),
        nullable=False,
        default=DataSourceType.INLINE,
        comment="数据源类型"
    )
    
    # ========== Inline 数据 ==========
    data_json = Column(
        JSON,
        comment="内联数据 [{col1: val1, col2: val2}, ...]"
    )
    
    # ========== CSV 配置 ==========
    csv_file_path = Column(String(500), comment="CSV 文件路径")
    csv_delimiter = Column(String(10), default=",", comment="CSV 分隔符")
    csv_has_header = Column(Boolean, default=True, comment="CSV 是否有表头")
    
    # ========== API 配置 ==========
    api_endpoint = Column(String(500), comment="API 端点 URL")
    api_method = Column(String(10), default="GET", comment="HTTP 方法")
    api_headers = Column(JSON, comment="请求头 {key: value}")
    api_body = Column(JSON, comment="请求体")
    
    # ========== 列定义 ==========
    columns = Column(
        JSON,
        comment="列定义 [{name, type, description, required}]"
    )
    
    # ========== 元信息 ==========
    row_count = Column(String(20), comment="数据行数（缓存）")
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    
    # ========== 时间戳 ==========
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), comment="创建人")
    
    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_dataset_app", "app_id"),
        Index("idx_dataset_project", "project_id"),
    )
    
    def __repr__(self) -> str:
        return f"<DataSet(id={self.id}, name={self.name}, source={self.source_type})>"
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "app_id": self.app_id,
            "project_id": self.project_id,
            "source_type": self.source_type.value if self.source_type else None,
            "data_json": self.data_json,
            "csv_file_path": self.csv_file_path,
            "csv_delimiter": self.csv_delimiter,
            "csv_has_header": self.csv_has_header,
            "api_endpoint": self.api_endpoint,
            "api_method": self.api_method,
            "api_headers": self.api_headers,
            "api_body": self.api_body,
            "columns": self.columns,
            "row_count": self.row_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }
    
    def get_data_rows(self) -> list[dict[str, Any]]:
        """
        获取数据行
        
        注意：对于 CSV 和 API 类型，需要在外部加载数据
        """
        if self.source_type == DataSourceType.INLINE:
            return self.data_json or []
        return []
    
    def get_column_names(self) -> list[str]:
        """获取列名列表"""
        if not self.columns:
            # 从数据中推断
            if self.data_json and len(self.data_json) > 0:
                return list(self.data_json[0].keys())
            return []
        return [col.get("name", "") for col in self.columns if col.get("name")]
