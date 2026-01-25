"""
用例管理 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import json
import yaml

from apps.ui_automation.database import get_db
from apps.ui_automation.models.test_case import TestCase
from apps.ui_automation.schemas.test_case import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse, TestCaseList
)

router = APIRouter()

def model_to_response(case: TestCase) -> TestCaseResponse:
    """模型转响应"""
    tags = json.loads(case.tags) if case.tags else []
    return TestCaseResponse(
        id=case.id,
        name=case.name,
        description=case.description,
        platform=case.platform,
        yaml_content=case.yaml_content,
        tags=tags,
        created_at=case.created_at,
        updated_at=case.updated_at
    )

@router.get("/", response_model=TestCaseList)
async def list_cases(
    platform: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取用例列表"""
    query = select(TestCase)
    if platform:
        query = query.where(TestCase.platform == platform)
    
    query = query.order_by(TestCase.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()
    
    # 获取总数
    count_query = select(TestCase)
    if platform:
        count_query = count_query.where(TestCase.platform == platform)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return TestCaseList(
        total=total,
        items=[model_to_response(c) for c in cases]
    )

@router.post("/", response_model=TestCaseResponse)
async def create_case(
    case_data: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建用例"""
    # 验证 YAML 格式
    try:
        parsed = yaml.safe_load(case_data.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML 格式错误: {e}")
    
    case = TestCase(
        id=str(uuid.uuid4()),
        name=case_data.name,
        description=case_data.description,
        platform=case_data.platform.value,
        yaml_content=case_data.yaml_content,
        tags=json.dumps(case_data.tags or [])
    )
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    return model_to_response(case)

@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """获取用例详情"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    return model_to_response(case)

@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_case(
    case_id: str,
    case_data: TestCaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    # 验证 YAML
    if case_data.yaml_content:
        try:
            yaml.safe_load(case_data.yaml_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"YAML 格式错误: {e}")
        case.yaml_content = case_data.yaml_content
    
    if case_data.name is not None:
        case.name = case_data.name
    if case_data.description is not None:
        case.description = case_data.description
    if case_data.tags is not None:
        case.tags = json.dumps(case_data.tags)
    
    await db.commit()
    await db.refresh(case)
    
    return model_to_response(case)

@router.delete("/{case_id}")
async def delete_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """删除用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    await db.delete(case)
    await db.commit()
    
    return {"message": "删除成功"}

@router.post("/{case_id}/duplicate", response_model=TestCaseResponse)
async def duplicate_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """复制用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    new_case = TestCase(
        id=str(uuid.uuid4()),
        name=f"{original.name} (副本)",
        description=original.description,
        platform=original.platform,
        yaml_content=original.yaml_content,
        tags=original.tags
    )
    
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    
    return model_to_response(new_case)

@router.post("/validate-yaml")
async def validate_yaml(data: dict):
    """验证 YAML 格式"""
    yaml_content = data.get("yaml_content", "")
    try:
        parsed = yaml.safe_load(yaml_content)
        return {"valid": True, "parsed": parsed}
    except yaml.YAMLError as e:
        return {"valid": False, "error": str(e)}

@router.post("/from-steps", response_model=dict)
async def generate_yaml_from_steps(data: dict):
    """从步骤生成 YAML"""
    steps = data.get("steps", [])
    name = data.get("name", "未命名用例")
    platform = data.get("platform", "android")
    description = data.get("description", "")
    
    yaml_data = {
        "name": name,
        "description": description,
        "platform": platform,
        "steps": steps
    }
    
    yaml_content = yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False)
    return {"yaml_content": yaml_content}
