"""
执行记录模型
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.sql import func
from apps.ui_automation.database import Base

class Execution(Base):
    """执行记录表"""
    __tablename__ = "executions"
    
    id = Column(String(36), primary_key=True)
    case_id = Column(String(36), ForeignKey("test_cases.id"))
    device_id = Column(String(100), nullable=False)
    platform = Column(String(20), nullable=False)  # android / ios
    status = Column(String(20), default="pending")  # pending, running, success, failed, error
    logs = Column(Text, nullable=True)  # 执行日志
    report_path = Column(String(500), nullable=True)  # 报告路径
    duration_ms = Column(Integer, nullable=True)  # 执行耗时
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
