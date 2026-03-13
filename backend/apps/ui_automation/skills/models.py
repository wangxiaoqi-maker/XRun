"""Skill ORM 模型 - 平台级 AI 技能"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON

from apps.ui_automation.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_beijing() -> datetime:
    return datetime.now()


class Skill(Base):
    """平台级 Skill - 可从 skills.sh/GitHub 下载，注入任意 LLM prompt"""

    __tablename__ = "skill"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    icon = Column(String(20), default="⚙")
    description = Column(Text)
    category = Column(String(50), default="general")  # general | tcg_method | ...

    source_type = Column(String(50))  # builtin | skills_sh | github | manual
    source_url = Column(String(1000))
    source_repo = Column(String(500))  # owner/repo
    raw_content = Column(Text, nullable=False)  # 完整 SKILL.md
    files = Column(JSON, default=list)  # [{filename, language, content}]

    is_builtin = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    version = Column(String(50))
    author = Column(String(200))
    weekly_installs = Column(Integer, default=0)
    github_stars = Column(Integer, default=0)

    created_at = Column(DateTime, default=now_beijing)
    updated_at = Column(DateTime, default=now_beijing, onupdate=now_beijing)
