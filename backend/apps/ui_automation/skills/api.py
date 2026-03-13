"""Skill API 路由 - 平台级 /api/v2/skills"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ui_automation.database import get_db
from apps.ui_automation.api.auth import get_current_user
from .repository import SkillRepository
from .service import SkillService
from .schemas import (
    SkillOut,
    SkillDetailOut,
    SkillInstallRequest,
    SkillImportUrlRequest,
    SkillManualCreate,
    SkillUpdate,
)

router = APIRouter(tags=["Skills"])


def _skill_out(s):
    data = SkillOut.model_validate(s)
    data.files_count = len(s.files or [])
    return data


def _skill_detail_out(s):
    return SkillDetailOut.model_validate(s)


@router.get("", response_model=dict)
async def list_skills(
    category: str | None = Query(None, description="按分类筛选"),
    enabled_only: bool = Query(True, description="仅返回已启用"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有已安装 Skills"""
    repo = SkillRepository(db)
    skills = await repo.list_all(category=category, enabled_only=enabled_only)
    return {"items": [_skill_out(s) for s in skills], "total": len(skills)}


@router.get("/search", response_model=dict)
async def search_skills(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """代理 skills.sh 搜索 API"""
    service = SkillService(db)
    result = await service.search_skills_sh(q, limit)
    return result


@router.post("/install", response_model=dict)
async def install_from_skills_sh(
    body: SkillInstallRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从 skills.sh 安装"""
    service = SkillService(db)
    try:
        skill = await service.install_from_skills_sh(body.source, body.skill_name)
        return {"success": True, "data": _skill_out(skill)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import-url", response_model=dict)
async def import_from_url(
    body: SkillImportUrlRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从 URL 导入"""
    service = SkillService(db)
    try:
        skill = await service.install_from_url(body.url)
        return {"success": True, "data": _skill_out(skill)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/manual", response_model=dict)
async def create_manual(
    body: SkillManualCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动创建 Skill"""
    service = SkillService(db)
    try:
        files_data = [f.model_dump() for f in body.files] if body.files else []
        skill = await service.create_manual(
            key=body.key,
            name=body.name,
            content=body.content,
            description=body.description,
            category=body.category or "",
            files=files_data,
        )
        return {"success": True, "data": _skill_out(skill)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{skill_id}", response_model=dict)
async def get_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 Skill 详情（含 raw_content）"""
    repo = SkillRepository(db)
    skill = await repo.get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return {"success": True, "data": _skill_detail_out(skill)}


@router.put("/{skill_id}", response_model=dict)
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新 Skill"""
    repo = SkillRepository(db)
    skill = await repo.get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    kwargs = body.model_dump(exclude_unset=True)
    updated = await repo.update(skill_id, **kwargs)
    return {"success": True, "data": _skill_out(updated)}


@router.delete("/{skill_id}", response_model=dict)
async def delete_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除 Skill"""
    repo = SkillRepository(db)
    ok = await repo.delete(skill_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Skill 不存在或为内置不可删")
    return {"success": True}


@router.post("/{skill_id}/refresh", response_model=dict)
async def refresh_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从原始 URL 重新拉取"""
    service = SkillService(db)
    skill = await service.refresh(skill_id)
    if not skill:
        raise HTTPException(status_code=400, detail="无法刷新（无 source_url 或非远程来源）")
    return {"success": True, "data": _skill_out(skill)}
