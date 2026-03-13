"""SkillLoaderAgent — 从 SkillRepository 加载技能描述"""
from autogen_core import RoutedAgent, MessageContext, message_handler

from apps.ui_automation.skills.repository import SkillRepository

from .mixin import TCGAgentMixin
from .messages import LoadSkillsRequest, LoadSkillsResponse
from ..core.logger import get_logger

logger = get_logger("skill_loader")


def _build_skill_block(skills: list) -> tuple[str, list[str]]:
    blocks = []
    names = []
    for s in skills:
        desc = getattr(s, "description", "") or ""
        raw = getattr(s, "raw_content", "") or ""
        block = f"## {getattr(s, 'name', '')}\n{desc}\n\n{raw}".strip()
        if block:
            blocks.append(block)
        names.append(getattr(s, "name", ""))
    return "\n\n---\n\n".join(blocks), names


class SkillLoaderAgent(RoutedAgent, TCGAgentMixin):
    def __init__(self, event_bridge, db, skill_registry: list[dict] = None):
        super().__init__("技能加载")
        self._init_tcg(None, event_bridge, db)
        self._skill_repo = SkillRepository(db)
        self._skill_registry = skill_registry or []

    @message_handler
    async def handle_load(
        self, message: LoadSkillsRequest, ctx: MessageContext
    ) -> LoadSkillsResponse:
        skills = []
        if message.categories:
            skills = await self._skill_repo.list_by_categories(message.categories)
        if message.selected_keys:
            by_keys = await self._skill_repo.get_by_keys(message.selected_keys)
            seen = {s.key for s in skills}
            for s in by_keys:
                if s.key not in seen:
                    skills.append(s)
                    seen.add(s.key)
        skill_block, skill_names = _build_skill_block(skills)
        logger.info(f"加载 {len(skills)} 个 Skills: {skill_names} | categories={message.categories} selected_keys={message.selected_keys}")
        return LoadSkillsResponse(skill_block=skill_block, skill_names=skill_names)
