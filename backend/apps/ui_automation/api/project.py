"""
项目管理 API
"""
import uuid
import re
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.project import Project, ProjectMember
from ..models.user import User, UserRole
from .auth import get_current_user, get_current_admin

router = APIRouter(prefix="/projects", tags=["项目管理"])


def generate_project_code(name: str) -> str:
    """根据项目名称生成项目代码"""
    # 提取英文和数字
    code = re.sub(r'[^a-zA-Z0-9]', '', name)
    if not code:
        code = "PRJ"
    # 加上短UUID后缀保证唯一
    suffix = uuid.uuid4().hex[:6].upper()
    return f"{code[:10]}_{suffix}"


# ==================== 请求/响应模型 ====================

class ProjectCreate(BaseModel):
    """创建项目"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    icon: Optional[str] = Field("📁", description="项目图标")
    color: Optional[str] = Field("#184BFA", description="项目主题色")


class ProjectUpdate(BaseModel):
    """更新项目"""
    name: Optional[str] = Field(None, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    icon: Optional[str] = Field(None, description="项目图标")
    color: Optional[str] = Field(None, description="项目主题色")
    is_active: Optional[bool] = Field(None, description="是否启用")


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    code: str
    description: Optional[str]
    icon: str
    color: str
    is_active: bool
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


# ==================== API 端点 ====================

@router.get("", summary="获取项目列表")
async def list_projects(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取项目列表
    - 管理员可以看到所有项目
    - 普通用户只能看到自己参与的项目
    """
    if current_user.role == UserRole.ADMIN:
        # 管理员看所有项目
        result = await db.execute(
            select(Project).where(Project.is_active == True).order_by(Project.created_at.desc())
        )
    else:
        # 普通用户看自己参与的项目
        result = await db.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == current_user.id)
            .where(Project.is_active == True)
            .order_by(Project.created_at.desc())
        )
    
    projects = result.scalars().all()
    return [p.to_dict() for p in projects]


@router.get("/{project_id}", summary="获取项目详情")
async def get_project(
    project_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目详情"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN:
        member_result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权访问此项目")
    
    return project.to_dict()


@router.post("", summary="创建项目（管理员）")
async def create_project(
    request: ProjectCreate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建项目（仅管理员）"""
    # 自动生成项目代码
    code = generate_project_code(request.name)
    
    project = Project(
        name=request.name,
        code=code,
        description=request.description,
        icon=request.icon or "📁",
        color=request.color or "#184BFA",
        created_by=current_admin.id
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # 创建者自动成为项目 owner
    member = ProjectMember(
        project_id=project.id,
        user_id=current_admin.id,
        role="owner"
    )
    db.add(member)
    await db.commit()
    
    return project.to_dict()


@router.put("/{project_id}", summary="更新项目（管理员）")
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新项目（仅管理员）"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 更新字段
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description
    if request.icon is not None:
        project.icon = request.icon
    if request.color is not None:
        project.color = request.color
    if request.is_active is not None:
        project.is_active = request.is_active
    
    await db.commit()
    await db.refresh(project)
    
    return project.to_dict()


@router.delete("/{project_id}", summary="删除项目（管理员）")
async def delete_project(
    project_id: str,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除项目（仅管理员）- 软删除"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project.is_active = False
    await db.commit()
    
    return {"message": "项目已删除"}


# ==================== 项目成员管理 ====================

@router.get("/{project_id}/members", summary="获取项目成员")
async def list_project_members(
    project_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目成员列表"""
    from ..models.user import User
    
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
    )
    
    members = []
    for member, user in result.all():
        members.append({
            **member.to_dict(),
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email
            }
        })
    
    return members


class AddMemberRequest(BaseModel):
    """添加成员请求"""
    user_id: str = Field(..., description="用户ID")
    role: str = Field("member", description="角色: owner/admin/member")


@router.post("/{project_id}/members", summary="添加项目成员（管理员）")
async def add_project_member(
    project_id: str,
    request: AddMemberRequest,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """添加项目成员（仅管理员）"""
    # 检查是否已是成员
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == request.user_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户已是项目成员")
    
    member = ProjectMember(
        project_id=project_id,
        user_id=request.user_id,
        role=request.role
    )
    db.add(member)
    await db.commit()
    
    return {"message": "成员添加成功"}


@router.delete("/{project_id}/members/{user_id}", summary="移除项目成员（管理员）")
async def remove_project_member(
    project_id: str,
    user_id: str,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """移除项目成员（仅管理员）"""
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    
    await db.delete(member)
    await db.commit()
    
    return {"message": "成员已移除"}


class MemberRoleUpdate(BaseModel):
    """更新成员角色"""
    role: str = Field(..., description="角色: owner/admin/member")


@router.put("/{project_id}/members/{user_id}", summary="更新成员角色（管理员）")
async def update_member_role(
    project_id: str,
    user_id: str,
    request: MemberRoleUpdate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新成员角色（仅管理员）"""
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    
    member.role = request.role
    await db.commit()
    
    return {"message": "角色已更新"}


@router.get("/{project_id}/available-users", summary="获取可添加的用户列表")
async def get_available_users(
    project_id: str,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取不在项目中的用户列表（用于添加成员）"""
    # 获取项目已有成员
    member_result = await db.execute(
        select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)
    )
    existing_user_ids = [row[0] for row in member_result.all()]
    
    # 获取不在项目中的用户
    query = select(User).where(User.is_active == True)
    if existing_user_ids:
        query = query.where(~User.id.in_(existing_user_ids))
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "email": u.email,
            "role": u.role.value
        }
        for u in users
    ]
