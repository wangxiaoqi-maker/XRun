"""SSE 事件桥接 — Agent 内部事件 → ConversationManager Queue → SSE 推送"""
from ..core.logger import get_logger
from ..services.conversation_engine import ConversationManager, AgentEvent, LegacyEvent

logger = get_logger("sse_bridge")


class SSEEventBridge:
    """每个 Runtime 实例持有一个 bridge，绑定 conv_id + generation"""

    def __init__(self, conv_id: str, generation: int):
        self.conv_id = conv_id
        self.generation = generation

    async def emit_agent_event(self, agent_name: str, action: str, data: dict):
        evt = AgentEvent(event=action, agent=agent_name, data=data)
        await ConversationManager.emit(self.conv_id, evt, self.generation)

    async def emit_progress(self, agent_name: str, message: str, percent: int = None):
        data = {"message": message}
        if percent is not None:
            data["percent"] = percent
        await self.emit_agent_event(agent_name, "agent_progress", data)

    async def emit_thinking(self, agent_name: str, content: str, streaming: bool = True):
        await self.emit_agent_event(
            agent_name, "agent_thinking",
            {"content": content, "streaming": streaming},
        )

    async def emit_result(self, agent_name: str, data: dict):
        await self.emit_agent_event(agent_name, "agent_result", data)

    async def emit_legacy(self, event_type: str, data: dict):
        evt = LegacyEvent(event=event_type, data=data)
        await ConversationManager.emit(self.conv_id, evt, self.generation)
