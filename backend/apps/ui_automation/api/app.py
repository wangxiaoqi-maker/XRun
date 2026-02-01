"""
应用管理 API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.app import App, AppPlatform
from .auth import get_current_user

router = APIRouter(prefix="/apps", tags=["应用管理"])


# ==================== 请求/响应模型 ====================

class AppCreate(BaseModel):
    """创建应用"""
    name: str = Field(..., min_length=1, max_length=100, description="应用名称")
    name_en: Optional[str] = Field(None, max_length=100, description="英文名称")
    package_name: str = Field(..., min_length=1, max_length=200, description="包名/Bundle ID")
    platform: str = Field(..., description="平台: android/ios")
    icon_url: Optional[str] = Field(None, description="应用图标URL")
    latest_version: Optional[str] = Field(None, description="最新版本")
    launch_activity: Optional[str] = Field(None, description="启动Activity")
    project_id: Optional[str] = Field(None, description="所属项目ID")
    description: Optional[str] = Field(None, description="应用描述")


class AppUpdate(BaseModel):
    """更新应用"""
    name: Optional[str] = Field(None, max_length=100, description="应用名称")
    name_en: Optional[str] = Field(None, max_length=100, description="英文名称")
    icon_url: Optional[str] = Field(None, description="应用图标URL")
    latest_version: Optional[str] = Field(None, description="最新版本")
    launch_activity: Optional[str] = Field(None, description="启动Activity")
    description: Optional[str] = Field(None, description="应用描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


# ==================== API 端点 ====================

@router.get("", summary="获取应用列表")
async def list_apps(
    platform: Optional[str] = Query(None, description="平台筛选: android/ios"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    project_id: Optional[str] = Query(None, description="项目ID"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取应用列表"""
    query = select(App).where(App.is_active == True)
    
    # 平台筛选
    if platform:
        try:
            platform_enum = AppPlatform(platform.lower())
            query = query.where(App.platform == platform_enum)
        except ValueError:
            pass
    
    # 关键词搜索
    if keyword:
        query = query.where(
            or_(
                App.name.ilike(f"%{keyword}%"),
                App.name_en.ilike(f"%{keyword}%"),
                App.package_name.ilike(f"%{keyword}%")
            )
        )
    
    # 项目筛选
    if project_id:
        query = query.where(App.project_id == project_id)
    
    query = query.order_by(App.updated_at.desc())
    
    result = await db.execute(query)
    apps = result.scalars().all()
    
    # 查询每个应用关联的统计数据
    app_list = []
    for app in apps:
        app_dict = app.to_dict()
        
        # 查询知识库中关联的页面和元素数量
        try:
            from sqlalchemy import text
            # 通过应用名称或包名查找知识库中的 AppInfo
            stats_query = text('''
                SELECT 
                    (SELECT COUNT(*) FROM kb_page_analysis pa 
                     JOIN kb_app_info ai ON pa.app_id = ai.id 
                     WHERE ai.app_name = :app_name OR ai.package_name = :package_name) as page_count,
                    (SELECT COUNT(*) FROM kb_page_element pe 
                     JOIN kb_page_analysis pa ON pe.page_id = pa.id
                     JOIN kb_app_info ai ON pa.app_id = ai.id 
                     WHERE ai.app_name = :app_name OR ai.package_name = :package_name) as element_count
            ''')
            stats_result = await db.execute(stats_query, {
                'app_name': app.name,
                'package_name': app.package_name
            })
            stats = stats_result.fetchone()
            if stats:
                app_dict['ui_element_count'] = stats[1] or 0
                app_dict['page_count'] = stats[0] or 0
        except Exception as e:
            # 查询失败时使用默认值
            app_dict['ui_element_count'] = 0
            app_dict['page_count'] = 0
        
        app_list.append(app_dict)
    
    return app_list


@router.get("/{app_id}", summary="获取应用详情")
async def get_app(
    app_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取应用详情"""
    result = await db.execute(select(App).where(App.id == app_id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    return app.to_dict()


@router.post("", summary="创建应用")
async def create_app(
    request: AppCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建应用"""
    # 检查包名是否已存在
    result = await db.execute(select(App).where(App.package_name == request.package_name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="包名已存在")
    
    try:
        platform_enum = AppPlatform(request.platform.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的平台类型")
    
    app = App(
        name=request.name,
        name_en=request.name_en,
        package_name=request.package_name,
        platform=platform_enum,
        icon_url=request.icon_url,
        latest_version=request.latest_version,
        launch_activity=request.launch_activity,
        project_id=request.project_id,
        description=request.description,
        created_by=current_user.id
    )
    
    db.add(app)
    await db.commit()
    await db.refresh(app)
    
    return app.to_dict()


@router.put("/{app_id}", summary="更新应用")
async def update_app(
    app_id: str,
    request: AppUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新应用"""
    result = await db.execute(select(App).where(App.id == app_id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 更新字段
    if request.name is not None:
        app.name = request.name
    if request.name_en is not None:
        app.name_en = request.name_en
    if request.icon_url is not None:
        app.icon_url = request.icon_url
    if request.latest_version is not None:
        app.latest_version = request.latest_version
    if request.launch_activity is not None:
        app.launch_activity = request.launch_activity
    if request.description is not None:
        app.description = request.description
    if request.is_active is not None:
        app.is_active = request.is_active
    
    await db.commit()
    await db.refresh(app)
    
    return app.to_dict()


@router.delete("/{app_id}", summary="删除应用")
async def delete_app(
    app_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除应用（软删除）"""
    result = await db.execute(select(App).where(App.id == app_id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    app.is_active = False
    await db.commit()
    
    return {"message": "应用已删除"}
