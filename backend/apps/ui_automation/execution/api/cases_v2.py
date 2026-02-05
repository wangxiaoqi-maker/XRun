"""
用例管理 API V2

提供用例的 CRUD 操作和编译功能
"""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.ui_automation.database import get_db
from apps.ui_automation.execution.models import TestCaseV2, Platform, CaseStatus
from apps.ui_automation.execution.schemas.test_case import (
    TestCaseCreateRequest,
    TestCaseUpdateRequest,
    TestCaseResponse,
    TestCaseListResponse,
)
from apps.ui_automation.execution.compiler import TypeScriptCompiler

router = APIRouter(prefix="/cases", tags=["用例管理 V2"])


@router.get("", response_model=TestCaseListResponse)
async def list_cases(
    app_id: str | None = Query(None, description="应用 ID"),
    project_id: str | None = Query(None, description="项目 ID"),
    platform: Platform | None = Query(None, description="平台"),
    status: CaseStatus | None = Query(None, description="状态"),
    keyword: str | None = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> TestCaseListResponse:
    """获取用例列表"""
    # 构建查询
    query = select(TestCaseV2).where(TestCaseV2.is_latest == True)
    
    if app_id:
        query = query.where(TestCaseV2.app_id == app_id)
    if project_id:
        query = query.where(TestCaseV2.project_id == project_id)
    if platform:
        query = query.where(TestCaseV2.platform == platform)
    if status:
        query = query.where(TestCaseV2.status == status)
    if keyword:
        query = query.where(TestCaseV2.name.contains(keyword))
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.order_by(TestCaseV2.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    # 转换响应
    items = []
    for case in cases:
        items.append(TestCaseResponse(
            id=case.id,
            name=case.name,
            description=case.description,
            app_id=case.app_id,
            project_id=case.project_id,
            suite_id=case.suite_id,
            platform=case.platform.value if case.platform else "",
            steps_json=case.steps_json or [],
            input_variables=case.input_variables,
            refs=case.refs,
            config_override=case.config_override,
            data_set_id=case.data_set_id,
            launch_target=case.launch_target,
            tags=case.tags,
            priority=case.priority.value if case.priority else "medium",
            status=case.status.value if case.status else "draft",
            version=case.version or "1.0.0",
            step_count=case.get_step_count(),
            variable_names=case.get_variable_names(),
            created_at=case.created_at,
            updated_at=case.updated_at,
            created_by=case.created_by,
        ))
    
    return TestCaseListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    request: TestCaseCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TestCaseResponse:
    """创建用例"""
    case_id = str(uuid.uuid4())
    
    case = TestCaseV2(
        id=case_id,
        name=request.name,
        description=request.description,
        app_id=request.app_id,
        project_id=request.project_id,
        suite_id=request.suite_id,
        platform=request.platform,
        steps_json=[step.model_dump(by_alias=True, exclude_none=True) for step in request.steps_json],
        input_variables=[v.model_dump(by_alias=True, exclude_none=True) for v in request.input_variables] if request.input_variables else None,
        refs=[r.model_dump(by_alias=True, exclude_none=True) for r in request.refs] if request.refs else None,
        config_override=request.config_override,
        data_set_id=request.data_set_id,
        launch_target=request.launch_target,
        tags=request.tags,
        priority=request.priority,
        status=CaseStatus.DRAFT,
    )
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    return TestCaseResponse(
        id=case.id,
        name=case.name,
        description=case.description,
        app_id=case.app_id,
        project_id=case.project_id,
        suite_id=case.suite_id,
        platform=case.platform.value if case.platform else "",
        steps_json=case.steps_json or [],
        input_variables=case.input_variables,
        refs=case.refs,
        config_override=case.config_override,
        data_set_id=case.data_set_id,
        launch_target=case.launch_target,
        tags=case.tags,
        priority=case.priority.value if case.priority else "medium",
        status=case.status.value if case.status else "draft",
        version=case.version or "1.0.0",
        step_count=case.get_step_count(),
        variable_names=case.get_variable_names(),
        created_at=case.created_at,
        updated_at=case.updated_at,
        created_by=case.created_by,
    )


@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
) -> TestCaseResponse:
    """获取用例详情"""
    result = await db.execute(
        select(TestCaseV2).where(TestCaseV2.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {case_id} not found"
        )
    
    return TestCaseResponse(
        id=case.id,
        name=case.name,
        description=case.description,
        app_id=case.app_id,
        project_id=case.project_id,
        suite_id=case.suite_id,
        platform=case.platform.value if case.platform else "",
        steps_json=case.steps_json or [],
        input_variables=case.input_variables,
        refs=case.refs,
        config_override=case.config_override,
        data_set_id=case.data_set_id,
        launch_target=case.launch_target,
        tags=case.tags,
        priority=case.priority.value if case.priority else "medium",
        status=case.status.value if case.status else "draft",
        version=case.version or "1.0.0",
        step_count=case.get_step_count(),
        variable_names=case.get_variable_names(),
        created_at=case.created_at,
        updated_at=case.updated_at,
        created_by=case.created_by,
    )


@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_case(
    case_id: str,
    request: TestCaseUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TestCaseResponse:
    """更新用例"""
    result = await db.execute(
        select(TestCaseV2).where(TestCaseV2.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {case_id} not found"
        )
    
    # 更新字段
    if request.name is not None:
        case.name = request.name
    if request.description is not None:
        case.description = request.description
    if request.steps_json is not None:
        case.steps_json = [step.model_dump(by_alias=True, exclude_none=True) for step in request.steps_json]
    if request.input_variables is not None:
        case.input_variables = [v.model_dump(by_alias=True, exclude_none=True) for v in request.input_variables]
    if request.refs is not None:
        case.refs = [r.model_dump(by_alias=True, exclude_none=True) for r in request.refs]
    if request.config_override is not None:
        case.config_override = request.config_override
    if request.data_set_id is not None:
        case.data_set_id = request.data_set_id
    if request.launch_target is not None:
        case.launch_target = request.launch_target
    if request.tags is not None:
        case.tags = request.tags
    if request.priority is not None:
        case.priority = request.priority
    if request.status is not None:
        case.status = request.status
    
    await db.commit()
    await db.refresh(case)
    
    return TestCaseResponse(
        id=case.id,
        name=case.name,
        description=case.description,
        app_id=case.app_id,
        project_id=case.project_id,
        suite_id=case.suite_id,
        platform=case.platform.value if case.platform else "",
        steps_json=case.steps_json or [],
        input_variables=case.input_variables,
        refs=case.refs,
        config_override=case.config_override,
        data_set_id=case.data_set_id,
        launch_target=case.launch_target,
        tags=case.tags,
        priority=case.priority.value if case.priority else "medium",
        status=case.status.value if case.status else "draft",
        version=case.version or "1.0.0",
        step_count=case.get_step_count(),
        variable_names=case.get_variable_names(),
        created_at=case.created_at,
        updated_at=case.updated_at,
        created_by=case.created_by,
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除用例"""
    result = await db.execute(
        select(TestCaseV2).where(TestCaseV2.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {case_id} not found"
        )
    
    await db.delete(case)
    await db.commit()


@router.post("/{case_id}/compile")
async def compile_case(
    case_id: str,
    variables: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    编译用例为 TypeScript 测试文件
    
    返回编译后的文件路径和内容
    """
    result = await db.execute(
        select(TestCaseV2).where(TestCaseV2.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {case_id} not found"
        )
    
    # 编译
    compiler = TypeScriptCompiler()
    compile_result = await compiler.compile(
        case=case.to_dict(),
        runtime_variables=variables,
    )
    
    if not compile_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compile failed: {', '.join(compile_result.errors)}"
        )
    
    return {
        "success": True,
        "output_path": compile_result.output_path,
        "content": compile_result.output_content or "",  # 完整内容
        "content_preview": compile_result.output_content[:2000] if compile_result.output_content else "",
        "warnings": compile_result.warnings,
    }


@router.post("/{case_id}/duplicate", response_model=TestCaseResponse)
async def duplicate_case(
    case_id: str,
    new_name: str | None = Query(None, description="新用例名称"),
    db: AsyncSession = Depends(get_db),
) -> TestCaseResponse:
    """复制用例"""
    result = await db.execute(
        select(TestCaseV2).where(TestCaseV2.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {case_id} not found"
        )
    
    # 创建副本
    new_id = str(uuid.uuid4())
    new_case = TestCaseV2(
        id=new_id,
        name=new_name or f"{case.name} (Copy)",
        description=case.description,
        app_id=case.app_id,
        project_id=case.project_id,
        suite_id=case.suite_id,
        platform=case.platform,
        steps_json=case.steps_json,
        input_variables=case.input_variables,
        refs=case.refs,
        config_override=case.config_override,
        data_set_id=case.data_set_id,
        launch_target=case.launch_target,
        tags=case.tags,
        priority=case.priority,
        status=CaseStatus.DRAFT,
    )
    
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    
    return TestCaseResponse(
        id=new_case.id,
        name=new_case.name,
        description=new_case.description,
        app_id=new_case.app_id,
        project_id=new_case.project_id,
        suite_id=new_case.suite_id,
        platform=new_case.platform.value if new_case.platform else "",
        steps_json=new_case.steps_json or [],
        input_variables=new_case.input_variables,
        refs=new_case.refs,
        config_override=new_case.config_override,
        data_set_id=new_case.data_set_id,
        launch_target=new_case.launch_target,
        tags=new_case.tags,
        priority=new_case.priority.value if new_case.priority else "medium",
        status=new_case.status.value if new_case.status else "draft",
        version=new_case.version or "1.0.0",
        step_count=new_case.get_step_count(),
        variable_names=new_case.get_variable_names(),
        created_at=new_case.created_at,
        updated_at=new_case.updated_at,
        created_by=new_case.created_by,
    )
