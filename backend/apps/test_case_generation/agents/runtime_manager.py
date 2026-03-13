"""RuntimeManager — Agent 注册 + Runtime 生命周期管理"""
from autogen_core import SingleThreadedAgentRuntime, AgentId

from .event_bridge import SSEEventBridge
from .coordinator import CoordinatorAgent
from .document_parser import DocumentParserAgent
from .test_point_extractor import TestPointExtractorAgent
from .test_case_generator import TestCaseGeneratorAgent
from .quality_reviewer import QualityReviewerAgent
from .skill_loader import SkillLoaderAgent
from .kb_search import KnowledgeSearchAgent
from .chat_agent import ChatAgent
from ..services.tcg_llm_service import TcgLLMService
from ..core.logger import get_logger

logger = get_logger("runtime_mgr")


class RuntimeManager:
    _runtimes: dict[str, SingleThreadedAgentRuntime] = {}
    _bridges: dict[str, SSEEventBridge] = {}

    @classmethod
    async def get_or_create(cls, conv_id, db, context, generation):
        if conv_id in cls._runtimes:
            bridge = cls._bridges.get(conv_id)
            if bridge:
                bridge.generation = generation
                logger.info(f"Runtime 复用: {conv_id[:8]}, bridge 更新 gen={generation}")
            return cls._runtimes[conv_id]

        runtime = SingleThreadedAgentRuntime()
        bridge = SSEEventBridge(conv_id, generation)
        llm_svc = TcgLLMService(db)

        agents = [
            (CoordinatorAgent, "coordinator",
             lambda: CoordinatorAgent(llm_svc, bridge, db, context)),
            (DocumentParserAgent, "doc_parser",
             lambda: DocumentParserAgent(llm_svc, bridge, db)),
            (TestPointExtractorAgent, "tp_extractor",
             lambda: TestPointExtractorAgent(llm_svc, bridge, db, context)),
            (TestCaseGeneratorAgent, "tc_generator",
             lambda: TestCaseGeneratorAgent(llm_svc, bridge, db, context)),
            (QualityReviewerAgent, "quality_reviewer",
             lambda: QualityReviewerAgent(llm_svc, bridge, db, context)),
            (SkillLoaderAgent, "skill_loader",
             lambda: SkillLoaderAgent(bridge, db, context.skill_registry)),
            (KnowledgeSearchAgent, "kb_search",
             lambda: KnowledgeSearchAgent(bridge, db)),
            (ChatAgent, "chat",
             lambda: ChatAgent(llm_svc, bridge, db)),
        ]

        for agent_cls, type_name, factory in agents:
            await agent_cls.register(runtime, type_name, factory)
            logger.info(f"Agent 注册: {type_name} → runtime[{conv_id[:8]}]")

        runtime.start()
        cls._runtimes[conv_id] = runtime
        cls._bridges[conv_id] = bridge
        logger.info(f"Runtime 创建: {conv_id[:8]}, 共 {len(agents)} 个 Agent")
        return runtime

    @classmethod
    def get_bridge(cls, conv_id: str) -> SSEEventBridge | None:
        return cls._bridges.get(conv_id)

    @classmethod
    async def cleanup(cls, conv_id):
        cls._bridges.pop(conv_id, None)
        rt = cls._runtimes.pop(conv_id, None)
        if rt:
            await rt.stop()
            logger.info(f"Runtime 销毁: {conv_id[:8]}")

    @classmethod
    async def cleanup_all(cls):
        for conv_id in list(cls._runtimes.keys()):
            await cls.cleanup(conv_id)
