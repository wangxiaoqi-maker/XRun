"""
页面分析 API 路由

提供 AI 教学模式的核心 API：
- POST /analyze-page: 分析页面截图
- POST /search-elements: 语义搜索元素
- GET /pages: 获取页面列表
- GET /apps: 获取应用列表
- GET /stats: 获取统计信息
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from apps.ui_automation.database import get_db
from ..services import KnowledgeService
from ..schemas import (
    PageAnalyzeRequest,
    PageAnalyzeResponse,
    ElementSearchRequest,
    ElementSearchResponse,
    ElementInfo,
    PageSummary,
    AppSummary,
    KnowledgeBaseStats,
)
from ..schemas.page_analysis import DeleteResponse

router = APIRouter()


def get_knowledge_service(session: AsyncSession = Depends(get_db)) -> KnowledgeService:
    """获取知识库服务实例"""
    return KnowledgeService(session)


# ==================== 页面分析 ====================

@router.post(
    "/analyze-page",
    summary="分析页面截图",
    description="分析 App 截图，提取可测试元素（不保存，需用户确认后手动保存）"
)
async def analyze_page(
    request: PageAnalyzeRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    分析页面截图（不保存数据库，需用户确认后手动保存）
    
    - 调用视觉大模型分析截图
    - 提取可交互元素
    - 返回分析结果供用户确认
    - 用户确认后调用 /save-to-knowledge-base 保存
    """
    try:
        result = await service.analyze_page(
            image_data=request.image_data,
            app_name=request.app_name,
            platform=request.platform,
            package_name=request.package_name,
            device_udid=request.device_udid,
            device_resolution=request.device_resolution,
            context_hint=request.context_hint,
            skip_duplicate=request.skip_duplicate,
            provider_id=request.provider_id,
            model_id=request.model_id,
            app_id=request.app_id
        )
        
        # 直接返回完整结果（包含 _meta，用于后续保存）
        return result
    except Exception as e:
        logger.error(f"页面分析失败: {e}")
        # 提取友好的错误信息
        error_msg = str(e)
        if "Model access denied" in error_msg or "AccessDenied" in error_msg:
            error_msg = "模型访问被拒绝，请检查 API Key 权限或更换模型"
        elif "API key" in error_msg.lower() or "api_key" in error_msg.lower():
            error_msg = "API Key 无效或未配置"
        elif "timeout" in error_msg.lower():
            error_msg = "模型请求超时，请稍后重试"
        elif "rate limit" in error_msg.lower():
            error_msg = "请求频率超限，请稍后重试"
        elif "cannot identify image" in error_msg.lower():
            error_msg = "图片格式无法识别，请重新截图"
        else:
            # 截取前100个字符
            error_msg = error_msg[:100] if len(error_msg) > 100 else error_msg
        raise HTTPException(status_code=500, detail=f"页面分析失败: {error_msg}")


# ==================== 语义搜索 ====================

@router.post(
    "/search-elements",
    response_model=ElementSearchResponse,
    summary="语义搜索元素",
    description="使用自然语言搜索知识库中的元素"
)
async def search_elements(
    request: ElementSearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
) -> ElementSearchResponse:
    """
    语义搜索元素
    
    - 将查询文本转换为向量
    - 在向量数据库中进行相似度搜索
    - 支持按 App、页面、元素类型过滤
    """
    try:
        result = await service.search_elements(
            query=request.query,
            app_name=request.app_name,
            page_name=request.page_name,
            page_type=request.page_type,
            element_type=request.element_type,
            platform=request.platform,
            testable_only=request.testable_only,
            top_k=request.top_k
        )
        
        return ElementSearchResponse(
            query=result["query"],
            results=result["results"],
            total_results=result["total_results"],
            search_time=result["search_time"],
            filters=result["filters"]
        )
    except Exception as e:
        logger.error(f"语义搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"语义搜索失败: {str(e)}")


# ==================== 知识库查询 ====================

@router.get(
    "/apps",
    response_model=List[AppSummary],
    summary="获取应用列表",
    description="获取知识库中的所有应用"
)
async def get_apps(
    platform: Optional[str] = Query(None, description="平台过滤（android/ios）"),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(100, ge=1, le=500, description="数量限制"),
    service: KnowledgeService = Depends(get_knowledge_service)
) -> List[AppSummary]:
    """获取应用列表"""
    try:
        apps = await service.get_apps(platform=platform, offset=offset, limit=limit)
        return [AppSummary(**app) for app in apps]
    except Exception as e:
        logger.error(f"获取应用列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取应用列表失败: {str(e)}")


@router.get(
    "/pages",
    response_model=List[PageSummary],
    summary="获取页面列表",
    description="获取知识库中的页面列表"
)
async def get_pages(
    app_name: Optional[str] = Query(None, description="应用名称过滤"),
    platform: Optional[str] = Query(None, description="平台过滤"),
    page_type: Optional[str] = Query(None, description="页面类型过滤"),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=500, description="数量限制"),
    include_failed: bool = Query(False, description="是否包含解析失败的页面"),
    deduplicate: bool = Query(True, description="是否去重（同名页面只保留最新的）"),
    service: KnowledgeService = Depends(get_knowledge_service)
) -> List[PageSummary]:
    """获取页面列表"""
    try:
        pages = await service.get_pages(
            app_name=app_name,
            platform=platform,
            page_type=page_type,
            offset=offset,
            limit=limit,
            include_failed=include_failed,
            deduplicate=deduplicate
        )
        return [PageSummary(**page) for page in pages]
    except Exception as e:
        logger.error(f"获取页面列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取页面列表失败: {str(e)}")


