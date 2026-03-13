"""
对话引擎 — 管理多轮对话、上下文状态、意图路由

高内聚：对话生命周期管理集中在此模块
低耦合：不依赖具体 Agent 实现，通过 EventQueue 与 Agent 层通信
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..core.logger import get_logger

logger = get_logger("conv_engine")


# ──────────────────────────────────────────────────────────────
#  SSE 事件协议
# ──────────────────────────────────────────────────────────────

@dataclass(slots=True)
class AgentEvent:
    """统一的 SSE 事件结构，所有 Agent 输出通过此类推送到前端"""
    event: str          # agent_start / agent_thinking / agent_result / agent_done / ...
    agent: str          # Agent 名称（如 "文档解析"）
    data: dict          # 事件数据
    elapsed_ms: int = 0 # 距 Agent 启动的耗时(ms)

    def to_sse(self) -> dict:
        return {
            "agent": self.agent,
            "action": self.event,
            "data": self.data,
            "elapsed_ms": self.elapsed_ms,
        }


# 兼容旧 SSE 格式
@dataclass(slots=True)
class LegacyEvent:
    event: str
    data: dict

    def to_sse(self) -> dict:
        return self.data


# ──────────────────────────────────────────────────────────────
#  意图枚举
# ──────────────────────────────────────────────────────────────

class UserIntent(str, Enum):
    UPLOAD_DOCUMENT = "upload_document"
    DESCRIBE_REQUIREMENT = "describe_requirement"
    CONFIRM_TEST_POINTS = "confirm_test_points"
    MODIFY_TEST_POINTS = "modify_test_points"
    GENERATE_CASES = "generate_cases"
    REVIEW_CASES = "review_cases"
    MODIFY_CASES = "modify_cases"
    QUERY_KNOWLEDGE = "query_knowledge"
    GENERAL_CHAT = "general_chat"


# ──────────────────────────────────────────────────────────────
#  上下文存储
# ──────────────────────────────────────────────────────────────

@dataclass
class ContextStore:
    """
    维护单个对话的累积上下文。
    高内聚：所有与对话状态相关的信息集中管理。
    """
    conversation_id: str = ""
    project_id: str = ""

    # 累积的需求信息
    parsed_documents: list[dict] = field(default_factory=list)
    user_requirements: list[str] = field(default_factory=list)

    # 已提取/确认的测试点
    test_points: list[dict] = field(default_factory=list)
    confirmed_point_ids: set[str] = field(default_factory=set)

    # 已生成的用例
    generated_cases: list[dict] = field(default_factory=list)

    # 审核状态
    point_review_status: dict[str, str] = field(default_factory=dict)
    case_review_status: dict[str, str] = field(default_factory=dict)
    point_review_round: int = 0
    case_review_round: int = 0

    # 对话历史
    messages: list[dict] = field(default_factory=list)

    # Skills
    skill_registry: list[dict] = field(default_factory=list)
    selected_skills: list[str] = field(default_factory=list)

    # 模型配置
    text_model_id: str = ""
    vision_model_id: str = ""

    def add_message(self, role: str, content: str, meta: dict = None):
        msg = {"role": role, "content": content, "timestamp": time.time()}
        if meta:
            msg["meta"] = meta
        self.messages.append(msg)
        if len(self.messages) > 50:
            self._compress_history()

    def get_context_summary(self) -> str:
        """生成当前上下文摘要，供 Agent 使用"""
        parts = []
        if self.parsed_documents:
            doc_names = [d.get("file_name", "未知") for d in self.parsed_documents]
            parts.append(f"已解析文档：{', '.join(doc_names)}")
        if self.test_points:
            confirmed = len(self.confirmed_point_ids)
            parts.append(f"测试点：{len(self.test_points)} 个（已确认 {confirmed} 个）")
        if self.generated_cases:
            parts.append(f"已生成用例：{len(self.generated_cases)} 条")
        if self.user_requirements:
            parts.append(f"用户补充说明：{'; '.join(self.user_requirements[-3:])}")
        return "\n".join(parts) if parts else "暂无上下文"

    def _compress_history(self):
        if len(self.messages) <= 30:
            return
        early = self.messages[:-30]
        summary = f"[历史摘要] 共 {len(early)} 条早期对话"
        self.messages = [{"role": "system", "content": summary}] + self.messages[-30:]

    def get_approved_points(self) -> list[dict]:
        return [p for p in self.test_points
                if self.point_review_status.get(p.get("id")) != "rejected"]

    def get_rejected_points(self) -> list[dict]:
        return [p for p in self.test_points
                if self.point_review_status.get(p.get("id")) == "rejected"]

    def merge_supplement_points(self, new_points: list[dict]):
        existing_ids = {p.get("id") for p in self.test_points}
        for p in new_points:
            if p.get("id") not in existing_ids:
                self.test_points.append(p)
                existing_ids.add(p.get("id"))

    def get_approved_cases(self) -> list[dict]:
        return [c for c in self.generated_cases
                if self.case_review_status.get(c.get("id")) != "rejected"]

    def get_rejected_cases(self) -> list[dict]:
        return [c for c in self.generated_cases
                if self.case_review_status.get(c.get("id")) == "rejected"]

    def merge_supplement_cases(self, new_cases: list[dict]):
        existing_ids = {c.get("id") for c in self.generated_cases}
        for c in new_cases:
            if c.get("id") not in existing_ids:
                self.generated_cases.append(c)
                existing_ids.add(c.get("id"))


# ──────────────────────────────────────────────────────────────
#  意图路由器
# ──────────────────────────────────────────────────────────────

class IntentRouter:
    """
    意图路由器 — 保守策略，默认走对话。

    设计原则：
    - 绝大多数消息 → GENERAL_CHAT（LLM 对话，像正常聊天一样）
    - 只有显式命令（斜杠指令 / 非常明确的动作词 + 上下文就绪）才触发工作流
    - 用户说"帮我生成测试用例"不会直接生成，而是 LLM 会对话式引导
    """

    SLASH_COMMANDS = {
        "/generate_from_chat": UserIntent.DESCRIBE_REQUIREMENT,
        "/generate": UserIntent.GENERATE_CASES,
        "/review": UserIntent.REVIEW_CASES,
        "/knowledge": UserIntent.QUERY_KNOWLEDGE,
        "/confirm": UserIntent.CONFIRM_TEST_POINTS,
        "/modify-points": UserIntent.MODIFY_TEST_POINTS,
        "/modify-cases": UserIntent.MODIFY_CASES,
    }

    @classmethod
    def route(cls, message: str, context: ContextStore, has_files: bool = False) -> UserIntent:
        msg = message.strip()
        msg_lower = msg.lower()

        if has_files:
            return UserIntent.UPLOAD_DOCUMENT

        # /skill-key 命令：匹配 skill_registry 中的 key，动态追加到 selected_skills
        skill_key = cls._extract_skill_key(msg, context)
        if skill_key and skill_key not in context.selected_skills:
            context.selected_skills.append(skill_key)

        for cmd, intent in sorted(cls.SLASH_COMMANDS.items(), key=lambda x: -len(x[0])):
            if msg_lower.startswith(cmd):
                return intent

        if cls._is_explicit_confirm(msg_lower, context):
            return UserIntent.CONFIRM_TEST_POINTS

        if cls._is_explicit_generate(msg_lower, context):
            return UserIntent.GENERATE_CASES

        return UserIntent.GENERAL_CHAT

    @staticmethod
    def _extract_skill_key(msg: str, context: ContextStore) -> str | None:
        """Detect /skill-key prefix against skill_registry, return key or None."""
        if not msg.startswith("/"):
            return None
        first_token = msg.split(None, 1)[0][1:]
        for s in context.skill_registry:
            if s["key"] == first_token:
                return first_token
        return None

    @staticmethod
    def _is_explicit_confirm(msg: str, context: ContextStore) -> bool:
        """Only trigger confirm when test points exist and user says something very explicit."""
        if not context.test_points:
            return False
        confirm_phrases = ["确认测试点", "确认全部", "通过测试点", "确认并生成"]
        return any(p in msg for p in confirm_phrases)

    @staticmethod
    def _is_explicit_generate(msg: str, context: ContextStore) -> bool:
        """Only trigger generation when confirmed points exist and user says an explicit command."""
        if not context.confirmed_point_ids:
            return False
        gen_phrases = ["开始生成", "立即生成", "生成用例"]
        return any(p in msg for p in gen_phrases)


# ──────────────────────────────────────────────────────────────
#  对话管理器
# ──────────────────────────────────────────────────────────────

class ConversationManager:
    """
    对话生命周期管理。
    职责：创建/获取对话、路由意图、管理 EventQueue、协调 Agent 执行。
    内存缓存 + DB 持久化双层设计：活跃对话在内存，非活跃从 DB 恢复。
    """

    _conversations: dict[str, ContextStore] = {}
    _queues: dict[str, asyncio.Queue] = {}
    _active_generation: dict[str, int] = {}

    @classmethod
    def create_conversation(
        cls,
        conv_id: str,
        project_id: str,
        text_model_id: str = "",
        vision_model_id: str = "",
        selected_skills: list[str] = None,
    ) -> str:
        ctx = ContextStore(
            conversation_id=conv_id,
            project_id=project_id,
            text_model_id=text_model_id,
            vision_model_id=vision_model_id,
            selected_skills=selected_skills or ["comprehensive"],
        )
        cls._conversations[conv_id] = ctx
        cls._queues[conv_id] = asyncio.Queue()
        return conv_id

    @classmethod
    def restore_context(cls, conv_id: str, ctx: ContextStore):
        """Restore a context from DB into memory cache."""
        cls._conversations[conv_id] = ctx
        if conv_id not in cls._queues:
            cls._queues[conv_id] = asyncio.Queue()

    @classmethod
    def get_context(cls, conv_id: str) -> Optional[ContextStore]:
        return cls._conversations.get(conv_id)

    @classmethod
    def get_queue(cls, conv_id: str) -> Optional[asyncio.Queue]:
        return cls._queues.get(conv_id)

    @classmethod
    def ensure_queue(cls, conv_id: str) -> asyncio.Queue:
        if conv_id not in cls._queues:
            cls._queues[conv_id] = asyncio.Queue()
        return cls._queues[conv_id]

    @classmethod
    def new_task_generation(cls, conv_id: str) -> int:
        """Increment generation counter and drain stale events from the queue."""
        gen = cls._active_generation.get(conv_id, 0) + 1
        cls._active_generation[conv_id] = gen
        queue = cls._queues.get(conv_id)
        if queue:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        return gen

    @classmethod
    async def emit(cls, conv_id: str, event: AgentEvent | LegacyEvent, generation: int = 0):
        if generation and cls._active_generation.get(conv_id, 0) != generation:
            logger.debug(f"Dropping stale event for conv={conv_id[:8]} gen={generation}")
            return
        queue = cls._queues.get(conv_id)
        if queue:
            await queue.put(event)

    @classmethod
    def is_current_generation(cls, conv_id: str, generation: int) -> bool:
        return cls._active_generation.get(conv_id, 0) == generation

    @classmethod
    def cleanup(cls, conv_id: str):
        cls._conversations.pop(conv_id, None)
        cls._queues.pop(conv_id, None)
        cls._active_generation.pop(conv_id, None)

    @classmethod
    def route_intent(cls, conv_id: str, message: str, has_files: bool = False) -> UserIntent:
        ctx = cls._conversations.get(conv_id)
        if not ctx:
            return UserIntent.GENERAL_CHAT
        return IntentRouter.route(message, ctx, has_files)
