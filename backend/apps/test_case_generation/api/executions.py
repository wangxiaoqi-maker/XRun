"""功能用例手工执行 API"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.ui_automation.database import get_db
from apps.ui_automation.api.auth import get_current_user
from ..models import TcgTestExecution, TcgTestCase
from ..schemas import (
    ApiResponse, ExecutionCreate, StepResultUpdate,
    ExecutionComplete, ExecutionOut,
)

router = APIRouter(tags=["TCG-用例执行"])


@router.post("/executions")
async def create_execution(
    request: ExecutionCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建执行记录并初始化步骤"""
    result = await db.execute(
        select(TcgTestCase).where(TcgTestCase.id == request.case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        return ApiResponse(success=False, message="用例不存在")

    steps = case.test_steps or []
    step_results = [
        {"step": s.get("step", i + 1), "status": "pending", "actual_result": "", "remark": ""}
        for i, s in enumerate(steps)
    ]

    execution = TcgTestExecution(
        project_id=request.project_id,
        case_id=request.case_id,
        case_name=case.name,
        executor=current_user.username if hasattr(current_user, "username") else "unknown",
        status="in_progress",
        step_results=step_results,
        total_steps=len(steps),
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return ApiResponse(data=ExecutionOut.model_validate(execution))


@router.put("/executions/{execution_id}/steps/{step_num}")
async def update_step_result(
    execution_id: str,
    step_num: int,
    request: StepResultUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新某一步骤的执行结果"""
    result = await db.execute(
        select(TcgTestExecution).where(TcgTestExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    if not execution:
        return ApiResponse(success=False, message="执行记录不存在")

    steps = list(execution.step_results or [])
    target = next((s for s in steps if s.get("step") == step_num), None)
    if not target:
        return ApiResponse(success=False, message=f"步骤 {step_num} 不存在")

    target["status"] = request.status
    if request.actual_result is not None:
        target["actual_result"] = request.actual_result
    if request.remark is not None:
        target["remark"] = request.remark

    execution.step_results = steps
    _recalculate_stats(execution)
    await db.commit()
    await db.refresh(execution)
    return ApiResponse(data=ExecutionOut.model_validate(execution))


@router.put("/executions/{execution_id}/complete")
async def complete_execution(
    execution_id: str,
    request: ExecutionComplete,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """完成执行"""
    result = await db.execute(
        select(TcgTestExecution).where(TcgTestExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    if not execution:
        return ApiResponse(success=False, message="执行记录不存在")

    _recalculate_stats(execution)
    execution.status = "passed" if execution.failed_steps == 0 and execution.blocked_steps == 0 else "failed"
    execution.finished_at = datetime.now()
    if request.remark:
        execution.remark = request.remark

    await db.commit()
    await db.refresh(execution)
    return ApiResponse(data=ExecutionOut.model_validate(execution))


@router.get("/executions")
async def list_executions(
    case_id: Optional[str] = None,
    project_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取执行记录列表"""
    query = select(TcgTestExecution)
    count_query = select(func.count()).select_from(TcgTestExecution)

    if case_id:
        query = query.where(TcgTestExecution.case_id == case_id)
        count_query = count_query.where(TcgTestExecution.case_id == case_id)
    if project_id:
        query = query.where(TcgTestExecution.project_id == project_id)
        count_query = count_query.where(TcgTestExecution.project_id == project_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(TcgTestExecution.started_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    return ApiResponse(data={
        "items": [ExecutionOut.model_validate(r) for r in rows],
        "total": total,
    })


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取执行详情"""
    result = await db.execute(
        select(TcgTestExecution).where(TcgTestExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    if not execution:
        return ApiResponse(success=False, message="执行记录不存在")
    return ApiResponse(data=ExecutionOut.model_validate(execution))


def _recalculate_stats(execution: TcgTestExecution):
    """重新计算步骤统计"""
    steps = execution.step_results or []
    execution.passed_steps = sum(1 for s in steps if s.get("status") == "passed")
    execution.failed_steps = sum(1 for s in steps if s.get("status") == "failed")
    execution.blocked_steps = sum(1 for s in steps if s.get("status") == "blocked")
