"""
页面模块管理 API

提供功能模块的 CRUD 操作：
- 创建/编辑/删除模块
- 获取模块树
- 将页面分配到模块
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from apps.ui_automation.database import get_db
from ..models import PageModule, PageAnalysis, AppInfo

router = APIRouter(prefix="/modules", tags=["功能模块管理"])


def module_to_dict(module: PageModule, pages_count: int = 0) -> dict:
    """安全地将模块转换为字典（避免访问关系）"""
    return {
        "id": module.id,
        "app_id": module.app_id,
        "parent_id": module.parent_id,
        "module_name": module.module_name,
        "module_code": module.module_code,
        "description": module.description,
        "icon": module.icon,
        "sort_order": module.sort_order,
        "depth": module.depth,
        "path": module.path,
        "pages_count": pages_count,
        "created_at": module.created_at.isoformat() if module.created_at else None,
        "updated_at": module.updated_at.isoformat() if module.updated_at else None,
    }


def page_to_dict(page: PageAnalysis, app_name: str = None, platform: str = None) -> dict:
    """安全地将页面转换为字典（避免访问关系）"""
    return {
        "id": page.id,
        "app_id": page.app_id,
        "app_name": app_name,
        "platform": platform,
        "module_id": page.module_id,
        "page_name": page.page_name,
        "page_type": page.page_type,
        "page_description": page.page_description,
        "is_common": page.is_common or False,
        "user_context": page.user_context,
        "navigation_source": page.navigation_source,
        "screenshot_hash": page.screenshot_hash,
        "screenshot_url": page.screenshot_url,
        "device_udid": page.device_udid,
        "device_resolution": page.device_resolution,
        "elements_count": page.elements_count,
        "confidence_score": float(page.confidence_score) if page.confidence_score else 0.0,
        "processing_time": float(page.processing_time) if page.processing_time else 0.0,
        "page_signature": page.page_signature,
        "depth": page.depth,
        "visit_count": page.visit_count,
        "version": page.visit_count or 1,
        "created_at": page.created_at.isoformat() if page.created_at else None,
        "updated_at": page.updated_at.isoformat() if page.updated_at else None,
    }


# ==================== 请求/响应模型 ====================

class ModuleCreateRequest(BaseModel):
    """创建模块请求"""
    app_id: str = Field(..., description="应用 ID")
    module_name: str = Field(..., description="模块名称")
    module_code: Optional[str] = Field(None, description="模块代码")
    parent_id: Optional[str] = Field(None, description="父模块 ID")
    description: Optional[str] = Field(None, description="模块描述")
    icon: Optional[str] = Field(None, description="模块图标")
    sort_order: int = Field(0, description="排序顺序")


class ModuleUpdateRequest(BaseModel):
    """更新模块请求"""
    module_name: Optional[str] = Field(None, description="模块名称")
    module_code: Optional[str] = Field(None, description="模块代码")
    parent_id: Optional[str] = Field(None, description="父模块 ID")
    description: Optional[str] = Field(None, description="模块描述")
    icon: Optional[str] = Field(None, description="模块图标")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class AssignPagesRequest(BaseModel):
    """分配页面到模块请求"""
    page_ids: List[str] = Field(..., description="页面 ID 列表")


# ==================== API 端点 ====================

@router.post("", summary="创建模块")
async def create_module(
    request: ModuleCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建功能模块
    
    支持层级结构，如：
    - 我的（一级）
      - 余额（二级）
        - 转账（三级）
        - 充值（三级）
    """
    try:
        # 计算层级深度和路径
        depth = 0
        path = ""
        
        if request.parent_id:
            parent_result = await db.execute(
                select(PageModule).where(PageModule.id == request.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
            if not parent:
                raise HTTPException(status_code=404, detail="父模块不存在")
            depth = (parent.depth or 0) + 1
            path = f"{parent.path or ''}"
        
        # 创建模块
        import uuid
        module_id = str(uuid.uuid4())
        
        module = PageModule(
            id=module_id,
            app_id=request.app_id,
            parent_id=request.parent_id,
            module_name=request.module_name,
            module_code=request.module_code or request.module_name.lower().replace(" ", "_"),
            description=request.description,
            icon=request.icon,
            sort_order=request.sort_order,
            depth=depth,
            path=f"{path}/{module_id}/"
        )
        
        db.add(module)
        await db.commit()
        
        logger.info(f"创建模块: {module.module_name} (depth={depth})")
        
        # 直接返回数据，避免 refresh 触发关系加载
        return {
            "success": True,
            "module": {
                "id": module_id,
                "app_id": request.app_id,
                "parent_id": request.parent_id,
                "module_name": request.module_name,
                "module_code": module.module_code,
                "description": request.description,
                "icon": request.icon,
                "sort_order": request.sort_order,
                "depth": depth,
                "path": module.path,
                "pages_count": 0,
                "created_at": module.created_at.isoformat() if module.created_at else None,
                "updated_at": module.updated_at.isoformat() if module.updated_at else None,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建模块失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建模块失败: {str(e)}")


@router.get("/tree/{app_id}", summary="获取模块树")
async def get_module_tree(
    app_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用的模块树结构
    
    返回完整的层级树，包含每个模块下的页面数量
    """
    try:
        # 获取所有模块
        result = await db.execute(
            select(PageModule)
            .where(PageModule.app_id == app_id)
            .order_by(PageModule.depth, PageModule.sort_order)
        )
        modules = result.scalars().all()
        
        # 获取每个模块的页面数量
        from sqlalchemy import func
        pages_count_result = await db.execute(
            select(PageAnalysis.module_id, func.count(PageAnalysis.id))
            .where(PageAnalysis.app_id == app_id)
            .where(PageAnalysis.module_id.isnot(None))
            .group_by(PageAnalysis.module_id)
        )
        pages_count_map = {row[0]: row[1] for row in pages_count_result.fetchall()}
        
        # 构建树结构（使用安全的转换函数）
        module_dict = {
            m.id: module_to_dict(m, pages_count_map.get(m.id, 0))
            for m in modules
        }
        tree = []
        
        for module in modules:
            module_data = module_dict[module.id]
            module_data["children"] = []
            
            if module.parent_id and module.parent_id in module_dict:
                # 添加到父模块的 children
                parent_data = module_dict[module.parent_id]
                if "children" not in parent_data:
                    parent_data["children"] = []
                parent_data["children"].append(module_data)
            else:
                # 顶级模块
                tree.append(module_data)
        
        return {
            "app_id": app_id,
            "modules": tree,
            "total_count": len(modules)
        }
        
    except Exception as e:
        logger.error(f"获取模块树失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模块树失败: {str(e)}")


@router.get("/{module_id}", summary="获取模块详情")
async def get_module(
    module_id: str,
    include_pages: bool = Query(False, description="是否包含页面列表"),
    db: AsyncSession = Depends(get_db)
):
    """获取模块详情及其下的页面"""
    try:
        result = await db.execute(
            select(PageModule).where(PageModule.id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        # 获取页面数量
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count(PageAnalysis.id))
            .where(PageAnalysis.module_id == module_id)
        )
        pages_count = count_result.scalar() or 0
        
        data = module_to_dict(module, pages_count)
        data["full_path"] = module.module_name  # 简化路径
        
        if include_pages:
            # 获取模块下的页面
            pages_result = await db.execute(
                select(PageAnalysis)
                .where(PageAnalysis.module_id == module_id)
                .order_by(PageAnalysis.created_at.desc())
            )
            pages = pages_result.scalars().all()
            data["pages"] = [page_to_dict(p) for p in pages]
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模块详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模块详情失败: {str(e)}")


@router.put("/{module_id}", summary="更新模块")
async def update_module(
    module_id: str,
    request: ModuleUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新模块信息"""
    try:
        result = await db.execute(
            select(PageModule).where(PageModule.id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        # 更新字段
        update_data = request.model_dump(exclude_none=True)
        for key, value in update_data.items():
            if hasattr(module, key):
                setattr(module, key, value)
        
        # 如果更改了父模块，需要重新计算深度和路径
        if "parent_id" in update_data:
            if request.parent_id:
                parent_result = await db.execute(
                    select(PageModule).where(PageModule.id == request.parent_id)
                )
                parent = parent_result.scalar_one_or_none()
                if parent:
                    module.depth = (parent.depth or 0) + 1
                    module.path = f"{parent.path or ''}/{module_id}/"
            else:
                module.depth = 0
                module.path = f"/{module_id}/"
        
        await db.commit()
        
        return {
            "success": True,
            "module": module_to_dict(module)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新模块失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新模块失败: {str(e)}")


@router.delete("/{module_id}", summary="删除模块")
async def delete_module(
    module_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除模块
    
    注意：会同时删除所有子模块，但不会删除页面（页面的 module_id 会被置为 NULL）
    """
    try:
        result = await db.execute(
            select(PageModule).where(PageModule.id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        await db.delete(module)
        await db.commit()
        
        return {"success": True, "message": "模块删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模块失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除模块失败: {str(e)}")


@router.post("/{module_id}/assign-pages", summary="分配页面到模块")
async def assign_pages_to_module(
    module_id: str,
    request: AssignPagesRequest,
    db: AsyncSession = Depends(get_db)
):
    """将页面分配到指定模块"""
    try:
        # 验证模块存在
        module_result = await db.execute(
            select(PageModule).where(PageModule.id == module_id)
        )
        module = module_result.scalar_one_or_none()
        if not module:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        # 批量更新页面的 module_id
        updated_count = 0
        for page_id in request.page_ids:
            page_result = await db.execute(
                select(PageAnalysis).where(PageAnalysis.id == page_id)
            )
            page = page_result.scalar_one_or_none()
            if page:
                page.module_id = module_id
                updated_count += 1
        
        await db.commit()
        
        logger.info(f"分配 {updated_count} 个页面到模块 {module.module_name}")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "module": module_to_dict(module, updated_count)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配页面失败: {e}")
        raise HTTPException(status_code=500, detail=f"分配页面失败: {str(e)}")


@router.post("/{module_id}/remove-pages", summary="从模块移除页面")
async def remove_pages_from_module(
    module_id: str,
    request: AssignPagesRequest,
    db: AsyncSession = Depends(get_db)
):
    """从模块移除页面（将 module_id 置为 NULL）"""
    try:
        updated_count = 0
        for page_id in request.page_ids:
            page_result = await db.execute(
                select(PageAnalysis)
                .where(PageAnalysis.id == page_id)
                .where(PageAnalysis.module_id == module_id)
            )
            page = page_result.scalar_one_or_none()
            if page:
                page.module_id = None
                updated_count += 1
        
        await db.commit()
        
        return {
            "success": True,
            "removed_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"移除页面失败: {e}")
        raise HTTPException(status_code=500, detail=f"移除页面失败: {str(e)}")


@router.get("/app/{app_id}/pages-by-module", summary="按模块分组获取页面")
async def get_pages_grouped_by_module(
    app_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用下所有页面，按模块分组
    
    返回结构：
    {
        "modules": [
            {
                "module": {...},
                "pages": [...]
            }
        ],
        "unassigned_pages": [...]  // 未分配模块的页面
    }
    """
    try:
        # 获取应用信息
        app_result = await db.execute(
            select(AppInfo).where(AppInfo.id == app_id)
        )
        app_info = app_result.scalar_one_or_none()
        app_name = app_info.app_name if app_info else None
        platform = app_info.platform if app_info else None
        
        # 获取所有模块
        modules_result = await db.execute(
            select(PageModule)
            .where(PageModule.app_id == app_id)
            .order_by(PageModule.depth, PageModule.sort_order)
        )
        modules = modules_result.scalars().all()
        
        # 获取所有页面
        pages_result = await db.execute(
            select(PageAnalysis)
            .where(PageAnalysis.app_id == app_id)
            .order_by(PageAnalysis.created_at.desc())
        )
        pages = pages_result.scalars().all()
        
        # 按模块分组
        module_pages = {m.id: [] for m in modules}
        unassigned_pages = []
        
        for page in pages:
            page_dict = page_to_dict(page, app_name=app_name, platform=platform)
            if page.module_id and page.module_id in module_pages:
                module_pages[page.module_id].append(page_dict)
            else:
                unassigned_pages.append(page_dict)
        
        # 构建结果
        result_modules = []
        for module in modules:
            pages_list = module_pages[module.id]
            result_modules.append({
                "module": module_to_dict(module, len(pages_list)),
                "pages": pages_list
            })
        
        return {
            "app_id": app_id,
            "app_name": app_name,
            "platform": platform,
            "modules": result_modules,
            "unassigned_pages": unassigned_pages,
            "total_pages": len(pages),
            "total_modules": len(modules)
        }
        
    except Exception as e:
        logger.error(f"获取分组页面失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分组页面失败: {str(e)}")
