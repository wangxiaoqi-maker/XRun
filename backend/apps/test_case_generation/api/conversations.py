"""对话 API — 多智能体对话式用例生成的入口

端点：
- POST   /conversations               — 创建对话
- GET    /conversations                — 对话列表
- GET    /conversations/{id}/messages  — 消息历史
- DELETE /conversations/{id}           — 删除对话
- POST   /conversations/{id}/messages  — 发送消息（触发 Agent）
- GET    /conversations/{id}/stream    — SSE 流式推送
- GET    /conversations/{id}/history   — 对话摘要（兼容旧版）
- PUT    /conversations/{id}/config    — 更新配置
- PUT    /conversations/{id}/title     — 更新标题
"""
import asyncio
import json

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from autogen_core import AgentId

from apps.ui_automation.database import get_db, AsyncSessionLocal
from apps.ui_automation.api.auth import get_current_user
from apps.ui_automation.services.auth_service import decode_token

from ..services.conversation_engine import (
    ConversationManager, ContextStore, AgentEvent, LegacyEvent, UserIntent,
)
from ..agents.runtime_manager import RuntimeManager
from ..agents.messages import UserRequest
from ..repositories.conversation_repo import ConversationRepository
from ..repositories.review_record_repo import ReviewRecordRepository
from ..models import generate_uuid
from ..schemas import ApiResponse
from ..core.logger import get_logger

from apps.ui_automation.skills.repository import SkillRepository

logger = get_logger("conversations")

router = APIRouter(tags=["TCG-对话"])


async def _load_skill_registry(db: AsyncSession) -> list[dict]:
    repo = SkillRepository(db)
    skills = await repo.list_all(enabled_only=True)
    return [
        {"key": s.key, "name": s.name, "icon": s.icon or "📋",
         "description": s.description or "", "category": s.category}
        for s in skills
    ]


# ──────────────────────────────────────────────────────────────
#  请求/响应模型
# ──────────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    project_id: str
    text_model_id: Optional[str] = None
    vision_model_id: Optional[str] = None
    selected_skills: List[str] = Field(default=["comprehensive"])


class MessageSend(BaseModel):
    content: str = ""
    file_ids: List[str] = Field(default_factory=list)
    image_ids: List[str] = Field(default_factory=list)
    intent_override: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ConfigUpdate(BaseModel):
    text_model_id: Optional[str] = None
    vision_model_id: Optional[str] = None
    selected_skills: Optional[List[str]] = None


class TitleUpdate(BaseModel):
    title: str


# ──────────────────────────────────────────────────────────────
#  创建对话
# ──────────────────────────────────────────────────────────────