@router.get(
    "/pages/{page_id}/elements",
    response_model=List[ElementInfo],
    summary="获取页面元素",
    description="获取指定页面的所有元素"
)
async def get_page_elements(
    page_id: str,
    element_type: Optional[str] = Query(None, description="元素类型过滤"),
    testable_only: bool = Query(True, description="只返回可测试元素"),
    service: KnowledgeService = Depends(get_knowledge_service)
) -> List[ElementInfo]:
    """获取页面元素"""
    try:
        elements = await service.get_page_elements(
            page_id=page_id,
            element_type=element_type,
            testable_only=testable_only
        )
        return [ElementInfo(**e) for e in elements]
    except Exception as e:
        logger.error(f"获取页面元素失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取页面元素失败: {str(e)}")


@router.get(
    "/stats",
    response_model=KnowledgeBaseStats,
    summary="获取统计信息",
    description="获取知识库的统计信息"
)
async def get_stats(
    service: KnowledgeService = Depends(get_knowledge_service)
) -> KnowledgeBaseStats:
    """获取知识库统计信息"""
    try:
        stats = await service.get_stats()
        return KnowledgeBaseStats(**stats)
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# ==================== 保存到知识库 ====================

class SaveToKnowledgeRequest(BaseModel):
    """保存到知识库请求"""
    analysis_result: dict = Field(..., description="AI 分析返回的完整结果（包含 _meta）")
    save_to_vector: bool = Field(True, description="是否同时保存到向量库")


class SaveToKnowledgeResponse(BaseModel):
    """保存到知识库响应"""
    success: bool
    message: str
    page_id: Optional[str] = None
    elements_count: int = 0


@router.post(
    "/save-to-knowledge-base",
    response_model=SaveToKnowledgeResponse,
    summary="保存到知识库",
    description="将 AI 分析结果保存到数据库和向量库"
)
async def save_to_knowledge_base(
    request: SaveToKnowledgeRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
) -> SaveToKnowledgeResponse:
    """
    保存分析结果到知识库
    
    用户确认 AI 分析正确后手动触发：
    1. 保存到关系型数据库（MySQL）
    2. 保存到向量数据库（Milvus）用于语义搜索
    """
    try:
        result = await service.save_analysis_to_knowledge_base(
            analysis_result=request.analysis_result,
            save_to_vector=request.save_to_vector
        )
        return SaveToKnowledgeResponse(
            success=True,
            message=f"成功保存 {result['elements_count']} 个元素到知识库",
            page_id=result["page_id"],
            elements_count=result["elements_count"]
        )
    except ValueError as e:
        return SaveToKnowledgeResponse(
            success=False,
            message=str(e),
            elements_count=0
        )
    except Exception as e:
        logger.error(f"保存到知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存到知识库失败: {str(e)}")


# ==================== 更新操作 ====================

class UpdatePageRequest(BaseModel):
    """更新页面请求"""
    page_name: Optional[str] = Field(None, description="页面名称")
    page_description: Optional[str] = Field(None, description="页面描述")
    page_type: Optional[str] = Field(None, description="页面类型")
    module_id: Optional[str] = Field(None, description="所属模块 ID")
    is_common: Optional[bool] = Field(None, description="是否为公共组件")


