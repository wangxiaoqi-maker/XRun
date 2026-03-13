"""TCGAgentMixin — 为 RoutedAgent 注入 LLM 调用 + SSE 推送能力"""
from ..core.logger import get_logger
from .event_bridge import SSEEventBridge
from ..services.tcg_llm_service import TcgLLMService


class TCGAgentMixin:
    """与 RoutedAgent 组合使用，不继承 BaseAgent"""

    def _init_tcg(
        self,
        llm_service: TcgLLMService,
        event_bridge: SSEEventBridge,
        db=None,
        context=None,
    ):
        self._llm_service = llm_service
        self._event_bridge = event_bridge
        self._db = db
        self._context = context
        self._logger = get_logger(self._description if hasattr(self, "_description") else "agent")

    async def call_llm(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        messages: list[dict] = None,
        model_id: str = None,
        temperature: float = 0.3,
        max_tokens: int = None,
        emit_thinking: bool = False,
        stream_content: bool = False,
    ) -> str:
        """统一 LLM 调用 — 始终流式，实时推送进度

        支持两种调用方式：
        1. messages: 多轮对话（ChatAgent 使用）
        2. system_prompt + user_prompt: 单轮调用（其他 Agent 不变）

        emit_thinking: 启用深度思考（reasoning_effort），有 reasoning_content 时推送 thinking 事件
        stream_content: 流式推送普通 content（content_stream 事件），用于 Chat 实时输出
        """
        last_content_len = [0]
        last_think_len = [0]
        has_thinking = [False]

        async def _on_thinking(full_text: str):
            has_thinking[0] = True
            if len(full_text) - last_think_len[0] >= 8:
                last_think_len[0] = len(full_text)
                await self.emit_thinking(full_text, streaming=True)

        async def _on_content(full_text: str):
            if not stream_content:
                return
            if has_thinking[0]:
                return
            if len(full_text) - last_content_len[0] >= 4:
                last_content_len[0] = len(full_text)
                await self.emit_content_stream(full_text)

        mid = model_id or (self._context.text_model_id if self._context else None)
        content, thinking, usage = await self._llm_service.chat_stream(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            messages=messages,
            model_id=mid,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort="medium" if emit_thinking else None,
            on_thinking=_on_thinking if emit_thinking else None,
            on_content=_on_content,
        )

        if thinking and emit_thinking:
            await self.emit_thinking(thinking, streaming=False)

        if stream_content and not has_thinking[0]:
            await self.emit_content_done(content)

        if usage:
            await self.emit_usage(usage)

        return content

    async def emit_progress(self, message: str, percent: int = None):
        data = {"message": message}
        if percent is not None:
            data["percent"] = percent
        await self._event_bridge.emit_legacy("progress", data)

    async def emit_thinking(self, content: str, streaming: bool = True):
        event_type = "thinking_stream" if streaming else "thinking_done"
        await self._event_bridge.emit_legacy(event_type, {"content": content})

    async def emit_content_stream(self, content: str):
        await self._event_bridge.emit_legacy("content_stream", {"content": content})

    async def emit_content_done(self, content: str):
        await self._event_bridge.emit_legacy("content_done", {"content": content})

    async def emit_usage(self, usage: dict):
        await self._event_bridge.emit_legacy("usage", usage)

    async def emit_result(self, data: dict):
        agent_name = getattr(self, "_description", "agent")
        await self._event_bridge.emit_result(agent_name, data)

    async def emit_legacy(self, event_type: str, data: dict):
        await self._event_bridge.emit_legacy(event_type, data)
