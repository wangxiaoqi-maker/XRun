"""QualityReviewerAgent — 用例质量评审"""
import asyncio
import json

from autogen_core import RoutedAgent, MessageContext, message_handler

from .mixin import TCGAgentMixin
from .messages import ReviewCasesRequest, AgentResponse
from ..core.logger import get_logger
from ..services.tcg_llm_service import TcgLLMService
from ..repositories.test_case_repo import TestCaseRepository

logger = get_logger("quality_reviewer")

REVIEW_BATCH_SIZE = 3
REVIEW_CONCURRENCY = 5

REVIEW_SYSTEM_PROMPT = """你是一个专业的软件测试质量评审专家。请对每个测试用例进行评分，评分维度：
1. completeness (完整性) - 测试步骤和预期结果是否完整
2. clarity (清晰度) - 描述是否清晰、无歧义
3. coverage (覆盖度) - 是否覆盖了测试点的关键场景
4. feasibility (可执行性) - 是否可以实际执行"""

REVIEW_USER_TEMPLATE = """请对以下测试用例进行质量评审，每个维度 1-5 分：

{cases_text}

请以 JSON 格式返回评审结果：
{{
  "reviews": [
    {{
      "case_no": "TC-001",
      "completeness": 4,
      "clarity": 5,
      "coverage": 3,
      "feasibility": 4,
      "comment": "简短评价"
    }}
  ]
}}"""


def _default_review(case_no: str) -> dict:
    return {
        "case_no": case_no,
        "completeness": 3,
        "clarity": 3,
        "coverage": 3,
        "feasibility": 3,
        "total_score": 3.0,
        "comment": "自动评审失败，使用默认分数",
    }


def _ensure_total_score(review: dict):
    dims = ["completeness", "clarity", "coverage", "feasibility"]
    scores = [review.get(d, 3) for d in dims]
    review["total_score"] = round(sum(scores) / len(scores), 1)


def _compute_summary(reviews: list[dict]) -> dict:
    if not reviews:
        return {"avg_score": 0, "count": 0}
    totals = [r.get("total_score", 0) for r in reviews]
    dims = ["completeness", "clarity", "coverage", "feasibility"]
    dim_avgs = {d: round(sum(r.get(d, 0) for r in reviews) / len(reviews), 1) for d in dims}
    return {
        "avg_score": round(sum(totals) / len(totals), 1),
        "count": len(reviews),
        "dimensions": dim_avgs,
        "high_quality": sum(1 for t in totals if t >= 4.0),
        "needs_improvement": sum(1 for t in totals if t < 3.0),
    }


class QualityReviewerAgent(RoutedAgent, TCGAgentMixin):
    def __init__(self, llm_service, event_bridge, db, context=None):
        super().__init__("质量评审")
        self._init_tcg(llm_service, event_bridge, db, context)
        self._case_repo = TestCaseRepository(db)

    @message_handler
    async def handle_review(
        self, message: ReviewCasesRequest, ctx: MessageContext
    ) -> AgentResponse:
        cases = message.cases or []
        if not cases:
            return AgentResponse(success=False, error="没有可评审的用例")

        await self.emit_progress(f"开始评审 {len(cases)} 条用例", percent=5)
        batches = [
            cases[i : i + REVIEW_BATCH_SIZE]
            for i in range(0, len(cases), REVIEW_BATCH_SIZE)
        ]
        total_batches = len(batches)
        sem = asyncio.Semaphore(REVIEW_CONCURRENCY)
        all_reviews = []

        async def _review_batch(batch_idx: int, batch: list[dict]) -> list[dict]:
            async with sem:
                await self.emit_progress(
                    f"评审第 {batch_idx + 1}/{total_batches} 批 ({len(batch)} 条)",
                    percent=5 + int((batch_idx / total_batches) * 80),
                )
                cases_for_review = [
                    {
                        "case_no": c.get("case_no"),
                        "name": c.get("name"),
                        "priority": c.get("priority"),
                        "preconditions": c.get("preconditions"),
                        "test_steps": c.get("test_steps"),
                        "test_type": c.get("test_type"),
                    }
                    for c in batch
                ]
                cases_text = json.dumps(cases_for_review, ensure_ascii=False, indent=2)
                user_prompt = REVIEW_USER_TEMPLATE.format(cases_text=cases_text)
                response = await self.call_llm(
                    REVIEW_SYSTEM_PROMPT, user_prompt=user_prompt, temperature=0.1
                )
                parsed = TcgLLMService.extract_json(response)
                reviews = []
                if parsed and "reviews" in parsed:
                    reviews = parsed["reviews"]
                elif parsed and isinstance(parsed, list):
                    reviews = parsed
                if not reviews:
                    logger.warning(
                        f"第 {batch_idx + 1} 批评审解析失败, response 前200字: {response[:200]}"
                    )
                    for c in batch:
                        reviews.append(_default_review(c.get("case_no", "")))
                else:
                    for r in reviews:
                        _ensure_total_score(r)
                return reviews

        tasks = [_review_batch(i, b) for i, b in enumerate(batches)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_reviews.extend(r)
            elif isinstance(r, Exception):
                logger.warning(f"评审批次失败: {r}")

        await self.emit_progress("正在保存评审结果...", percent=90)
        saved_count = await self._save_reviews(cases, all_reviews)
        summary = _compute_summary(all_reviews)
        await self.emit_result(
            {"reviews": all_reviews, "summary": summary, "reviewed_count": saved_count}
        )
        await self.emit_legacy("quality_scores", {"reviews": all_reviews, "summary": summary})
        return AgentResponse(
            success=True,
            data={"reviews": all_reviews, "summary": summary, "reviewed_count": saved_count},
        )

    async def _save_reviews(self, cases: list[dict], reviews: list[dict]) -> int:
        review_map = {r.get("case_no"): r for r in reviews}
        saved = 0
        for c in cases:
            case_id = c.get("id")
            case_no = c.get("case_no")
            if not case_id or not case_no:
                continue
            review = review_map.get(case_no)
            if not review:
                continue
            scores = {
                "completeness": review.get("completeness", 3),
                "clarity": review.get("clarity", 3),
                "coverage": review.get("coverage", 3),
                "feasibility": review.get("feasibility", 3),
                "total_score": review.get("total_score", 3.0),
                "comment": review.get("comment", ""),
            }
            await self._case_repo.update(case_id, quality_scores=scores)
            saved += 1
        return saved
