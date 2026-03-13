"""ORM 模型 - 复用主应用的 Base"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON, BigInteger,
    Index,
)
from apps.ui_automation.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_beijing() -> datetime:
    return datetime.now()


class TcgProject(Base):
    __tablename__ = "tcg_project"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=now_beijing)
    updated_at = Column(DateTime, default=now_beijing, onupdate=now_beijing)


# 已废弃：被 TcgConversation + ContextStore 替代
class TcgGenerationSession(Base):
    __tablename__ = "tcg_generation_session"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200))

    input_sources = Column(JSON, nullable=False)
    test_methods = Column(JSON, default=lambda: ["comprehensive"])
    user_prompt = Column(Text)
    text_model_id = Column(String(36))
    vision_model_id = Column(String(36))
    module_name = Column(String(200))

    test_points = Column(JSON)
    confirmed_test_points = Column(JSON)

    status = Column(String(30), default="pending", index=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    cost_tokens = Column(Integer, default=0)

    created_at = Column(DateTime, default=now_beijing)
    finished_at = Column(DateTime)


class TcgTestCase(Base):
    __tablename__ = "tcg_test_case"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    conversation_id = Column(String(36), index=True)
    module_name = Column(String(200))
    creator = Column(String(100))

    case_no = Column(String(50), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    test_type = Column(String(50))
    priority = Column(String(20))
    preconditions = Column(Text)
    test_steps = Column(JSON)
    tags = Column(JSON)

    review_status = Column(String(20), default="pending", index=True)
    review_comment = Column(Text)
    quality_scores = Column(JSON)

    source_ref = Column(JSON)
    hash_code = Column(String(64))
    version = Column(Integer, default=1)

    created_at = Column(DateTime, default=now_beijing)
    updated_at = Column(DateTime, default=now_beijing, onupdate=now_beijing)


class TcgModule(Base):
    __tablename__ = "tcg_module"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(String(36))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=now_beijing)

    __table_args__ = (
        Index("ix_tcg_module_proj_name", "project_id", "name", unique=True),
    )


class TcgInputFile(Base):
    __tablename__ = "tcg_input_file"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    file_name = Column(String(500))
    file_type = Column(String(20))
    file_path = Column(String(1000))
    file_size = Column(BigInteger)
    status = Column(String(20), default="uploaded")
    parsed_content = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=now_beijing)


class TcgKbDocumentChunk(Base):
    __tablename__ = "tcg_kb_document_chunk"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    file_id = Column(String(36), index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    page_num = Column(Integer)
    section = Column(String(200))
    vector_id = Column(String(36))
    created_at = Column(DateTime, default=now_beijing)


class TcgReviewRecord(Base):
    __tablename__ = "tcg_review_record"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), nullable=False, index=True)
    case_id = Column(String(36))
    review_round = Column(Integer, default=1)
    rejected_ids = Column(JSON, default=list)
    review_type = Column(String(20))
    review_status = Column(String(20))
    reviewer = Column(String(100))
    comment = Column(Text)
    checklist_results = Column(JSON)
    created_at = Column(DateTime, default=now_beijing)
    reviewed_at = Column(DateTime)


class TcgExportTemplate(Base):
    __tablename__ = "tcg_export_template"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    is_default = Column(Boolean, default=False)
    columns = Column(JSON, nullable=False)
    style_config = Column(JSON)
    created_at = Column(DateTime, default=now_beijing)
    updated_at = Column(DateTime, default=now_beijing, onupdate=now_beijing)


class TcgTestExecution(Base):
    """功能用例手工执行记录"""
    __tablename__ = "tcg_test_execution"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    case_id = Column(String(36), nullable=False, index=True)
    case_name = Column(String(500))
    executor = Column(String(100))
    status = Column(String(20), default="in_progress", index=True)
    step_results = Column(JSON, default=list)
    total_steps = Column(Integer, default=0)
    passed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    blocked_steps = Column(Integer, default=0)
    remark = Column(Text)
    started_at = Column(DateTime, default=now_beijing)
    finished_at = Column(DateTime)


class TcgConversation(Base):
    __tablename__ = "tcg_conversation"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False)
    title = Column(String(200), default="新对话")
    config = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=now_beijing)
    updated_at = Column(DateTime, default=now_beijing, onupdate=now_beijing)

    __table_args__ = (
        Index("ix_tcg_conv_proj_updated", "project_id", "updated_at"),
    )


class TcgConversationMessage(Base):
    __tablename__ = "tcg_conversation_message"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text)
    message_type = Column(String(30), default="text")
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=now_beijing)
