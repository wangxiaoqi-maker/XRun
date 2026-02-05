"""
测试套件/目录 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ui_automation.database import get_db
from apps.ui_automation.execution.models.test_suite import TestSuite
from apps.ui_automation.execution.models.test_case import TestCaseV2
from apps.ui_automation.execution.schemas.test_suite import (
    TestSuiteCreate,
    TestSuiteUpdate,
    TestSuiteResponse,
    TestSuiteTreeNode
)

router = APIRouter(prefix="/suites", tags=["测试套件"])


@router.get("", response_model=list[TestSuiteResponse])
async def list_suites(
    project_id: str | None = None,
    parent_id: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """获取套件列表"""
    query = select(TestSuite)
    
    if project_id:
        query = query.where(TestSuite.project_id == project_id)
    
    if parent_id:
        query = query.where(TestSuite.parent_id == parent_id)
    elif parent_id is None and project_id:
        # 只获取根目录
        query = query.where(TestSuite.parent_id.is_(None))
    
    query = query.order_by(TestSuite.sort_order, TestSuite.created_at)
    
    result = await db.execute(query)
    suites = result.scalars().all()
    
    return [TestSuiteResponse.model_validate(s) for s in suites]


@router.get("/tree")
async def get_suite_tree(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """获取套件树结构"""
    query = select(TestSuite)
    if project_id:
        query = query.where(TestSuite.project_id == project_id)
    query = query.order_by(TestSuite.depth, TestSuite.sort_order, TestSuite.created_at)
    
    result = await db.execute(query)
    suites = result.scalars().all()
    
    # 获取每个套件的用例数量
    case_count_query = select(
        TestCaseV2.suite_id,
        func.count(TestCaseV2.id).label("count")
    ).where(TestCaseV2.suite_id.isnot(None)).group_by(TestCaseV2.suite_id)
    
    case_counts_result = await db.execute(case_count_query)
    case_counts = {row.suite_id: row.count for row in case_counts_result}
    
    # 构建树
    suite_map = {s.id: s for s in suites}
    root_nodes = []
    
    for suite in suites:
        node = {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "parentId": suite.parent_id,
            "depth": suite.depth,
            "sortOrder": suite.sort_order,
            "hasChildren": False,
            "children": [],
            "caseCount": case_counts.get(suite.id, 0)
        }
        
        if suite.parent_id and suite.parent_id in suite_map:
            # 找到父节点，添加到父节点的 children
            parent = suite_map[suite.parent_id]
            if not hasattr(parent, '_children'):
                parent._children = []
            parent._children.append(node)
        else:
            # 根节点
            root_nodes.append(node)
    
    # 递归填充 children
    def fill_children(node, suite_map):
        suite = suite_map.get(node["id"])
        if suite and hasattr(suite, '_children'):
            node["children"] = suite._children
            node["hasChildren"] = True
            for child in node["children"]:
                fill_children(child, suite_map)
    
    for node in root_nodes:
        fill_children(node, suite_map)
    
    return root_nodes


@router.get("/{suite_id}", response_model=TestSuiteResponse)
async def get_suite(
    suite_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取套件详情"""
    result = await db.execute(
        select(TestSuite).where(TestSuite.id == suite_id)
    )
    suite = result.scalar_one_or_none()
    
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    
    return TestSuiteResponse.model_validate(suite)


@router.post("", response_model=TestSuiteResponse, status_code=201)
async def create_suite(
    request: TestSuiteCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建套件"""
    # 计算深度和路径
    depth = 0
    path = f"/{request.name}"
    
    if request.parent_id:
        parent_result = await db.execute(
            select(TestSuite).where(TestSuite.id == request.parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="父目录不存在")
        depth = parent.depth + 1
        path = f"{parent.path}/{request.name}"
    
    # 获取同级最大排序号
    sort_query = select(func.max(TestSuite.sort_order)).where(
        and_(
            TestSuite.parent_id == request.parent_id,
            TestSuite.project_id == request.project_id
        )
    )
    max_sort_result = await db.execute(sort_query)
    max_sort = max_sort_result.scalar() or 0
    
    suite = TestSuite(
        name=request.name,
        description=request.description,
        parent_id=request.parent_id,
        project_id=request.project_id,
        depth=depth,
        path=path,
        sort_order=max_sort + 1
    )
    
    db.add(suite)
    await db.commit()
    await db.refresh(suite)
    
    return TestSuiteResponse.model_validate(suite)


@router.put("/{suite_id}", response_model=TestSuiteResponse)
async def update_suite(
    suite_id: str,
    request: TestSuiteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新套件"""
    result = await db.execute(
        select(TestSuite).where(TestSuite.id == suite_id)
    )
    suite = result.scalar_one_or_none()
    
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    
    # 更新字段
    if request.name is not None:
        suite.name = request.name
        # 更新路径
        if suite.parent_id:
            parent_result = await db.execute(
                select(TestSuite).where(TestSuite.id == suite.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
            suite.path = f"{parent.path}/{request.name}" if parent else f"/{request.name}"
        else:
            suite.path = f"/{request.name}"
    
    if request.description is not None:
        suite.description = request.description
    
    if request.sort_order is not None:
        suite.sort_order = request.sort_order
    
    # 处理移动到新父目录
    if request.parent_id is not None and request.parent_id != suite.parent_id:
        if request.parent_id:
            new_parent_result = await db.execute(
                select(TestSuite).where(TestSuite.id == request.parent_id)
            )
            new_parent = new_parent_result.scalar_one_or_none()
            if not new_parent:
                raise HTTPException(status_code=400, detail="目标父目录不存在")
            suite.parent_id = request.parent_id
            suite.depth = new_parent.depth + 1
            suite.path = f"{new_parent.path}/{suite.name}"
        else:
            suite.parent_id = None
            suite.depth = 0
            suite.path = f"/{suite.name}"
    
    await db.commit()
    await db.refresh(suite)
    
    return TestSuiteResponse.model_validate(suite)


@router.delete("/{suite_id}")
async def delete_suite(
    suite_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除套件（级联删除子目录）"""
    result = await db.execute(
        select(TestSuite).where(TestSuite.id == suite_id)
    )
    suite = result.scalar_one_or_none()
    
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    
    # 检查是否有关联的用例
    case_count_result = await db.execute(
        select(func.count(TestCaseV2.id)).where(TestCaseV2.suite_id == suite_id)
    )
    case_count = case_count_result.scalar() or 0
    
    if case_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"该目录下有 {case_count} 个用例，请先移动或删除用例"
        )
    
    # 检查是否有子目录
    children_result = await db.execute(
        select(func.count(TestSuite.id)).where(TestSuite.parent_id == suite_id)
    )
    children_count = children_result.scalar() or 0
    
    if children_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"该目录下有 {children_count} 个子目录，请先删除子目录"
        )
    
    await db.delete(suite)
    await db.commit()
    
    return {"success": True, "message": "删除成功"}
