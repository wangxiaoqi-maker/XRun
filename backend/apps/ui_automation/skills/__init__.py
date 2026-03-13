"""平台级 Skill 模块 - 支持从 skills.sh/GitHub 下载，任何 LLM 调用场景可动态加载"""

from .models import Skill
from .repository import SkillRepository
from .service import SkillService

__all__ = ["Skill", "SkillRepository", "SkillService"]
