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
    response_model=PageAnalyzeResponse,
    summary="分析页面截图",
    description="分析 App 截图，提取可测试元素并存入知识库"
)
async def analyze_page(
    request: PageAnalyzeRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
) -> PageAnalyzeResponse:
    """
    分析页面截图
    
    - 调用视觉大模型分析截图
    - 提取可交互元素
    - 存入关系型数据库和向量数据库
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
            model_id=request.model_id
        )
        
        # 转换元素为 ElementInfo
        elements = [ElementInfo(**e) for e in result.get("elements", [])]
        
        return PageAnalyzeResponse(
            page_id=result["page_id"],
            page_name=result["page_name"],
            page_type=result["page_type"],
            page_description=result.get("page_description"),
            elements=elements,
            elements_count=result["elements_count"],
            confidence_score=result.get("confidence_score", 0.0),
            is_new_page=result.get("is_new_page", True),
            is_cached=result.get("is_cached", False),
            processing_time=result.get("processing_time", 0.0)
        )
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
    limit: int = Query(50, ge=1, le=200, description="数量限制"),
    service: KnowledgeService = Depends(get_knowledge_service)
) -> List[PageSummary]:
    """获取页面列表"""
    try:
        pages = await service.get_pages(
            app_name=app_name,
            platform=platform,
            page_type=page_type,
            offset=offset,
            limit=limit
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
