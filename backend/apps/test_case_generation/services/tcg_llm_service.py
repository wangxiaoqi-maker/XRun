"""TCG LLM 服务 — 基于 LiteLLM 统一调用，全流式输出"""
import asyncio
import json
import re
import time
from typing import Optional, Callable, Awaitable

import litellm
from litellm import acompletion
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ui_automation.models.llm_config import LLMProvider, LLMModel, LLMUsageLog, ModelType, ModelStatus
from ..core.logger import get_logger

logger = get_logger("tcg_llm")

litellm.drop_params = True

ENABLED = ModelStatus.ENABLED
TYPE_MAP = {"chat": ModelType.CHAT, "vision": ModelType.VISION, "embedding": ModelType.EMBEDDING}


class TcgLLMService:
    """基于 LiteLLM 的统一 LLM 调用服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._model_config_cache: dict[str, tuple[LLMProvider, LLMModel]] = {}

    async def get_model_config(
        self, model_id: str = None, model_type: str = "chat",
    ) -> tuple[LLMProvider, LLMModel]:
        cache_key = f"{model_id or 'default'}:{model_type}"
        if cache_key in self._model_config_cache:
            return self._model_config_cache[cache_key]

        mt_enum = TYPE_MAP.get(model_type, ModelType.CHAT)

        if model_id:
            result = await self.db.execute(
                select(LLMModel).where(LLMModel.id == model_id, LLMModel.status == ENABLED)
            )
            model = result.scalar_one_or_none()
        else:
            result = await self.db.execute(
                select(LLMModel).where(
                    LLMModel.model_type == mt_enum,
                    LLMModel.is_default == True,  # noqa: E712
                    LLMModel.status == ENABLED,
                )
            )
            model = result.scalar_one_or_none()

            if not model:
                result = await self.db.execute(
                    select(LLMModel).where(
                        LLMModel.model_type == mt_enum,
                        LLMModel.status == ENABLED,
                    ).limit(1)
                )
                model = result.scalar_one_or_none()

            if not model:
                logger.warning(f"未找到 {model_type} 类型模型，尝试任意可用模型")
                result = await self.db.execute(
                    select(LLMModel).where(LLMModel.status == ENABLED).limit(1)
                )
                model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"未找到可用的 {model_type} 模型，请先在平台配置 LLM 模型")

        result = await self.db.execute(
            select(LLMProvider).where(LLMProvider.id == model.provider_id)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            raise ValueError(f"模型 {model.model_id} 对应的供应商不存在")

        self._model_config_cache[cache_key] = (provider, model)
        return provider, model

    def _build_litellm_model(self, provider: LLMProvider, model: LLMModel) -> str:
        prefix = getattr(provider, "litellm_prefix", None) or "openai"
        return f"{prefix}/{model.model_id}"

    async def chat_stream(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        messages: list[dict] = None,
        model_id: str = None,
        temperature: float = 0.3,
        max_tokens: int = None,
        reasoning_effort: str = None,
        on_thinking: Optional[Callable[[str], Awaitable]] = None,
        on_content: Optional[Callable[[str], Awaitable]] = None,
    ) -> tuple[str, str, dict]:
        """统一的流式 LLM 调用

        支持两种调用方式：
        1. 传入 messages: 直接作为多轮对话历史发送给 LLM
        2. 传入 system_prompt + user_prompt: 构建单轮 [system, user] 消息（向后兼容）

        始终流式输出；reasoning_effort 不为 None 时自动注入思考参数。
        返回 (content, thinking, usage_dict)。
        """
        provider, model = await self.get_model_config(model_id, "chat")
        litellm_model = self._build_litellm_model(provider, model)

        model_limit = model.max_tokens or 4096
        requested = max_tokens or model_limit
        effective_max_tokens = min(requested, model_limit)

        if messages:
            chat_messages = messages
        else:
            chat_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

        kwargs: dict = {
            "model": litellm_model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": effective_max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
            "api_key": provider.api_key or "sk-placeholder",
        }

        prefix = getattr(provider, "litellm_prefix", None) or "openai"
        if prefix == "openai":
            kwargs["api_base"] = provider.base_url
            kwargs["client"] = AsyncOpenAI(
                api_key=provider.api_key or "sk-placeholder",
                base_url=provider.base_url,
            )

        mid_lower = (model.model_id or "").lower()
        builtin_thinking = "thinking" in mid_lower
        temp_locked = "kimi-k2" in mid_lower or "o3" in mid_lower or "o4" in mid_lower
        if temp_locked or builtin_thinking:
            kwargs["temperature"] = 1.0
        if builtin_thinking:
            logger.info(f"模型 {model.model_id} 内置思考能力，跳过 reasoning_effort")
        elif reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort

        prompt_chars = 0
        for m in chat_messages:
            c = m.get("content", "")
            if isinstance(c, str):
                prompt_chars += len(c)
            elif isinstance(c, list):
                prompt_chars += sum(len(p.get("text", "")) for p in c if isinstance(p, dict) and p.get("type") == "text")
        logger.info(f"LLM 调用: {litellm_model} | {len(chat_messages)} 条消息 | {prompt_chars} 字符 | max_tokens={effective_max_tokens}")
        t0 = time.time()

        response = await self._acompletion_with_retry(kwargs)

        thinking_buf = ""
        content_buf = ""
        finish_reason = None
        usage_info: dict = {}
        has_native_reasoning = False
        raw_stream = ""
        tag_phase = 0  # 0=detecting, 1=in_think, 2=post_think, -1=no_tags

        async for chunk in response:
            if hasattr(chunk, "usage") and chunk.usage:
                usage_info = {
                    "input_tokens": getattr(chunk.usage, "prompt_tokens", 0) or 0,
                    "output_tokens": getattr(chunk.usage, "completion_tokens", 0) or 0,
                    "total_tokens": getattr(chunk.usage, "total_tokens", 0) or 0,
                }

            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            rc = getattr(delta, "reasoning_content", None)
            if rc:
                has_native_reasoning = True
                thinking_buf += rc
                if on_thinking:
                    try:
                        await on_thinking(thinking_buf)
                    except Exception as e:
                        logger.warning(f"on_thinking 回调异常: {e}")

            if delta.content:
                if has_native_reasoning:
                    content_buf += delta.content
                    if on_content:
                        try:
                            await on_content(content_buf)
                        except Exception as e:
                            logger.warning(f"on_content 回调异常: {e}")
                else:
                    raw_stream += delta.content
                    tag_phase = self._detect_tag_phase(raw_stream, tag_phase)
                    prev_t, prev_c = thinking_buf, content_buf
                    thinking_buf, content_buf = self._extract_think_parts(raw_stream, tag_phase)
                    if on_thinking and thinking_buf != prev_t:
                        try:
                            await on_thinking(thinking_buf)
                        except Exception as e:
                            logger.warning(f"on_thinking 回调异常: {e}")
                    if on_content and content_buf != prev_c and content_buf:
                        try:
                            await on_content(content_buf)
                        except Exception as e:
                            logger.warning(f"on_content 回调异常: {e}")

        if not has_native_reasoning and raw_stream:
            thinking_buf, content_buf = self._finalize_think_tags(raw_stream)

        elapsed = round(time.time() - t0, 1)
        truncated = finish_reason == "length"
        usage_str = f" | tokens={usage_info.get('total_tokens', '?')}" if usage_info else ""
        logger.info(
            f"LLM 完成: {litellm_model} | {elapsed}s | "
            f"thinking={len(thinking_buf)}字 content={len(content_buf)}字"
            f"{usage_str}"
            f"{' | ⚠️ 输出被截断' if truncated else ''}"
        )

        if usage_info:
            await self._record_usage(
                provider_id=provider.id, model_id=model.id,
                usage=usage_info, latency_ms=int(elapsed * 1000),
                request_type="tcg_chat",
            )

        return content_buf, thinking_buf, usage_info

    @staticmethod
    async def _acompletion_with_retry(kwargs: dict, max_retries: int = 5):
        """带指数退避重试的 acompletion 调用，覆盖限流和并发限制"""
        for attempt in range(max_retries):
            try:
                return await acompletion(**kwargs)
            except litellm.RateLimitError as e:
                if attempt < max_retries - 1:
                    err_msg = str(e)
                    is_concurrency = "concurrency" in err_msg
                    wait = 2 * (attempt + 1) if is_concurrency else 5 * (attempt + 1)
                    tag = "并发" if is_concurrency else "限流"
                    logger.warning(f"{tag}重试 {attempt + 1}/{max_retries}，等待 {wait}s")
                    await asyncio.sleep(wait)
                else:
                    raise

    @staticmethod
    def _detect_tag_phase(raw: str, current: int) -> int:
        """检测 <think> 标签阶段: 0=检测中, 1=在标签内, 2=标签已结束, -1=无标签"""
        if current != 0:
            if current == 1 and "</think>" in raw:
                return 2
            return current
        stripped = raw.lstrip()
        if stripped.startswith("<think>"):
            return 2 if "</think>" in raw else 1
        return -1 if stripped else 0

    @staticmethod
    def _extract_think_parts(raw: str, phase: int) -> tuple[str, str]:
        """根据 tag_phase 从 raw 中提取 thinking 和 content"""
        if phase == -1 or phase == 0:
            return "", raw
        s = raw.index("<think>") + 7
        if phase == 2:
            e = raw.index("</think>")
            return raw[s:e], raw[e + 8:].lstrip()
        return raw[s:], ""

    @staticmethod
    def _finalize_think_tags(raw: str) -> tuple[str, str]:
        """流结束后，从原始内容中分离 thinking 和 content"""
        match = re.search(r'<think>(.*?)</think>', raw, re.DOTALL)
        if match:
            thinking = match.group(1).strip()
            content = re.sub(r'<think>.*?</think>\s*', '', raw, flags=re.DOTALL).strip()
            return thinking, content
        return "", raw

    async def _record_usage(self, provider_id: str, model_id: str, usage: dict, latency_ms: int, request_type: str = "tcg_chat"):
        try:
            log = LLMUsageLog(
                provider_id=provider_id, model_id=model_id,
                request_type=request_type,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_ms=latency_ms, success=True,
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.warning(f"用量记录写入失败（已回滚）: {e}")

    async def chat_with_vision(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: str,
        model_id: str = None,
    ) -> str:
        """调用视觉模型分析图片"""
        import base64

        provider, model = await self.get_model_config(model_id, "vision")
        litellm_model = self._build_litellm_model(provider, model)

        with open(image_path, "rb") as f:
            image_data = f.read()

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64.b64encode(image_data).decode()}"
                        },
                    },
                ],
            },
        ]

        kwargs: dict = {
            "model": litellm_model,
            "messages": messages,
            "max_tokens": 2048,
            "api_key": provider.api_key or "sk-placeholder",
        }
        prefix = getattr(provider, "litellm_prefix", None) or "openai"
        if prefix == "openai":
            kwargs["api_base"] = provider.base_url
            kwargs["client"] = AsyncOpenAI(
                api_key=provider.api_key or "sk-placeholder",
                base_url=provider.base_url,
            )

        logger.info(f"Vision 调用: {litellm_model}")
        resp = await acompletion(**kwargs)
        content = resp.choices[0].message.content or ""
        logger.info(f"Vision 响应: {len(content)} 字")
        return content

    @staticmethod
    def extract_json(text: str) -> Optional[dict]:
        if not text or not text.strip():
            return None

        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```\w*\n?', '', text)
            text = re.sub(r'\n?```\s*$', '', text)
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        for key in ("test_cases", "test_points"):
            pattern = r'"' + key + r'"\s*:\s*\['
            m = re.search(pattern, text)
            if not m:
                continue

            array_start = text.index("[", m.start())
            depth = 0
            complete_ends: list[int] = []
            i = array_start + 1
            in_str = False
            escape = False

            while i < len(text):
                ch = text[i]
                if escape:
                    escape = False
                    i += 1
                    continue
                if ch == '\\' and in_str:
                    escape = True
                elif ch == '"':
                    in_str = not in_str
                elif not in_str:
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            complete_ends.append(i)
                i += 1

            while complete_ends:
                last_complete = complete_ends[-1]
                repaired = '{"' + key + '": ' + text[array_start:last_complete + 1] + "]}"
                try:
                    result = json.loads(repaired)
                    logger.info(f"截断 JSON 修复成功: {key}={len(complete_ends)} 个对象")
                    return result
                except json.JSONDecodeError:
                    complete_ends.pop()

            logger.warning(f"截断 JSON 修复失败: 无法解析任何完整的 {key} 对象")

        return None
