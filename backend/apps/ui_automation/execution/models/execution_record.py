"""
执行记录模型

记录每次用例执行的详细信息，包括状态、结果、报告等
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, DateTime, Text, Enum, JSON, Index, Integer
from sqlalchemy.sql import func

from apps.ui_automation.database import Base
from apps.ui_automation.execution.models.enums import Platform, ExecutionStatus


class ExecutionRecord(Base):
    """执行记录表 - 详细记录每次执行"""
    __tablename__ = "execution_record"
    
    # ========== 主键 ==========
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="执行记录 ID"
    )
    
    # ========== 关联 ==========
    case_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="用例 ID"
    )
    suite_id = Column(String(36), index=True, comment="套件 ID")
    suite_execution_id = Column(
        String(36),
        index=True,
        comment="套件执行批次 ID（用于关联同批次执行）"
    )
    
    # ========== 设备信息 ==========
    device_id = Column(String(100), nullable=False, comment="设备 ID")
    device_name = Column(String(200), comment="设备名称")
    platform = Column(
        Enum(Platform),
        nullable=False,
        comment="平台"
    )
    
    # ========== 执行状态 ==========
    status = Column(
        Enum(ExecutionStatus),
        nullable=False,
        default=ExecutionStatus.PENDING,
        index=True,
        comment="执行状态"
    )
    
    # ========== 变量快照 ==========
    variables_snapshot = Column(
        JSON,
        comment="执行时的变量值 {varName: value}"
    )
    config_snapshot = Column(
        JSON,
        comment="执行时的配置快照"
    )
    data_row_index = Column(
        Integer,
        comment="数据驱动的行索引（-1 表示全部）"
    )
    
    # ========== 时间 ==========
    started_at = Column(DateTime, comment="开始时间")
    finished_at = Column(DateTime, comment="结束时间")
    duration_ms = Column(Integer, comment="执行时长（毫秒）")
    
    # ========== 结果 ==========
    report_url = Column(String(500), comment="HTML 报告路径")
    report_data = Column(JSON, comment="报告数据摘要")
    error_message = Column(Text, comment="错误信息")
    error_stack = Column(Text, comment="错误堆栈")
    
    # ========== 步骤详情 ==========
    steps_result = Column(
        JSON,
        comment="步骤执行结果 [{stepId, status, duration, error, screenshot}]"
    )
    total_steps = Column(Integer, comment="总步骤数")
    passed_steps = Column(Integer, comment="通过步骤数")
    failed_steps = Column(Integer, comment="失败步骤数")
    skipped_steps = Column(Integer, comment="跳过步骤数")
    
    # ========== 编译产物 ==========
    compiled_script_content = Column(
        Text,
        comment="编译后的 TypeScript 代码内容"
    )
    compiled_script_hash = Column(
        String(64),
        index=True,
        comment="编译产物 hash（用于缓存和去重）"
    )
    
    # ========== 触发信息 ==========
    triggered_by = Column(String(100), comment="触发者（用户/定时/CI）")
    trigger_source = Column(
        String(50),
        default="manual",
        comment="触发来源 (manual/schedule/ci/api)"
    )
    
    # ========== 时间戳 ==========
    created_at = Column(DateTime, server_default=func.now())
    
    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_exec_case", "case_id"),
        Index("idx_exec_status", "status"),
        Index("idx_exec_started", "started_at"),
        Index("idx_exec_suite_batch", "suite_execution_id"),
    )
    
    def __repr__(self) -> str:
        return f"<ExecutionRecord(id={self.id}, case_id={self.case_id}, status={self.status})>"
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "suite_id": self.suite_id,
            "suite_execution_id": self.suite_execution_id,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "platform": self.platform.value if self.platform else None,
            "status": self.status.value if self.status else None,
            "variables_snapshot": self.variables_snapshot,
            "config_snapshot": self.config_snapshot,
            "data_row_index": self.data_row_index,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
            "report_url": self.report_url,
            "error_message": self.error_message,
            "steps_result": self.steps_result,
            "total_steps": self.total_steps,
            "passed_steps": self.passed_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "compiled_script_hash": self.compiled_script_hash,
            # 注意：compiled_script_content 不包含在默认 dict 中，避免响应过大
            "triggered_by": self.triggered_by,
            "trigger_source": self.trigger_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_summary(self) -> dict[str, Any]:
        """转换为摘要信息"""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "status": self.status.value if self.status else None,
            "duration_ms": self.duration_ms,
            "total_steps": self.total_steps,
            "passed_steps": self.passed_steps,
            "failed_steps": self.failed_steps,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }
    
    def calculate_duration(self) -> None:
        """计算执行时长"""
        if self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def is_finished(self) -> bool:
        """检查是否已完成"""
        return self.status in [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
        ]
