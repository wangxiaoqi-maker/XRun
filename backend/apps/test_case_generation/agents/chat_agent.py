"""ChatAgent — 处理通用对话（标准多轮 messages 格式 + token 感知截取）"""
from autogen_core import RoutedAgent, MessageContext, message_handler

from .mixin import TCGAgentMixin
from .messages import ChatRequest, AgentResponse
from ..core.logger import get_logger

logger = get_logger("chat_agent")

SYSTEM_PROMPT = "你是一个测试用例生成助手，帮助用户解答测试相关问题。请基于对话历史进行连贯的回复。"

CHARS_PER_TOKEN = 2


def _estimate_tokens(text: str) -> int:
    return max(len(text) // CHARS_PER_TOKEN, 1)


def _build_messages(
    history: list[dict],
    current_msg: str,
    context_summary: str = "",
    context_window: int = 32768,
    max_output_tokens: int = 4096,
    image_urls: list[str] = None,
) -> list[dict]:
    """将对话历史构建为标准多轮 messages 数组，根据模型上下文窗口动态截取。

    策略：优先保留 system + 当前消息，剩余预算从最新到最旧填充历史。
    支持多模态：当 image_urls 非空时，构建 content 数组格式（text + image_url）。
    """
    input_budget = context_window - max_output_tokens

    system_msg = {"role": "system", "content": SYSTEM_PROMPT}
    user_text = current_msg
    if context_summary:
        user_text += f"\n\n[当前工作上下文]\n{context_summary}"

    if image_urls:
        content_parts = [{"type": "text", "text": user_text}]
        for url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": url}})
        current_user_msg = {"role": "user", "content": content_parts}
    else:
        current_user_msg = {"role": "user", "content": user_text}

    reserved = _estimate_tokens(SYSTEM_PROMPT) + _estimate_tokens(user_text)
    if image_urls:
        reserved += len(image_urls) * 1000
    remaining_budget = input_budget - reserved

    valid_history = [
        h for h in history
        if h.get("role") in ("user", "assistant") and h.get("content")
    ]

    kept: list[dict] = []
    for h in reversed(valid_history):
        c = h["content"]
        cost = _estimate_tokens(c) if isinstance(c, str) else 500
        if remaining_budget - cost < 0:
            break
        kept.append({"role": h["role"], "content": c})
        remaining_budget -= cost

    kept.reverse()

    trimmed = len(valid_history) - len(kept)
    if trimmed > 0:
        logger.info(f"上下文截取: 丢弃 {trimmed} 条早期消息，保留最近 {len(kept)} 条 | 预算 {input_budget} tokens")

    return [system_msg] + kept + [current_user_msg]


class ChatAgent(RoutedAgent, TCGAgentMixin):
    def __init__(self, llm_service, event_bridge, db):
        super().__init__("通用对话")
        self._init_tcg(llm_service, event_bridge, db)

    @message_handler
    async def handle_chat(
        self, message: ChatRequest, ctx: MessageContext,
    ) -> AgentResponse:
        mid = message.text_model_id or None
        has_images = bool(message.image_urls)
        if has_images and message.vision_model_id:
            mid = message.vision_model_id

        try:
            _, model = await self._llm_service.get_model_config(mid, "vision" if has_images else "chat")
            context_window = model.context_window or 32768
            max_output = model.max_tokens or 4096
        except Exception:
            context_window, max_output = 32768, 4096

        msgs = _build_messages(
            history=message.history,
            current_msg=message.message,
            context_summary=message.context_summary,
            context_window=context_window,
            max_output_tokens=max_output,
            image_urls=message.image_urls if has_images else None,
        )
        img_info = f" | {len(message.image_urls)} 张图片" if has_images else ""
        logger.info(f"多轮对话: {len(msgs)} 条 messages | 模型窗口 {context_window} tokens{img_info}")
        response = await self.call_llm(messages=msgs, model_id=mid, emit_thinking=True, stream_content=True)
        await self.emit_legacy("chat_response", {"content": response})
        return AgentResponse(success=True, data={"response": response})
