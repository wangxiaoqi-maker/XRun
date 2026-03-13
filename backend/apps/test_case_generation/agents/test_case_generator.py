"""TestCaseGeneratorAgent — 用例生成 Agent"""
import asyncio
import uuid

from autogen_core import RoutedAgent, MessageContext, message_handler

from .mixin import TCGAgentMixin
from .messages import GenerateCasesRequest, ModifyCasesRequest, AgentResponse
from ..core.logger import get_logger
from ..core.prompts import (
    build_test_case_system_prompt,
    build_test_case_user_prompt,
    build_modify_cases_system_prompt,
    build_modify_cases_user_prompt,
)
from ..services.tcg_llm_service import TcgLLMService

logger = get_logger("tc_generator")

BATCH_SIZE = 12
CONCURRENCY = 1


class TestCaseGeneratorAgent(RoutedAgent, TCGAgentMixin):
    def __init__(self, llm_service, event_bridge, db, context=None):
        super().__init__("用例生成")
        self._init_tcg(llm_service, event_bridge, db, context)

    @message_handler
    async def handle_generate(
        self, message: GenerateCasesRequest, ctx: MessageContext
    ) -> AgentResponse:
        if not message.confirmed_points:
            return AgentResponse(success=False, error="没有已确认的测试点")

        batches = self._split_into_batches(message.confirmed_points)
        total_batches = len(batches)

        await self.emit_progress(
            f"共 {len(message.confirmed_points)} 个测试点，分 {total_batches} 批并行生成",
            percent=5,
        )

        sem = asyncio.Semaphore(CONCURRENCY)
        all_cases = []

        async def _generate_batch(batch_idx: int, points: list[dict]) -> list[dict]:
            async with sem:
                point_ids = [p.get("id", "") for p in points]
                await self.emit_progress(
                    f"第 {batch_idx + 1}/{total_batches} 批: {', '.join(point_ids)}",
                    percent=5 + int((batch_idx / total_batches) * 70),
                )

                system_prompt = build_test_case_system_prompt()
                user_prompt = build_test_case_user_prompt(
                    confirmed_points=points,
                    skill_prompt_block=message.skill_block or "",
                    requirement_context=message.requirement_context or "",
                    all_points=message.all_points or [],
                    rag_context=message.rag_context or "",
                )

                response = await self.call_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    emit_thinking=(batch_idx == 0),
                    stream_content=(batch_idx == 0),
                )

                parsed = TcgLLMService.extract_json(response)
                cases = []
                if parsed and "test_cases" in parsed:
                    cases = parsed["test_cases"]
                elif parsed and isinstance(parsed, list):
                    cases = parsed

                if not cases:
                    logger.warning(
                        f"第 {batch_idx + 1} 批解析失败, response 前300字: {response[:300]}"
                    )
                    return []

                await self.emit_result(
                    {
                        "batch": batch_idx + 1,
                        "total_batches": total_batches,
                        "cases": cases,
                        "count": len(cases),
                    },
                )
                return cases

        tasks = [_generate_batch(i, batch) for i, batch in enumerate(batches)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, list):
                all_cases.extend(r)
            elif isinstance(r, Exception):
                logger.warning(f"用例生成批次失败: {r}")

        if not all_cases:
            return AgentResponse(success=False, error="所有批次均未生成有效用例")

        self._reindex_cases(all_cases)
        self._normalize_fields(all_cases, message.module_name or "")

        await self.emit_progress(f"共生成 {len(all_cases)} 条用例，等待审查", percent=95)
        await self.emit_legacy(
            "test_cases",
            {
                "test_cases": all_cases,
                "count": len(all_cases),
                "message": f"共生成 {len(all_cases)} 条用例，请审查后点击「保存入库」",
            },
        )

        return AgentResponse(
            success=True,
            data={"cases": all_cases, "count": len(all_cases)},
        )

    @message_handler
    async def handle_modify(
        self, message: ModifyCasesRequest, ctx: MessageContext
    ) -> AgentResponse:
        system_prompt = build_modify_cases_system_prompt()
        user_prompt = build_modify_cases_user_prompt(
            feedback=message.feedback,
            approved_cases=message.approved_cases,
            rejected_cases=message.rejected_cases,
            confirmed_points=message.confirmed_points,
            skill_block=message.skill_block or "",
            rag_context=message.rag_context or "",
        )

        await self.emit_progress("根据反馈补充生成用例...", percent=20)

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            emit_thinking=True,
            stream_content=True,
        )

        parsed = TcgLLMService.extract_json(response)
        supplement_cases = []
        if parsed and "test_cases" in parsed:
            supplement_cases = parsed["test_cases"]
        elif parsed and isinstance(parsed, list):
            supplement_cases = parsed

        if not supplement_cases:
            logger.warning(f"增量补充解析失败, response 前300字: {response[:300]}")
            return AgentResponse(success=False, error="未解析到有效补充用例")

        self._reindex_cases(supplement_cases)
        self._normalize_fields(supplement_cases, "")

        await self.emit_legacy(
            "supplement_cases",
            {"supplement_cases": supplement_cases, "count": len(supplement_cases)},
        )

        return AgentResponse(
            success=True,
            data={"supplement_cases": supplement_cases, "count": len(supplement_cases)},
        )

    def _split_into_batches(self, points: list[dict]) -> list[list[dict]]:
        return [points[i : i + BATCH_SIZE] for i in range(0, len(points), BATCH_SIZE)]

    @staticmethod
    def _reindex_cases(cases: list[dict]):
        for i, c in enumerate(cases, 1):
            c["case_no"] = f"TC-{i:03d}"

    @staticmethod
    def _normalize_fields(cases: list[dict], default_module: str = ""):
        for c in cases:
            if "id" not in c:
                c["id"] = f"tmp-{uuid.uuid4().hex[:8]}"
            if "steps" in c and "test_steps" not in c:
                c["test_steps"] = c.pop("steps")
            if "module" in c and "module_name" not in c:
                c["module_name"] = c.pop("module") or default_module or "未分类"
            elif "module_name" not in c:
                c["module_name"] = default_module or "未分类"
            steps = c.get("test_steps", [])
            if "expected_results" not in c and isinstance(steps, list) and steps:
                c["expected_results"] = " ".join(
                    s.get("expected", "") if isinstance(s, dict) else "" for s in steps
                )
            for key in ("case_no", "name", "priority", "preconditions", "test_steps", "expected_results", "test_type"):
                if key not in c:
                    c[key] = [] if key == "test_steps" else ""
