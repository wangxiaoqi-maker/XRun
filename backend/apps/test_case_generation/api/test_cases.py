from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
import io
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from apps.ui_automation.database import get_db
from apps.ui_automation.api.auth import get_current_user
from ..repositories.test_case_repo import TestCaseRepository
from ..schemas import TestCaseOut, TestCaseDetailOut, TestCaseUpdate, BatchReview, ApiResponse, ExcelExportRequest, ExportTemplateCreate, ExportTemplateOut
from ..models import TcgExportTemplate

router = APIRouter(tags=["TCG-用例管理"])


@router.get("/test-cases")
async def list_test_cases(
    project_id: str,
    page: int = 1,
    page_size: int = 20,
    review_status: Optional[str] = None,
    priority: Optional[str] = None,
    module_name: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TestCaseRepository(db)
    filters = {}
    if review_status:
        filters["review_status"] = review_status
    if priority:
        filters["priority"] = priority.split(",")
    if module_name:
        filters["module_name"] = module_name
    if search:
        filters["search"] = search

    cases, total = await repo.list_by_project(project_id, page, page_size, **filters)
    return ApiResponse(data={
        "items": [TestCaseOut.model_validate(c) for c in cases],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/test-cases/{case_id}")
async def get_test_case(
    case_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TestCaseRepository(db)
    case = await repo.get_by_id(case_id)
    if not case:
        return ApiResponse(success=False, message="用例不存在")
    return ApiResponse(data=TestCaseDetailOut.model_validate(case))


@router.put("/test-cases/{case_id}")
async def update_test_case(
    case_id: str,
    request: TestCaseUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TestCaseRepository(db)
    case = await repo.update(case_id, **request.model_dump(exclude_unset=True))
    if not case:
        return ApiResponse(success=False, message="用例不存在")
    return ApiResponse(data=TestCaseOut.model_validate(case))


@router.delete("/test-cases/{case_id}")
async def delete_test_case(
    case_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TestCaseRepository(db)
    deleted = await repo.delete(case_id)
    if not deleted:
        return ApiResponse(success=False, message="用例不存在")
    return ApiResponse(message="删除成功")


@router.post("/test-cases/batch-save")
async def batch_save_cases(
    body: dict,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从对话流生成的用例直接批量保存入库"""
    project_id = body.get("project_id")
    cases_data = body.get("cases", [])
    module_name = body.get("module_name", "")
    if not project_id or not cases_data:
        return ApiResponse(success=False, message="缺少 project_id 或 cases")

    records = []
    for c in cases_data:
        records.append({
            "project_id": project_id,
            "module_name": module_name or c.get("module_name", ""),
            "case_no": c.get("case_no", ""),
            "name": c.get("name", ""),
            "description": c.get("description", ""),
            "test_type": c.get("test_type", ""),
            "priority": c.get("priority", "P2"),
            "preconditions": c.get("preconditions", ""),
            "test_steps": c.get("test_steps", []),
            "tags": c.get("tags", []),
            "review_status": "approved",
            "creator": current_user.username if hasattr(current_user, 'username') else "ai",
        })

    repo = TestCaseRepository(db)
    saved = await repo.batch_create(records)

    import asyncio
    async def _index_to_kb():
        try:
            from apps.ui_automation.database import AsyncSessionLocal
            from ..knowledge.service import KnowledgeService
            async with AsyncSessionLocal() as kb_db:
                kb = KnowledgeService(kb_db)
                await kb.index_test_cases(project_id, records)
        except Exception as e:
            from loguru import logger
            logger.warning(f"用例入库知识库失败: {e}")
    asyncio.create_task(_index_to_kb())

    return ApiResponse(data={"saved_count": len(saved)})


@router.post("/test-cases/batch-delete")
async def batch_delete_cases(
    case_ids: List[str],
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除用例"""
    repo = TestCaseRepository(db)
    deleted_count = await repo.batch_delete(case_ids)
    return ApiResponse(message=f"已删除 {deleted_count} 条用例")


@router.post("/conversations/{conversation_id}/test-cases/review")
async def batch_review_cases(
    conversation_id: str,
    request: BatchReview,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量审查用例：更新评审状态和评论"""
    repo = TestCaseRepository(db)
    await repo.batch_update_review([r.model_dump() for r in request.reviews])
    return ApiResponse(message=f"已审查 {len(request.reviews)} 条用例")


@router.post("/conversations/{conversation_id}/test-cases/save")
async def save_approved_cases(
    conversation_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将审查通过的用例正式保存入库"""
    repo = TestCaseRepository(db)
    cases = await repo.list_by_conversation(conversation_id)
    approved = [c for c in cases if c.review_status == "approved"]
    # 正式入库：将状态从 approved 改为 pending（待入库）
    for c in approved:
        c.review_status = "pending"
    await db.commit()
    return ApiResponse(data={"saved_count": len(approved)})


# --- 导出模板管理 ---
@router.get("/export-templates")
async def list_export_templates(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取导出模板列表"""
    from sqlalchemy import select
    result = await db.execute(
        select(TcgExportTemplate).where(TcgExportTemplate.project_id == project_id)
    )
    templates = result.scalars().all()
    return ApiResponse(data=[ExportTemplateOut.model_validate(t) for t in templates])


@router.post("/export-templates")
async def create_export_template(
    project_id: str,
    request: ExportTemplateCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建导出模板"""
    template = TcgExportTemplate(
        project_id=project_id,
        name=request.name,
        description=request.description,
        columns=request.columns,
        style_config=request.style_config,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return ApiResponse(data=ExportTemplateOut.model_validate(template))


@router.put("/export-templates/{template_id}")
async def update_export_template(
    template_id: str,
    request: ExportTemplateCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新导出模板"""
    from sqlalchemy import select
    result = await db.execute(
        select(TcgExportTemplate).where(TcgExportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        return ApiResponse(success=False, message="模板不存在")
    template.name = request.name
    template.description = request.description
    template.columns = request.columns
    template.style_config = request.style_config
    await db.commit()
    await db.refresh(template)
    return ApiResponse(data=ExportTemplateOut.model_validate(template))


@router.delete("/export-templates/{template_id}")
async def delete_export_template(
    template_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除导出模板"""
    from sqlalchemy import select
    result = await db.execute(
        select(TcgExportTemplate).where(TcgExportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        return ApiResponse(success=False, message="模板不存在")
    await db.delete(template)
    await db.commit()
    return ApiResponse(message="删除成功")


# --- 导出用例 ---
DEFAULT_COLUMNS = [
    {"key": "module_name", "label": "模块", "width": 20},
    {"key": "name", "label": "用例标题*", "width": 40},
    {"key": "priority", "label": "优先级", "width": 10},
    {"key": "preconditions", "label": "前置条件", "width": 30},
    {"key": "test_steps", "label": "操作步骤", "width": 40},
    {"key": "expected", "label": "预期结果", "width": 40},
    {"key": "test_type", "label": "用例类型", "width": 15},
    {"key": "tags", "label": "标签", "width": 20},
    {"key": "requirement_name", "label": "关联需求名称", "width": 25},
    {"key": "requirement_link", "label": "关联需求链接", "width": 30},
    {"key": "creator", "label": "创建人", "width": 15},
    {"key": "created_at", "label": "创建时间", "width": 20},
    {"key": "remark", "label": "备注", "width": 30},
]


def format_test_steps(steps):
    """格式化测试步骤为可读文本"""
    if not steps:
        return ""
    return "\n".join([f"{s.get('step', '')}. {s.get('action', '')}" for s in steps])


def format_expected_results(steps):
    """格式化预期结果为可读文本"""
    if not steps:
        return ""
    return "\n".join([f"{s.get('step', '')}. {s.get('expected', '')}" for s in steps])


@router.post("/test-cases/export")
async def export_test_cases(
    request: ExcelExportRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导出测试用例为Excel"""
    repo = TestCaseRepository(db)
    
    # 获取要导出的用例
    if request.case_ids:
        cases = await repo.get_by_ids(request.case_ids)
    elif request.project_id:
        cases, _ = await repo.list_by_project(request.project_id, page=1, page_size=10000)
        # 应用过滤条件
        if request.filters:
            if request.filters.get("review_status"):
                cases = [c for c in cases if c.review_status == request.filters["review_status"]]
            if request.filters.get("priority"):
                cases = [c for c in cases if c.priority in request.filters["priority"]]
            if request.filters.get("module_name"):
                cases = [c for c in cases if c.module_name == request.filters["module_name"]]
    else:
        return ApiResponse(success=False, message="请提供用例ID列表或项目ID")
    
    # 获取模板配置
    columns = DEFAULT_COLUMNS
    if request.template_id:
        from sqlalchemy import select
        result = await db.execute(
            select(TcgExportTemplate).where(TcgExportTemplate.id == request.template_id)
        )
        template = result.scalar_one_or_none()
        if template and template.columns:
            columns = template.columns
    
    # 创建Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "测试用例"
    
    # 设置表头样式
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 写入表头
    for col_idx, col in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col.get("label", col.get("key", "")))
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = col.get("width", 15)
    
    # 写入数据
    for row_idx, case in enumerate(cases, 2):
        for col_idx, col in enumerate(columns, 1):
            key = col.get("key", "")
            value = ""
            if key == "case_no":
                value = case.case_no or ""
            elif key == "name":
                value = case.name or ""
            elif key == "module_name":
                value = case.module_name or ""
            elif key == "priority":
                value = case.priority or ""
            elif key == "test_type":
                value = case.test_type or ""
            elif key == "preconditions":
                value = case.preconditions or ""
            elif key == "creator":
                value = case.creator or ""
            elif key == "created_at":
                value = case.created_at.strftime("%Y-%m-%d %H:%M:%S") if case.created_at else ""
            elif key == "test_steps":
                value = format_test_steps(case.test_steps)
            elif key == "expected":
                value = format_expected_results(case.test_steps)
            elif key == "tags":
                tags = case.tags
                value = ", ".join(tags) if tags else ""
            elif key == "requirement_name":
                value = ""
            elif key == "requirement_link":
                value = ""
            elif key == "remark":
                value = case.description or ""
            
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    
    # 保存到内存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=test_cases.xlsx"}
    )
