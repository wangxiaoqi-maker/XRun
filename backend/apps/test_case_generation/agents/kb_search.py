"""KnowledgeSearchAgent — 从知识库检索相关内容"""
from autogen_core import RoutedAgent, MessageContext, message_handler

from .mixin import TCGAgentMixin
from .messages import KnowledgeSearchRequest, KnowledgeSearchResponse
from ..core.logger import get_logger
from ..knowledge.service import KnowledgeService

logger = get_logger("kb_search")


class KnowledgeSearchAgent(RoutedAgent, TCGAgentMixin):
    def __init__(self, event_bridge, db):
        super().__init__("知识库检索")
        self._init_tcg(None, event_bridge, db)

    @message_handler
    async def handle_search(
        self, message: KnowledgeSearchRequest, ctx: MessageContext
    ) -> KnowledgeSearchResponse:
        if not message.project_id or not message.query:
            return KnowledgeSearchResponse(context="", chunks=[])

        try:
            kb_service = KnowledgeService(self._db)
            context, chunks = await kb_service.search(
                project_id=message.project_id,
                query=message.query,
                top_k=message.top_k,
            )
            if context:
                logger.info(f"知识库检索: {len(chunks)} 条结果 | project={message.project_id[:8]}")
            else:
                logger.info("知识库检索: 无匹配结果")
            return KnowledgeSearchResponse(context=context, chunks=chunks)
        except Exception as e:
            logger.warning(f"知识库检索失败（降级为空）: {e}")
            return KnowledgeSearchResponse(context="", chunks=[])
