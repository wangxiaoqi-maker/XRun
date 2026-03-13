"""知识库 API — 构建/检索/统计/清空"""
import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ui_automation.database import get_db
from apps.ui_automation.api.auth import get_current_user
from ..knowledge.service import KnowledgeService
from ..schemas import ApiResponse

router = APIRouter(tags=["TCG-知识库"])


@router.post("/knowledge/build")
async def build_knowledge(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动触发知识库重建（清空后重新索引所有文档和用例）"""
    kb = KnowledgeService(db)
    count = await kb.rebuild_project(project_id)
    return ApiResponse(data={"indexed_count": count}, message=f"已索引 {count} 条向量")


@router.get("/knowledge/stats")
async def knowledge_stats(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库统计信息"""
    kb = KnowledgeService(db)
    stats = await kb.get_stats(project_id)
    return ApiResponse(data=stats)


@router.post("/knowledge/search")
async def search_knowledge(
    project_id: str,
    query: str,
    top_k: int = 10,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动搜索知识库（调试用）"""
    kb = KnowledgeService(db)
    context, chunks = await kb.search(project_id, query, top_k)
    return ApiResponse(data={
        "context": context,
        "chunks": [{"id": c.get("id"), "score": c.get("score"), "content": c.get("content", "")[:200], "source_type": c.get("source_type")} for c in chunks],
    })


@router.delete("/knowledge/clear")
async def clear_knowledge(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """清空项目知识库"""
    kb = KnowledgeService(db)
    await kb._vector.delete_by_project(project_id)
    from ..repositories.knowledge_repo import KnowledgeRepository
    repo = KnowledgeRepository(db)
    count = await repo.clear_project(project_id)
    return ApiResponse(message=f"已清空 {count} 条记录")
