"""
测试用例模型 V2

支持 JSON 格式的步骤定义、变量参数化、用例引用
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, DateTime, Text, Enum, JSON, Index, Boolean
from sqlalchemy.sql import func

from apps.ui_automation.database import Base
from apps.ui_automation.execution.models.enums import Platform, CaseStatus, Priority


class TestCaseV2(Base):
    """测试用例表 V2 - 企业级用例管理"""
    __tablename__ = "test_case_v2"
    
    # ========== 主键 ==========
    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="用例 ID"
    )
    
    # ========== 基本信息 ==========
    name = Column(String(200), nullable=False, comment="用例名称")
    description = Column(Text, comment="用例描述")
    
    # ========== 关联 ==========
    app_id = Column(String(36), nullable=False, index=True, comment="关联应用 ID")
    project_id = Column(String(36), index=True, comment="关联项目 ID")
    suite_id = Column(String(36), index=True, comment="关联套件 ID")
    
    # ========== 平台 ==========
    platform = Column(
        Enum(Platform),
        nullable=False,
        comment="目标平台 (android/ios)"
    )
    
    # ========== 用例内容 (JSON) ==========
    steps_json = Column(
        JSON,
        nullable=False,
        comment="步骤列表 JSON [{id, type, locator, elementRef, options, ...}]"
    )
    
    input_variables = Column(
        JSON,
        comment="输入变量定义 [{name, type, required, defaultValue, description}]"
    )
    
    refs = Column(
        JSON,
        comment="引用的其他用例 [{caseId, alias, inputMapping}]"
    )
    
    # ========== 执行配置 (可覆盖全局配置) ==========
    config_override = Column(
        JSON,
        comment="执行配置覆盖 {timeout_ms, retry_count, ai_context, ...}"
    )
    
    # ========== 数据驱动 ==========
    data_set_id = Column(String(36), index=True, comment="关联数据集 ID")
    
    # ========== 启动配置 ==========
    launch_target = Column(
        String(500),
        comment="启动目标 (URL/包名/BundleID/URL Scheme)"
    )
    
    # ========== 元信息 ==========
    tags = Column(JSON, comment="标签数组 ['回归', '冒烟', ...]")
    priority = Column(
        Enum(Priority),
        default=Priority.MEDIUM,
        comment="优先级"
    )
    status = Column(
        Enum(CaseStatus),
        default=CaseStatus.DRAFT,
        index=True,
        comment="用例状态"
    )
    
    # ========== 版本控制 ==========
    version = Column(String(20), default="1.0.0", comment="用例版本")
    is_latest = Column(Boolean, default=True, index=True, comment="是否最新版本")
    parent_id = Column(String(36), comment="父版本 ID（用于版本追溯）")
    
    # ========== 编译缓存 ==========
    compiled_content = Column(Text, comment="编译后的 TypeScript 代码（缓存）")
    compiled_hash = Column(String(64), index=True, comment="用例内容 hash（用于判断是否需要重编译）")
    compiled_at = Column(DateTime, comment="最后编译时间")
    
    # ========== 时间戳 ==========
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    created_by = Column(String(100), comment="创建人")
    updated_by = Column(String(100), comment="更新人")
    
    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_case_app", "app_id"),
        Index("idx_case_project", "project_id"),
        Index("idx_case_platform", "platform"),
        Index("idx_case_status", "status"),
        Index("idx_case_latest", "is_latest"),
    )
    
    def __repr__(self) -> str:
        return f"<TestCaseV2(id={self.id}, name={self.name}, platform={self.platform})>"
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "app_id": self.app_id,
            "project_id": self.project_id,
            "suite_id": self.suite_id,
            "platform": self.platform.value if self.platform else None,
            "steps_json": self.steps_json,
            "input_variables": self.input_variables,
            "refs": self.refs,
            "config_override": self.config_override,
            "data_set_id": self.data_set_id,
            "launch_target": self.launch_target,
            "tags": self.tags,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "version": self.version,
            "is_latest": self.is_latest,
            # 编译缓存
            "compiled_content": self.compiled_content,
            "compiled_hash": self.compiled_hash,
            "compiled_at": self.compiled_at.isoformat() if self.compiled_at else None,
            # 时间戳
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
    
    def get_step_count(self) -> int:
        """获取步骤数量"""
        if not self.steps_json:
            return 0
        return len(self.steps_json)
    
    def get_variable_names(self) -> list[str]:
        """获取输入变量名列表"""
        if not self.input_variables:
            return []
        return [v.get("name", "") for v in self.input_variables if v.get("name")]
