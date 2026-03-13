"""用例模块 API"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ui_automation.database import get_db
from apps.ui_automation.api.auth import get_current_user
from ..repositories.module_repo import ModuleRepository
from ..schemas import ApiResponse

router = APIRouter(tags=["TCG-模块管理"])


class ModuleCreate(BaseModel):
    project_id: str
    name: str
    parent_id: str | None = None


class ModuleRename(BaseModel):
    name: str


class ModuleOut(BaseModel):
    id: str
    project_id: str
    name: str
    parent_id: str | None = None
    sort_order: int = 0

    model_config = {"from_attributes": True}


@router.get("/modules")
async def list_modules(
    project_id: str = Query(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ModuleRepository(db)
    modules = await repo.list_by_project(project_id)
    return ApiResponse(data=[ModuleOut.model_validate(m) for m in modules])


@router.post("/modules")
async def create_module(
    req: ModuleCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ModuleRepository(db)
    try:
        module = await repo.create(req.project_id, req.name, req.parent_id)
        return ApiResponse(data=ModuleOut.model_validate(module))
    except ValueError as e:
        return ApiResponse(success=False, message=str(e))


@router.put("/modules/{module_id}")
async def rename_module(
    module_id: str,
    req: ModuleRename,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ModuleRepository(db)
    try:
        module = await repo.rename(module_id, req.name)
        return ApiResponse(data=ModuleOut.model_validate(module))
    except ValueError as e:
        return ApiResponse(success=False, message=str(e))


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ModuleRepository(db)
    await repo.delete(module_id)
    return ApiResponse(message="删除成功")