@router.put(
    "/pages/{page_id}",
    summary="更新页面信息",
    description="更新页面的名称、描述、类型等信息"
)
async def update_page(
    page_id: str,
    request: UpdatePageRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    """更新页面信息"""
    try:
        update_data = {}
        if request.page_name is not None:
            update_data["page_name"] = request.page_name
        if request.page_description is not None:
            update_data["page_description"] = request.page_description
        if request.page_type is not None:
            update_data["page_type"] = request.page_type
        if request.module_id is not None:
            # 空字符串表示取消关联
            update_data["module_id"] = request.module_id if request.module_id else None
        if request.is_common is not None:
            update_data["is_common"] = request.is_common
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有要更新的字段")
        
        success = await service.update_page(page_id, update_data)
        if success:
            return {"success": True, "message": "更新成功"}
        else:
            raise HTTPException(status_code=404, detail="页面不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新页面失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新页面失败: {str(e)}")


# ==================== 删除操作 ====================

@router.delete(
    "/pages/{page_id}",
    response_model=DeleteResponse,
    summary="删除页面",
    description="删除页面及其所有元素"
)
async def delete_page(
    page_id: str,
    service: KnowledgeService = Depends(get_knowledge_service)
) -> DeleteResponse:
    """删除页面"""
    try:
        success = await service.delete_page(page_id)
        if success:
            return DeleteResponse(success=True, message="页面删除成功")
        else:
            raise HTTPException(status_code=404, detail="页面不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除页面失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除页面失败: {str(e)}")


@router.delete(
    "/apps/{app_id}",
    response_model=DeleteResponse,
    summary="删除应用",
    description="删除应用及其所有页面和元素"
)
async def delete_app(
    app_id: str,
    service: KnowledgeService = Depends(get_knowledge_service)
) -> DeleteResponse:
    """删除应用"""
    try:
        success = await service.delete_app(app_id)
        if success:
            return DeleteResponse(success=True, message="应用删除成功")
        else:
            raise HTTPException(status_code=404, detail="应用不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除应用失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除应用失败: {str(e)}")


# ==================== 元素操作 ====================

class ElementUpdateRequest(BaseModel):
    """元素更新请求"""
    element_name: Optional[str] = Field(None, description="元素名称")
    element_type: Optional[str] = Field(None, description="元素类型")
    text_content: Optional[str] = Field(None, description="文字内容")
    description: Optional[str] = Field(None, description="元素描述")
    midscene_locator: Optional[str] = Field(None, description="Midscene 定位描述")
    # 导航信息
    is_navigation: Optional[bool] = Field(None, description="是否是导航元素")
    target_page_name: Optional[str] = Field(None, description="跳转目标页面名称")


@router.put(
    "/elements/{element_id}",
    summary="更新元素信息",
    description="更新元素的名称、类型、描述等信息"
)
async def update_element(
    element_id: str,
    request: ElementUpdateRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    """更新元素信息"""
    try:
        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="没有需要更新的字段")
        
        success = await service.update_element(element_id, update_data)
        if success:
            return {"success": True, "message": "更新成功"}
        else:
            raise HTTPException(status_code=404, detail="元素不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新元素失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新元素失败: {str(e)}")


@router.delete(
    "/elements/{element_id}",
    response_model=DeleteResponse,
    summary="删除元素",
    description="删除单个元素"
)
async def delete_element(
    element_id: str,
    service: KnowledgeService = Depends(get_knowledge_service)
) -> DeleteResponse:
    """删除元素"""
    try:
        success = await service.delete_element(element_id)
        if success:
            return DeleteResponse(success=True, message="元素删除成功")
        else:
            raise HTTPException(status_code=404, detail="元素不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除元素失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除元素失败: {str(e)}")


# ==================== 知识图谱 / 跳转关系 ====================

@router.get(
    "/apps/{app_id}/graph",
    summary="获取应用知识图谱",
    description="获取应用的页面跳转关系图谱，包含节点（页面）和边（跳转关系）"
)
async def get_app_graph(
    app_id: str,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    获取应用知识图谱
    
    返回：
    - nodes: 页面列表（id, name, type, depth, elements_count）
    - edges: 跳转关系列表（from, to, trigger, locator）
    - stats: 统计信息
    """
    try:
        result = await service.get_page_transitions(app_id)
        return result
    except Exception as e:
        logger.error(f"获取知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识图谱失败: {str(e)}")


class FindPathRequest(BaseModel):
    """查找导航路径请求"""
    from_page: str = Field(..., description="起始页面名称（支持模糊匹配）")
    to_page: str = Field(..., description="目标页面名称（支持模糊匹配）")


@router.post(
    "/apps/{app_id}/find-path",
    summary="查找导航路径",
    description="查找从页面 A 到页面 B 的操作路径，用于自动生成用例的前置步骤"
)
async def find_navigation_path(
    app_id: str,
    request: FindPathRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    查找导航路径（BFS 最短路径）
    
    返回操作步骤列表，每步包含：
    - page: 当前页面名称
    - action: 要执行的操作（如 "点击「转账」"）
    - locator: Midscene 定位器
    """
    try:
        path = await service.find_navigation_path(
            app_id=app_id,
            from_page_name=request.from_page,
            to_page_name=request.to_page
        )
        
        if path is None:
            return {
                "found": False,
                "message": f"未找到从「{request.from_page}」到「{request.to_page}」的路径",
                "path": []
            }
        
        return {
            "found": True,
            "path": path,
            "steps_count": len(path)
        }
    except Exception as e:
        logger.error(f"查找导航路径失败: {e}")
        raise HTTPException(status_code=500, detail=f"查找导航路径失败: {str(e)}")


@router.post("/apps/{app_id}/infer-transitions")
async def infer_transitions(
    app_id: str,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    批量推断应用的跳转边
    
    遍历所有页面的导航元素（is_navigation=True），
    根据 target_page_name 自动创建 PageTransition 记录。
    
    用于：
    1. 补全历史数据（已分析但未建立跳转关系的页面）
    2. 新页面分析后重新计算跳转关系
    
    Returns:
        - pages_processed: 处理的页面数
        - transitions_created: 创建的跳转边数
        - pending_targets: 未找到目标页面的元素列表
    """
    try:
        result = await service.infer_all_transitions(app_id)
        return {
            "success": True,
            "app_id": app_id,
            **result
        }
    except Exception as e:
        logger.error(f"批量推断跳转边失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量推断跳转边失败: {str(e)}")
