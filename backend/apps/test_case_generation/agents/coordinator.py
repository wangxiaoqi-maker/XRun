"""CoordinatorAgent — 纯消息驱动编排中心

通过 autogen-core 的 send_message 向 Worker Agent 分发任务，
Worker Agent 通过 @message_handler 接收消息并返回结果。
"""
import asyncio
import base64
import os

from autogen_core import RoutedAgent, MessageContext, message_handler, AgentId

from .mixin import TCGAgentMixin
from .messages import (
    UserRequest, AgentResponse,
    ParseDocumentRequest, LoadSkillsRequest, LoadSkillsResponse,
    KnowledgeSearchRequest, KnowledgeSearchResponse,
    ExtractTestPointsRequest, ModifyTestPointsRequest,
    GenerateCasesRequest, ModifyCasesRequest,
    ReviewCasesRequest, ChatRequest,
)
from ..core.logger import get_logger

logger = get_logger("coordinator")

_GEN_VERBS = ("生成", "写出", "创建", "编写", "设计", "给我", "列出")
_GEN_OBJECTS = ("用例", "测试用例", "测试case", "test case", "testcase")


class CoordinatorAgent(RoutedAgent, TCGAgentMixin):

    def __init__(self, llm_service, event_bridge, db, context):
        super().__init__("协调中心")
        self._init_tcg(llm_service, event_bridge, db, context)

    def _agent(self, type_name: str) -> AgentId:
        return AgentId(type_name, self.id.key)

    @message_handler
    async def handle_request(
        self, message: UserRequest, ctx: MessageContext,
    ) -> AgentResponse:
        logger.info(f"收到意图: {message.intent}")

        match message.intent:
            case "upload_document":
                return await self._flow_upload(message, ctx)
            case "describe_requirement":
                return await self._flow_describe(message, ctx)
            case "confirm_test_points":
                return await self._flow_confirm(message, ctx)
            case "modify_test_points":
                return await self._flow_modify_points(message, ctx)
            case "generate_cases":
                return await self._flow_generate(message, ctx)
            case "modify_cases":
                return await self._flow_modify_cases(message, ctx)
            case "review_cases":
                return await self._flow_review(message, ctx)
            case _:
                return await self._flow_chat(message, ctx)

    # ──────── Skills + RAG 并行获取 ────────

    async def _load_skills_and_rag(
        self, query: str, project_id: str,
    ) -> tuple[str, str]:
        skill_resp, kb_resp = await asyncio.gather(
            self.send_message(
                LoadSkillsRequest(
                    categories=["tcg_method", "tcg_case", "general"],
                    selected_keys=self._context.selected_skills,
                ),
                self._agent("skill_loader"),
            ),
            self.send_message(
                KnowledgeSearchRequest(query=query, project_id=project_id),
                self._agent("kb_search"),
            ),
        )
        skill_block = skill_resp.skill_block if isinstance(skill_resp, LoadSkillsResponse) else ""
        rag_context = kb_resp.context if isinstance(kb_resp, KnowledgeSearchResponse) else ""
        if skill_block:
            logger.info(f"Skills 已加载: {', '.join(skill_resp.skill_names)}")
        else:
            logger.warning("未加载到任何 Skills")
        return skill_block, rag_context

    # ──────── 流程 1: 上传文档 → 测试点 ────────

    async def _flow_upload(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        if not msg.file_ids:
            return AgentResponse(success=False, error="未提供文件")

        self._context.test_points = []
        self._context.confirmed_point_ids = set()
        self._context.generated_cases = []

        parse_result = await self.send_message(
            ParseDocumentRequest(file_ids=msg.file_ids, vision_model_id=msg.vision_model_id),
            self._agent("doc_parser"),
        )
        if not parse_result.success:
            return parse_result

        parsed_docs = parse_result.data.get("parsed_documents", [])
        self._context.parsed_documents = parsed_docs
        await self.emit_progress(f"已解析 {len(parsed_docs)} 个文档，开始提取测试点")

        self._async_index_documents(msg.project_id, msg.file_ids, parsed_docs)

        skill_block, rag_context = await self._load_skills_and_rag(
            msg.content, msg.project_id,
        )

        result = await self.send_message(
            ExtractTestPointsRequest(
                parsed_documents=parsed_docs,
                user_prompt=msg.content,
                skill_block=skill_block,
                rag_context=rag_context,
            ),
            self._agent("tp_extractor"),
        )
        if result.success:
            self._context.test_points = result.data.get("test_points", [])
        return result

    # ──────── 流程 2: 纯文本需求 → 测试点 ────────

    async def _flow_describe(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        requirement = msg.content.strip()
        if requirement.startswith("/"):
            requirement = (self._context.user_requirements[-1]
                           if self._context.user_requirements else "")
        if not requirement:
            await self.emit_legacy("error", {"message": "请先描述你的测试需求"})
            return AgentResponse(success=False, error="请描述你的测试需求")

        if requirement not in self._context.user_requirements:
            self._context.user_requirements.append(requirement)

        skill_block, rag_context = await self._load_skills_and_rag(
            requirement, msg.project_id,
        )

        result = await self.send_message(
            ExtractTestPointsRequest(
                requirement_text=requirement,
                user_prompt=requirement,
                skill_block=skill_block,
                rag_context=rag_context,
            ),
            self._agent("tp_extractor"),
        )
        if result.success:
            self._context.test_points = result.data.get("test_points", [])
        return result

    # ──────── 流程 3: 审核反馈 → 增量补充测试点 ────────

    async def _flow_modify_points(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        self._context.point_review_round += 1

        skill_block, rag_context = await self._load_skills_and_rag(
            msg.feedback or msg.content, msg.project_id,
        )

        approved = [p for p in self._context.test_points
                    if p.get("id") not in set(msg.rejected_ids)]
        rejected = [p for p in self._context.test_points
                    if p.get("id") in set(msg.rejected_ids)]

        result = await self.send_message(
            ModifyTestPointsRequest(
                feedback=msg.feedback or msg.content,
                rejected_point_ids=msg.rejected_ids,
                approved_points=approved,
                rejected_points=rejected,
                original_requirement="\n".join(self._context.user_requirements),
                skill_block=skill_block,
                rag_context=rag_context,
            ),
            self._agent("tp_extractor"),
        )

        if result.success:
            new_points = result.data.get("supplement_points", [])
            self._context.merge_supplement_points(new_points)
            await self.emit_legacy("test_points_updated", {
                "test_points": self._context.test_points,
            })
        return result

    # ──────── 流程 4: 确认测试点 → 生成用例 ────────

    async def _flow_confirm(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        if not self._context.test_points:
            await self.emit_legacy("error", {"message": "没有测试点可确认"})
            return AgentResponse(success=False, error="没有测试点")

        if msg.confirmed_points:
            self._context.confirmed_point_ids = {
                p.get("id") for p in msg.confirmed_points
            }
        elif not self._context.confirmed_point_ids:
            self._context.confirmed_point_ids = {
                p.get("id") for p in self._context.test_points
            }

        return await self._flow_generate(msg, ctx)

    # ──────── 流程 5: 生成用例 ────────

    async def _flow_generate(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        confirmed = [p for p in self._context.test_points
                     if p.get("id") in self._context.confirmed_point_ids]
        if not confirmed:
            await self.emit_legacy("error", {"message": "没有已确认的测试点"})
            return AgentResponse(success=False, error="没有已确认的测试点")

        skill_block, rag_context = await self._load_skills_and_rag(
            msg.content or "生成测试用例", msg.project_id,
        )

        req_context = self._build_requirement_context()

        result = await self.send_message(
            GenerateCasesRequest(
                confirmed_points=confirmed,
                all_points=self._context.test_points,
                requirement_context=req_context,
                project_id=msg.project_id,
                module_name=msg.module_name,
                skill_block=skill_block,
                rag_context=rag_context,
            ),
            self._agent("tc_generator"),
        )
        if result.success:
            self._context.generated_cases = result.data.get("cases", [])
        return result

    # ──────── 流程 6: 审核反馈 → 增量补充用例 ────────

    async def _flow_modify_cases(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        self._context.case_review_round += 1

        skill_block, rag_context = await self._load_skills_and_rag(
            msg.feedback or msg.content, msg.project_id,
        )

        rejected_set = set(msg.rejected_ids)
        approved = [c for c in self._context.generated_cases
                    if c.get("id") not in rejected_set]
        rejected = [c for c in self._context.generated_cases
                    if c.get("id") in rejected_set]
        confirmed = [p for p in self._context.test_points
                     if p.get("id") in self._context.confirmed_point_ids]

        result = await self.send_message(
            ModifyCasesRequest(
                feedback=msg.feedback or msg.content,
                rejected_case_ids=msg.rejected_ids,
                approved_cases=approved,
                rejected_cases=rejected,
                confirmed_points=confirmed,
                skill_block=skill_block,
                rag_context=rag_context,
            ),
            self._agent("tc_generator"),
        )

        if result.success:
            new_cases = result.data.get("supplement_cases", [])
            self._context.merge_supplement_cases(new_cases)
            await self.emit_legacy("test_cases_updated", {
                "test_cases": self._context.generated_cases,
            })
        return result

    # ──────── 流程 7: 质量评审 ────────

    async def _flow_review(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        cases = self._context.generated_cases
        if not cases:
            return AgentResponse(success=False, error="没有可评审的用例")

        return await self.send_message(
            ReviewCasesRequest(cases=cases),
            self._agent("quality_reviewer"),
        )

    # ──────── 辅助方法 ────────

    def _async_index_documents(self, project_id: str, file_ids: list[str], parsed_docs: list[dict]):
        """后台异步入库到知识库，不阻塞主流程"""
        async def _do_index():
            try:
                from apps.ui_automation.database import AsyncSessionLocal
                from ..knowledge.service import KnowledgeService
                async with AsyncSessionLocal() as db:
                    kb = KnowledgeService(db)
                    for doc in parsed_docs:
                        fid = doc.get("file_id", file_ids[0] if file_ids else "")
                        content = doc.get("content", "")
                        if content:
                            await kb.index_document(project_id, fid, content)
            except Exception as e:
                logger.warning(f"知识库后台入库失败: {e}")
        asyncio.create_task(_do_index())

    def _build_requirement_context(self, max_chars: int = 3000) -> str:
        """从 parsed_documents 提取需求摘要，为用例生成提供上下文"""
        docs = self._context.parsed_documents
        if not docs:
            return ""
        combined = "\n\n".join(d.get("content", "") for d in docs)
        if len(combined) <= max_chars:
            return combined
        return combined[:max_chars] + "\n\n... (需求内容已截取前 3000 字)"

    # ──────── 流程 8: 通用对话 ────────

    async def _flow_chat(self, msg: UserRequest, ctx: MessageContext) -> AgentResponse:
        content = msg.content
        if not content.startswith("/") and not msg.image_file_ids and self._has_gen_intent(content):
            return await self._ask_generation_mode(content)

        image_urls = []
        if msg.image_file_ids:
            image_urls = await self._load_image_urls(msg.image_file_ids)
            if image_urls:
                await self.emit_progress(f"正在分析 {len(image_urls)} 张图片...")

        return await self.send_message(
            ChatRequest(
                message=content or "请分析这些图片的内容",
                context_summary=self._context.get_context_summary(),
                history=self._context.messages[:-1],
                text_model_id=self._context.text_model_id,
                image_urls=image_urls,
                vision_model_id=self._context.vision_model_id,
            ),
            self._agent("chat"),
        )

    async def _load_image_urls(self, file_ids: list[str]) -> list[str]:
        from ..repositories.file_repo import FileRepository
        repo = FileRepository(self._db)
        urls = []
        mime_map = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "webp": "image/webp",
        }
        for fid in file_ids:
            record = await repo.get_by_id(fid)
            if not record or not record.file_path or not os.path.exists(record.file_path):
                continue
            with open(record.file_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(record.file_path)[1].lower().lstrip(".")
            mime = mime_map.get(ext, "image/png")
            urls.append(f"data:{mime};base64,{data}")
        return urls

    @staticmethod
    def _has_gen_intent(msg: str) -> bool:
        m = msg.lower()
        return any(v in m for v in _GEN_VERBS) and any(o in m for o in _GEN_OBJECTS)

    async def _ask_generation_mode(self, message: str) -> AgentResponse:
        self._context.user_requirements.append(message)
        content = (
            "检测到你想**生成测试用例**，请选择生成方式：\n\n"
            "- **结构化工作流**：上传文档或基于描述，提取测试点 → 确认 → 批量生成用例 → 质量评审 → 保存入库（推荐用于正式项目）\n"
            "- **对话式生成**：我直接在对话中为你分析测试点和用例（适合快速讨论和草稿）"
        )
        actions = [
            {"id": "invoke_workflow", "label": "启动结构化工作流", "style": "primary"},
            {"id": "chat_generate", "label": "对话中直接生成", "style": "default",
             "followup": f"请基于以下需求，直接在对话中详细列出测试点和测试用例：{message}"},
            {"id": "upload_doc", "label": "上传需求文档", "style": "outline"},
        ]
        self._context.add_message("assistant", content)
        await self.emit_legacy("chat_response", {"content": content, "actions": actions})
        return AgentResponse(success=True, data={"response": content})
