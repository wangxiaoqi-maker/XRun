from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ui_automation.database import get_db
from apps.ui_automation.api.auth import get_current_user
from ..repositories.project_repo import ProjectRepository
from ..schemas import ProjectCreate, ProjectUpdate, ProjectOut, ApiResponse

router = APIRouter(tags=["TCG-项目管理"])


@router.get("/projects")
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    projects, total = await repo.list_all(page, page_size)

    items = []
    for p in projects:
        stats = await repo.get_stats(p.id)
        items.append(ProjectOut(
            id=p.id, name=p.name, description=p.description,
            created_at=p.created_at, updated_at=p.updated_at,
            **stats,
        ))

    return ApiResponse(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/projects")
async def create_project(
    request: ProjectCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.create(name=request.name, description=request.description)
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        return ApiResponse(success=False, message="项目不存在")
    stats = await repo.get_stats(project_id)
    return ApiResponse(data=ProjectOut(
        id=project.id, name=project.name, description=project.description,
        created_at=project.created_at, updated_at=project.updated_at,
        **stats,
    ))


@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.update(project_id, **request.model_dump(exclude_unset=True))
    if not project:
        return ApiResponse(success=False, message="项目不存在")
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    deleted = await repo.delete(project_id)
    if not deleted:
        return ApiResponse(success=False, message="项目不存在")
    return ApiResponse(message="删除成功")
