"""TestPointExtractorAgent — 测试点提取 Agent"""
import asyncio
import re

from autogen_core import RoutedAgent, MessageContext, message_handler

from .mixin import TCGAgentMixin
from .messages import ExtractTestPointsRequest, ModifyTestPointsRequest, AgentResponse
from ..core.logger import get_logger
from ..core.prompts import build_test_point_system_prompt, build_test_point_user_prompt
from ..services.tcg_llm_service import TcgLLMService

logger = get_logger("tp_extractor")
MAX_CHUNK_CHARS = 8000
CONCURRENCY = 2


class TestPointExtractorAgent(RoutedAgent, TCGAgentMixin):
    def __init__(self, llm_service, event_bridge, db, context=None):
        super().__init__("测试点提取")
        self._init_tcg(llm_service, event_bridge, db, context)

    @message_handler
    async def handle_extract(
        self, message: ExtractTestPointsRequest, ctx: MessageContext
    ) -> AgentResponse:
        if message.parsed_documents:
            return await self._extract_from_documents(message)
        if message.requirement_text:
            return await self._extract_from_text(message)
        return AgentResponse(success=False, error="没有可分析的内容，请上传文档或描述需求")

    async def _extract_from_documents(self, msg: ExtractTestPointsRequest) -> AgentResponse:
        chunks = self._split_documents_into_chunks(msg.parsed_documents)
        total = len(chunks)
        await self.emit_progress(f"共 {total} 个分析批次，开始并行提取测试点...", percent=10)

        sem = asyncio.Semaphore(CONCURRENCY)
        all_points = []
        completed = [0]

        async def _extract_chunk(idx: int, chunk: dict) -> list[dict]:
            async with sem:
                await self.emit_progress(
                    f"提取第 {idx + 1}/{total} 批: {chunk['source']}",
                    percent=10 + int((idx / total) * 70),
                )
                sys_p = build_test_point_system_prompt()
                user_p = build_test_point_user_prompt(
                    parsed_content=chunk["content"],
                    rag_context=msg.rag_context,
                    user_prompt=msg.user_prompt,
                    skill_prompt_block=msg.skill_block,
                )
                if idx == 0:
                    resp = await self.call_llm(sys_p, user_p, emit_thinking=True, stream_content=True)
                else:
                    resp = await self.call_llm(sys_p, user_p)
                points = self._parse_points(resp)
                completed[0] += 1
                if points:
                    await self.emit_result({
                        "points": points,
                        "batch": idx + 1,
                        "total_batches": total,
                        "message": f"第 {idx + 1} 批提取了 {len(points)} 个测试点",
                    })
                return points

        tasks = [_extract_chunk(i, c) for i, c in enumerate(chunks)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_points.extend(r)
            elif isinstance(r, Exception):
                logger.warning(f"测试点提取批次失败: {r}")

        all_points = self._deduplicate_and_reindex(all_points)
        await self.emit_progress(f"共提取 {len(all_points)} 个测试点", percent=95)
        await self.emit_legacy("test_points", {
            "test_points": all_points,
            "count": len(all_points),
            "message": f"共提取 {len(all_points)} 个测试点，请确认后生成用例",
        })
        return AgentResponse(success=True, data={"test_points": all_points, "count": len(all_points)})

    async def _extract_from_text(self, msg: ExtractTestPointsRequest) -> AgentResponse:
        await self.emit_progress("分析需求描述中...", percent=20)
        sys_p = build_test_point_system_prompt()
        user_p = build_test_point_user_prompt(
            parsed_content=msg.requirement_text,
            rag_context=msg.rag_context,
            user_prompt=msg.user_prompt,
            skill_prompt_block=msg.skill_block,
        )
        resp = await self.call_llm(sys_p, user_p, emit_thinking=True, stream_content=True)
        points = self._parse_points(resp)
        if not points:
            logger.error(f"[TestPointExtractor] JSON 解析失败, response 前500字: {resp[:500]}")
            return AgentResponse(success=False, error="模型未返回有效测试点")
        points = self._deduplicate_and_reindex(points)
        await self.emit_legacy("test_points", {
            "test_points": points,
            "count": len(points),
            "message": f"共提取 {len(points)} 个测试点，请确认后生成用例",
        })
        return AgentResponse(success=True, data={"test_points": points, "count": len(points)})

    @message_handler
    async def handle_modify(
        self, message: ModifyTestPointsRequest, ctx: MessageContext
    ) -> AgentResponse:
        prompt = self._build_supplement_prompt(message)
        sys_p = build_test_point_system_prompt()
        resp = await self.call_llm(sys_p, prompt)
        supplement_points = self._parse_points(resp)
        if not supplement_points:
            return AgentResponse(success=False, error="模型未返回有效增量测试点")
        supplement_points = self._deduplicate_and_reindex(supplement_points)
        await self.emit_legacy("test_points", {
            "test_points": supplement_points,
            "count": len(supplement_points),
            "message": f"补充了 {len(supplement_points)} 个测试点",
        })
        return AgentResponse(success=True, data={"supplement_points": supplement_points})

    def _build_supplement_prompt(self, msg: ModifyTestPointsRequest) -> str:
        approved = "\n".join(
            f"- {p.get('title', p.get('name', ''))}: {p.get('description', '')}"
            for p in msg.approved_points
        )
        rejected = "\n".join(
            f"- {p.get('title', p.get('name', ''))}: {p.get('description', '')}"
            for p in msg.rejected_points
        )
        return f"""基于用户反馈，补充测试点。

## 用户反馈
{msg.feedback}

## 已采纳的测试点
{approved or '无'}

## 被拒绝的测试点（请勿重复）
{rejected or '无'}

{f"## 原始需求{chr(10)}{msg.original_requirement}" if msg.original_requirement else ""}

{msg.skill_block}

请仅输出新增的测试点，格式与提取要求一致，JSON 中 key 为 test_points。"""

    @staticmethod
    def _parse_points(response: str) -> list[dict]:
        parsed = TcgLLMService.extract_json(response)
        if parsed and "test_points" in parsed:
            return parsed["test_points"]
        if parsed and isinstance(parsed, list):
            return parsed
        return []

    def _split_documents_into_chunks(self, parsed_documents: list[dict]) -> list[dict]:
        combined = "\n\n".join(d.get("content", "") for d in parsed_documents)
        if not combined.strip():
            return []
        sections = re.split(r"\n##\s+", combined)
        chunks = []
        current = ""
        chunk_idx = 0
        for i, sec in enumerate(sections):
            if not sec.strip():
                continue
            sec_text = f"## {sec}" if i > 0 or not combined.strip().startswith("##") else sec
            if len(current) + len(sec_text) > MAX_CHUNK_CHARS:
                if current:
                    chunks.append({
                        "source": f"需求文档 (第{chunk_idx + 1}部分)" if chunk_idx > 0 else "需求文档",
                        "content": current,
                    })
                    chunk_idx += 1
                current = sec_text
            else:
                current = (current + "\n\n" + sec_text) if current else sec_text
        if current.strip():
            chunks.append({
                "source": f"需求文档 (第{chunk_idx + 1}部分)" if chunk_idx > 0 else "需求文档",
                "content": current,
            })
        if not chunks and combined:
            chunks.append({"source": "需求文档", "content": combined[:MAX_CHUNK_CHARS]})
        return chunks

    @staticmethod
    def _deduplicate_and_reindex(points: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for p in points:
            key = (p.get("name") or p.get("title") or "").strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(p)
        for i, p in enumerate(unique):
            p["id"] = f"TP-{i + 1:03d}"
        return unique
