"""
执行配置模型

支持多级作用域（全局/项目/应用）的配置管理
"""
import uuid
from typing import Any

from sqlalchemy import Column, String, DateTime, Text, Enum, JSON, Index, Integer, Boolean
from sqlalchemy.sql import func

from apps.ui_automation.database import Base
from apps.ui_automation.execution.models.enums import ConfigScope


class ExecutionConfig(Base):
    """执行配置表 - 支持多级作用域"""
    __tablename__ = "execution_config"
    
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
        default=ConfigScope.GLOBAL,
        comment="作用域 (global/project/app)"
    )
    scope_id = Column(
        String(36),
        comment="关联的 project_id 或 app_id"
    )
    
    # ========== 超时配置（毫秒）==========
    test_timeout_ms = Column(
        Integer,
        default=240000,
        comment="测试总超时（默认 4 分钟）"
    )
    step_timeout_ms = Column(
        Integer,
        default=720000,
        comment="单步骤超时（默认 12 分钟）"
    )
    hook_timeout_ms = Column(
        Integer,
        default=240000,
        comment="beforeAll/afterAll 超时"
    )
    wait_timeout_ms = Column(
        Integer,
        default=30000,
        comment="aiWaitFor 默认超时"
    )
    wait_interval_ms = Column(
        Integer,
        default=3000,
        comment="aiWaitFor 检查间隔"
    )
    
    # ========== 重试配置 ==========
    default_retry_count = Column(
        Integer,
        default=0,
        comment="默认重试次数"
    )
    retry_delay_ms = Column(
        Integer,
        default=1000,
        comment="重试间隔（毫秒）"
    )
    retry_backoff = Column(
        Boolean,
        default=True,
        comment="是否递增等待"
    )
    
    # ========== AI 上下文 ==========
    ai_action_context = Column(
        Text,
        comment="AI 操作上下文提示"
    )
    
    # ========== 规划配置 ==========
    replanning_cycle_limit = Column(
        Integer,
        default=20,
        comment="aiAct 最大重规划次数"
    )
    
    # ========== 模型配置 ==========
    model_name = Column(String(100), comment="Midscene 模型名称")
    model_base_url = Column(String(500), comment="模型 API 地址")
    model_family = Column(String(50), comment="模型家族 (qwen3-vl, gpt-4v, etc.)")
    model_config = Column(
        JSON,
        comment="多模型配置 {default: {}, planning: {}, insight: {}}"
    )
    
    # ========== 执行后操作 ==========
    wait_after_action_ms = Column(
        Integer,
        default=300,
        comment="每个操作后等待时间"
    )
    auto_dismiss_keyboard = Column(
        Boolean,
        default=True,
        comment="自动关闭键盘"
    )
    
    # ========== 报告配置 ==========
    generate_report = Column(Boolean, default=True, comment="是否生成报告")
    report_output_format = Column(
        String(50),
        default="single-html",
        comment="报告格式 (single-html/html-and-external-assets)"
    )
    
    # ========== 时间戳 ==========
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ========== 唯一约束 ==========
    __table_args__ = (
        Index("uk_config_scope", "scope", "scope_id", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<ExecutionConfig(scope={self.scope}, scope_id={self.scope_id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "scope": self.scope.value if self.scope else None,
            "scope_id": self.scope_id,
            "test_timeout_ms": self.test_timeout_ms,
            "step_timeout_ms": self.step_timeout_ms,
            "hook_timeout_ms": self.hook_timeout_ms,
            "wait_timeout_ms": self.wait_timeout_ms,
            "wait_interval_ms": self.wait_interval_ms,
            "default_retry_count": self.default_retry_count,
            "retry_delay_ms": self.retry_delay_ms,
            "retry_backoff": self.retry_backoff,
            "ai_action_context": self.ai_action_context,
            "replanning_cycle_limit": self.replanning_cycle_limit,
            "model_name": self.model_name,
            "model_base_url": self.model_base_url,
            "model_family": self.model_family,
            "model_config": self.model_config,
            "wait_after_action_ms": self.wait_after_action_ms,
            "auto_dismiss_keyboard": self.auto_dismiss_keyboard,
            "generate_report": self.generate_report,
            "report_output_format": self.report_output_format,
        }
    
    def merge_with(self, override: dict[str, Any] | None) -> dict[str, Any]:
        """
        与覆盖配置合并
        
        Args:
            override: 覆盖配置字典
            
        Returns:
            合并后的配置字典
        """
        base = self.to_dict()
        if not override:
            return base
        
        # 只覆盖非 None 的值
        for key, value in override.items():
            if value is not None and key in base:
                base[key] = value
        
        return base