@router.post("/conversations")
async def create_conversation(
    body: ConversationCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv_id = generate_uuid()
    config = {
        "text_model_id": body.text_model_id or "",
        "vision_model_id": body.vision_model_id or "",
        "selected_skills": body.selected_skills,
    }
    conv = await repo.create(
        id=conv_id, project_id=body.project_id, config=config,
    )

    ConversationManager.create_conversation(
        conv_id=conv.id,
        project_id=body.project_id,
        text_model_id=body.text_model_id or "",
        vision_model_id=body.vision_model_id or "",
        selected_skills=body.selected_skills,
    )

    ctx = ConversationManager.get_context(conv.id)
    if ctx:
        ctx.skill_registry = await _load_skill_registry(db)

    return ApiResponse(data={
        "conversation_id": conv.id,
        "title": conv.title,
        "created_at": str(conv.created_at),
    })


# ──────────────────────────────────────────────────────────────
#  对话列表
# ──────────────────────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations(
    project_id: str = Query(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    convs = await repo.list_by_project(project_id)
    items = [
        {
            "id": c.id,
            "title": c.title,
            "status": c.status,
            "created_at": str(c.created_at),
            "updated_at": str(c.updated_at),
        }
        for c in convs
    ]
    return ApiResponse(data={"items": items})


# ──────────────────────────────────────────────────────────────
#  消息历史
# ──────────────────────────────────────────────────────────────

@router.get("/conversations/{conv_id}/messages")
async def get_messages(
    conv_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    msgs = await repo.get_messages(conv_id)
    items = [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "message_type": m.message_type,
            "metadata": m.metadata_,
            "created_at": str(m.created_at),
        }
        for m in msgs
    ]
    return ApiResponse(data={"items": items, "conversation_id": conv_id})


# ──────────────────────────────────────────────────────────────
#  删除对话
# ──────────────────────────────────────────────────────────────

@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    await repo.delete_messages(conv_id)
    await repo.delete(conv_id)
    ConversationManager.cleanup(conv_id)
    await RuntimeManager.cleanup(conv_id)
    return ApiResponse(message="对话已删除")


# ──────────────────────────────────────────────────────────────
#  发送消息（触发 Agent 执行）
# ──────────────────────────────────────────────────────────────

async def _ensure_context(conv_id: str, db: AsyncSession) -> ContextStore:
    ctx = ConversationManager.get_context(conv_id)
    if ctx:
        return ctx

    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    config = conv.config or {}
    ctx = ContextStore(
        conversation_id=conv.id,
        project_id=conv.project_id,
        text_model_id=config.get("text_model_id", ""),
        vision_model_id=config.get("vision_model_id", ""),
        selected_skills=config.get("selected_skills", ["comprehensive"]),
    )

    # 恢复持久化的结构化数据
    ctx.test_points = config.get("test_points", [])
    ctx.confirmed_point_ids = set(config.get("confirmed_point_ids", []))
    ctx.generated_cases = config.get("generated_cases", [])
    ctx.user_requirements = config.get("user_requirements", [])
    ctx.point_review_round = config.get("point_review_round", 0)
    ctx.case_review_round = config.get("case_review_round", 0)
    ctx.point_review_status = config.get("point_review_status", {})
    ctx.case_review_status = config.get("case_review_status", {})

    msgs = await repo.get_messages(conv_id, limit=50)
    for m in msgs:
        if m.role in ("user", "assistant", "system"):
            ctx.add_message(m.role, m.content or "", meta=m.metadata_)

    ctx.skill_registry = await _load_skill_registry(db)
    ConversationManager.restore_context(conv_id, ctx)
    return ctx


@router.post("/conversations/{conv_id}/messages")
async def send_message(
    conv_id: str,
    body: MessageSend,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    context = await _ensure_context(conv_id, db)

    repo = ConversationRepository(db)
    msg_meta = {}
    if body.file_ids:
        msg_meta["file_ids"] = body.file_ids
    if body.image_ids:
        msg_meta["image_ids"] = body.image_ids
    await repo.add_message(
        conversation_id=conv_id,
        role="user",
        content=body.content,
        message_type="text",
        metadata=msg_meta,
    )

    if body.content.strip():
        msg_count = await repo.message_count(conv_id)
        if msg_count <= 1:
            await repo.update_title(conv_id, body.content.strip()[:20])

    await repo.touch(conv_id)

    has_files = bool(body.file_ids)
    intent = ConversationManager.route_intent(conv_id, body.content, has_files)
    if body.intent_override:
        try:
            intent = UserIntent(body.intent_override)
        except ValueError:
            pass

    context.add_message("user", body.content, meta=msg_meta)
    generation = ConversationManager.new_task_generation(conv_id)

    metadata = body.metadata or {}
    if body.image_ids:
        metadata["image_ids"] = body.image_ids
    asyncio.create_task(
        _run_coordinator(intent, body.content, body.file_ids, conv_id,
                         context, generation, metadata)
    )

    logger.info(
        f"消息已投递: conv={conv_id[:8]} intent={intent.value} gen={generation}"
    )
    return ApiResponse(data={"intent": intent.value, "message": f"正在处理: {intent.value}"})


async def _run_coordinator(
    intent, message, file_ids, conv_id, context, generation, metadata,
):
    async with AsyncSessionLocal() as bg_db:
        if not context.skill_registry:
            context.skill_registry = await _load_skill_registry(bg_db)

        if not ConversationManager.is_current_generation(conv_id, generation):
            logger.info(f"gen={generation} 已过期, 跳过")
            return

        runtime = await RuntimeManager.get_or_create(
            conv_id, bg_db, context, generation,
        )

        bridge = RuntimeManager.get_bridge(conv_id)
        repo = ConversationRepository(bg_db)

        try:
            logger.info(f"消息分发: UserRequest(intent={intent.value}) → coordinator")

            result = await runtime.send_message(
                UserRequest(
                    intent=intent.value,
                    content=message,
                    file_ids=file_ids or [],
                    image_file_ids=metadata.get("image_ids", []),
                    conv_id=conv_id,
                    rejected_ids=metadata.get("rejected_ids", []),
                    feedback=metadata.get("feedback", ""),
                    confirmed_points=metadata.get("confirmed_points", []),
                    project_id=context.project_id,
                    text_model_id=context.text_model_id,
                    vision_model_id=context.vision_model_id,
                ),
                AgentId("coordinator", "default"),
            )

            if not ConversationManager.is_current_generation(conv_id, generation):
                logger.info(f"gen={generation} dispatch 后过期, 跳过保存")
                await bridge.emit_legacy("done", {"success": True, "cancelled": True})
                return

            logger.info(f"Coordinator 响应: success={result.success}")

            if result.success and isinstance(result.data, dict):
                resp_text = result.data.get("response", "")
                if resp_text:
                    await repo.add_message(
                        conversation_id=conv_id, role="assistant",
                        content=resp_text, message_type="text",
                        metadata={"ui_type": "assistant"},
                    )
                    context.add_message("assistant", resp_text)

            # 持久化 ContextStore 快照
            await _persist_context_snapshot(conv_id, context, repo)

        except Exception as e:
            logger.error(f"Coordinator 执行失败: {e}")
            if ConversationManager.is_current_generation(conv_id, generation):
                await bridge.emit_legacy("error", {"message": f"执行失败: {e}"})
        finally:
            is_current = ConversationManager.is_current_generation(conv_id, generation)
            await bridge.emit_legacy("done", {
                "success": True,
                "cancelled": not is_current,
            })


async def _persist_context_snapshot(conv_id: str, context: ContextStore, repo):
    snapshot = {
        "text_model_id": context.text_model_id,
        "vision_model_id": context.vision_model_id,
        "selected_skills": context.selected_skills,
        "test_points": context.test_points,
        "confirmed_point_ids": list(context.confirmed_point_ids),
        "generated_cases": context.generated_cases,
        "point_review_status": getattr(context, "point_review_status", {}),
        "case_review_status": getattr(context, "case_review_status", {}),
        "point_review_round": getattr(context, "point_review_round", 0),
        "case_review_round": getattr(context, "case_review_round", 0),
        "user_requirements": context.user_requirements,
        "parsed_documents": [
            {"file_name": d.get("file_name", ""), "content_preview": d.get("content", "")[:200]}
            for d in context.parsed_documents
        ],
    }
    await repo.update_config(conv_id, snapshot)


# ──────────────────────────────────────────────────────────────
#  SSE 流式推送
# ──────────────────────────────────────────────────────────────

@router.get("/conversations/{conv_id}/stream")
async def stream_conversation(
    conv_id: str,
    token: str = Query(default=None),
):
    if token:
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效令牌")

    async def event_generator():
        queue = ConversationManager.ensure_queue(conv_id)
        idle_count = 0

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                idle_count = 0

                if isinstance(event, AgentEvent):
                    payload = json.dumps(event.to_sse(), ensure_ascii=False)
                    yield f"event: agent_event\ndata: {payload}\n\n"
                elif isinstance(event, LegacyEvent):
                    payload = json.dumps(event.data, ensure_ascii=False)
                    yield f"event: {event.event}\ndata: {payload}\n\n"
                    if event.event == "done":
                        break

            except asyncio.TimeoutError:
                idle_count += 1
                yield f"event: ping\ndata: {json.dumps({'message': 'keepalive'})}\n\n"
                if idle_count >= 10:
                    break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ──────────────────────────────────────────────────────────────
#  对话历史（兼容旧版 — 返回摘要）
# ──────────────────────────────────────────────────────────────

@router.get("/conversations/{conv_id}/history")
async def get_history(
    conv_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    context = await _ensure_context(conv_id, db)
    return ApiResponse(data={
        "messages": context.messages,
        "summary": context.get_context_summary(),
        "test_points_count": len(context.test_points),
        "cases_count": len(context.generated_cases),
    })


# ──────────────────────────────────────────────────────────────
#  更新配置（模型 / Skills）
# ──────────────────────────────────────────────────────────────

@router.put("/conversations/{conv_id}/config")
async def update_config(
    conv_id: str,
    body: ConfigUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    context = await _ensure_context(conv_id, db)

    if body.text_model_id is not None:
        context.text_model_id = body.text_model_id
    if body.vision_model_id is not None:
        context.vision_model_id = body.vision_model_id
    if body.selected_skills is not None:
        context.selected_skills = body.selected_skills

    repo = ConversationRepository(db)
    await _persist_context_snapshot(conv_id, context, repo)
    return ApiResponse(message="配置已更新")


# ──────────────────────────────────────────────────────────────
#  更新标题
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
#  审核历史
# ──────────────────────────────────────────────────────────────

@router.get("/conversations/{conv_id}/review-history")
async def get_review_history(
    conv_id: str,
    review_type: str = Query(default=None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ReviewRecordRepository(db)
    records = await repo.get_by_conversation(conv_id, review_type)
    items = [
        {
            "id": r.id,
            "review_type": r.review_type,
            "review_status": r.review_status,
            "reviewer": r.reviewer,
            "comment": r.comment,
            "review_round": getattr(r, "review_round", 0),
            "rejected_ids": getattr(r, "rejected_ids", []),
            "created_at": str(r.created_at),
        }
        for r in records
    ]
    return ApiResponse(data={"items": items})


@router.put("/conversations/{conv_id}/title")
async def update_title(
    conv_id: str,
    body: TitleUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    await repo.update_title(conv_id, body.title)
    return ApiResponse(message="标题已更新")
