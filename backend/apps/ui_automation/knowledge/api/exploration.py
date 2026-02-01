"""
知识图谱探索 API

提供以下功能：
- 开始/结束探索会话
- 记录页面跳转
- 查询知识图谱
- 路径规划
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from loguru import logger

from ...database import get_db
from ..services.exploration_service import ExplorationService, ExplorationMode


router = APIRouter(prefix="/exploration", tags=["知识图谱探索"])


# ==================== 请求/响应模型 ====================

class StartExplorationRequest(BaseModel):
    """开始探索请求"""
    app_id: str = Field(..., description="应用 ID")
    device_udid: str = Field(..., description="设备 UDID")
    mode: str = Field("manual", description="探索模式: manual|semi_auto|full_auto")
    current_page_id: Optional[str] = Field(None, description="当前页面 ID")


class StartExplorationResponse(BaseModel):
    """开始探索响应"""
    success: bool
    session_id: str
    message: str


class RecordTransitionRequest(BaseModel):
    """记录跳转请求"""
    session_id: str = Field(..., description="探索会话 ID")
    trigger_element: dict = Field(..., description="触发跳转的元素信息")
    action_type: str = Field("click", description="操作类型: click|swipe|input")
    to_page_screenshot: str = Field(..., description="目标页面截图 (base64)")
    model_id: Optional[str] = Field(None, description="分析使用的模型 ID")


class RecordTransitionResponse(BaseModel):
    """记录跳转响应"""
    success: bool
    is_new_page: bool = False
    transition_id: Optional[str] = None
    to_page: Optional[dict] = None
    session_stats: Optional[dict] = None
    error: Optional[str] = None


class EndExplorationRequest(BaseModel):
    """结束探索请求"""
    session_id: str = Field(..., description="探索会话 ID")


class FindPathRequest(BaseModel):
    """查找路径请求"""
    app_id: str = Field(..., description="应用 ID")
    from_page: str = Field(..., description="起始页面名称")
    to_page: str = Field(..., description="目标页面名称")


class UpdateCurrentPageRequest(BaseModel):
    """更新当前页面请求"""
    session_id: str = Field(..., description="探索会话 ID")
    page_id: str = Field(..., description="当前页面 ID")


# ==================== API 端点 ====================

@router.post("/start", response_model=StartExplorationResponse)
async def start_exploration(
    request: StartExplorationRequest,
    db: Session = Depends(get_db)
):
    """
    开始探索会话
    
    在开始探索前调用，返回会话 ID 用于后续记录跳转
    """
    try:
        mode = ExplorationMode(request.mode)
    except ValueError:
        mode = ExplorationMode.MANUAL
    
    service = ExplorationService(db)
    session = service.start_exploration(
        app_id=request.app_id,
        device_udid=request.device_udid,
        mode=mode,
        current_page_id=request.current_page_id
    )
    
    return StartExplorationResponse(
        success=True,
        session_id=session.session_id,
        message=f"探索会话已开始，模式: {mode.value}"
    )


@router.post("/end")
async def end_exploration(
    request: EndExplorationRequest,
    db: Session = Depends(get_db)
):
    """
    结束探索会话
    
    返回本次探索的统计信息
    """
    service = ExplorationService(db)
    stats = service.end_exploration(request.session_id)
    
    return {
        "success": "error" not in stats,
        **stats
    }


@router.post("/record-transition", response_model=RecordTransitionResponse)
async def record_transition(
    request: RecordTransitionRequest,
    db: Session = Depends(get_db)
):
    """
    记录页面跳转
    
    当用户点击元素导致页面跳转时调用：
    1. 分析目标页面
    2. 判断是否是新页面
    3. 创建跳转记录
    4. 更新元素的导航信息
    """
    service = ExplorationService(db)
    
    result = await service.record_transition(
        session_id=request.session_id,
        trigger_element=request.trigger_element,
        action_type=request.action_type,
        to_page_screenshot=request.to_page_screenshot,
        model_id=request.model_id
    )
    
    return RecordTransitionResponse(**result)


@router.post("/update-current-page")
async def update_current_page(
    request: UpdateCurrentPageRequest,
    db: Session = Depends(get_db)
):
    """
    更新探索会话的当前页面
    
    当用户通过 AI 分析获得页面 ID 后，更新会话的当前页面
    """
    service = ExplorationService(db)
    session = service.get_session(request.session_id)
    
    if not session:
        # 会话可能因服务重启丢失，返回警告而非错误
        logger.warning(f"探索会话不存在: {request.session_id}，可能已过期")
        return {
            "success": False,
            "message": "探索会话已过期，请重新开始探索",
            "session_id": request.session_id
        }
    
    session.current_page_id = request.page_id
    
    return {
        "success": True,
        "session_id": request.session_id,
        "current_page_id": request.page_id
    }


@router.get("/graph/{app_id}")
async def get_app_graph(
    app_id: str,
    db: Session = Depends(get_db)
):
    """
    获取 App 的知识图谱
    
    返回所有页面节点和跳转边
    """
    service = ExplorationService(db)
    graph = service.get_app_graph(app_id)
    
    return {
        "success": True,
        "data": graph
    }


@router.post("/find-path")
async def find_path(
    request: FindPathRequest,
    db: Session = Depends(get_db)
):
    """
    查找从 A 页面到 B 页面的操作路径
    
    使用 BFS 算法在知识图谱中搜索最短路径
    """
    service = ExplorationService(db)
    path = service.find_path(
        app_id=request.app_id,
        from_page_name=request.from_page,
        to_page_name=request.to_page
    )
    
    if path is None:
        return {
            "success": False,
            "error": f"未找到从「{request.from_page}」到「{request.to_page}」的路径",
            "path": None
        }
    
    return {
        "success": True,
        "path": path,
        "total_steps": len(path) - 1  # 不算最后一个页面
    }


@router.get("/page/{page_id}/transitions")
async def get_page_transitions(
    page_id: str,
    db: Session = Depends(get_db)
):
    """
    获取页面的所有跳转关系
    
    包括出向跳转（从该页面出发）和入向跳转（跳转到该页面）
    """
    service = ExplorationService(db)
    transitions = service.get_page_transitions(page_id)
    
    return {
        "success": True,
        "data": transitions
    }


@router.get("/sessions")
async def list_active_sessions(db: Session = Depends(get_db)):
    """
    列出所有活跃的探索会话
    """
    sessions = ExplorationService._active_sessions
    
    return {
        "success": True,
        "sessions": [
            {
                "session_id": s.session_id,
                "app_id": s.app_id,
                "device_udid": s.device_udid,
                "mode": s.mode.value,
                "current_page_id": s.current_page_id,
                "started_at": s.started_at.isoformat(),
                "transitions_count": s.transitions_count,
                "pages_discovered": s.pages_discovered
            }
            for s in sessions.values()
        ]
    }
