"""Skill Pydantic 请求/响应"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class SkillFileItem(BaseModel):
    filename: str = Field(..., min_length=1, max_length=200)
    language: str = "shell"  # shell | python | javascript | typescript | yaml | json
    content: str = ""


class SkillOut(BaseModel):
    id: str
    key: str
    name: str
    icon: str = "⚙"
    description: Optional[str] = None
    category: str = "general"
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    source_repo: Optional[str] = None
    is_builtin: bool = False
    is_enabled: bool = True
    sort_order: int = 0
    version: Optional[str] = None
    author: Optional[str] = None
    weekly_installs: int = 0
    github_stars: int = 0
    files_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SkillDetailOut(SkillOut):
    raw_content: str = ""
    files: List[SkillFileItem] = []

    @field_validator('files', mode='before')
    @classmethod
    def coerce_none(cls, v):
        return v or []


class SkillInstallRequest(BaseModel):
    source: str = Field(..., description="owner/repo，如 chyax98/twu")
    skill_name: str = Field(..., description="skill 名称，如 testcase-generator")


class SkillImportUrlRequest(BaseModel):
    url: str = Field(..., description="SKILL.md 的 URL")


class SkillManualCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    files: List[SkillFileItem] = []


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_enabled: Optional[bool] = None
    raw_content: Optional[str] = None
    files: Optional[List[SkillFileItem]] = None


class SkillSearchResult(BaseModel):
    id: str
    skillId: Optional[str] = None
    name: str
    source: Optional[str] = None
    installs: Optional[int] = None
