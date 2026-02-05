"""
执行配置 API V2

提供全局配置、变量、缓存配置的管理
"""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.ui_automation.database import get_db
from apps.ui_automation.execution.models import (
    ExecutionConfig,
    GlobalVariable,
    CacheConfig,
    ConfigScope,
    CacheStrategy,
)
from apps.ui_automation.execution.schemas.config import (
    ExecutionConfigSchema,
    GlobalVariableSchema,
    CacheConfigSchema,
)

router = APIRouter(prefix="/config", tags=["执行配置 V2"])


# ==================== 执行配置 ====================

@router.get("", response_model=dict[str, Any])
async def get_global_config(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取全局执行配置"""
    result = await db.execute(
        select(ExecutionConfig).where(
            ExecutionConfig.scope == ConfigScope.GLOBAL,
            ExecutionConfig.scope_id == None,
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        # 返回默认配置
        return {
            "scope": "global",
            "test_timeout_ms": 240000,
            "step_timeout_ms": 720000,
            "hook_timeout_ms": 240000,
            "wait_timeout_ms": 30000,
            "wait_interval_ms": 3000,
            "default_retry_count": 0,
            "retry_delay_ms": 1000,
            "retry_backoff": True,
            "replanning_cycle_limit": 20,
            "wait_after_action_ms": 300,
            "auto_dismiss_keyboard": True,
            "generate_report": True,
        }
    
    return config.to_dict()


@router.put("")
async def update_global_config(
    request: ExecutionConfigSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新全局执行配置"""
    result = await db.execute(
        select(ExecutionConfig).where(
            ExecutionConfig.scope == ConfigScope.GLOBAL,
            ExecutionConfig.scope_id == None,
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        # 创建新配置
        config = ExecutionConfig(
            id=str(uuid.uuid4()),
            scope=ConfigScope.GLOBAL,
        )
        db.add(config)
    
    # 更新字段
    update_data = request.model_dump(exclude_none=True, by_alias=False)
    for key, value in update_data.items():
        if hasattr(config, key) and key not in ("scope", "scope_id"):
            setattr(config, key, value)
    
    await db.commit()
    await db.refresh(config)
    
    return config.to_dict()


@router.get("/app/{app_id}", response_model=dict[str, Any])
async def get_app_config(
    app_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取应用级执行配置（合并全局配置）"""
    # 获取全局配置
    global_result = await db.execute(
        select(ExecutionConfig).where(
            ExecutionConfig.scope == ConfigScope.GLOBAL,
            ExecutionConfig.scope_id == None,
        )
    )
    global_config = global_result.scalar_one_or_none()
    
    # 获取应用配置
    app_result = await db.execute(
        select(ExecutionConfig).where(
            ExecutionConfig.scope == ConfigScope.APP,
            ExecutionConfig.scope_id == app_id,
        )
    )
    app_config = app_result.scalar_one_or_none()
    
    # 合并配置
    base = global_config.to_dict() if global_config else {}
    override = app_config.to_dict() if app_config else {}
    
    result = {**base}
    for key, value in override.items():
        if value is not None:
            result[key] = value
    
    result["scope"] = "app"
    result["scope_id"] = app_id
    
    return result


@router.put("/app/{app_id}")
async def update_app_config(
    app_id: str,
    request: ExecutionConfigSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新应用级执行配置"""
    result = await db.execute(
        select(ExecutionConfig).where(
            ExecutionConfig.scope == ConfigScope.APP,
            ExecutionConfig.scope_id == app_id,
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        config = ExecutionConfig(
            id=str(uuid.uuid4()),
            scope=ConfigScope.APP,
            scope_id=app_id,
        )
        db.add(config)
    
    update_data = request.model_dump(exclude_none=True, by_alias=False)
    for key, value in update_data.items():
        if hasattr(config, key) and key not in ("scope", "scope_id"):
            setattr(config, key, value)
    
    await db.commit()
    await db.refresh(config)
    
    return config.to_dict()


# ==================== 全局变量 ====================

@router.get("/variables", response_model=dict[str, Any])
async def list_variables(
    scope: ConfigScope = Query(ConfigScope.GLOBAL, description="作用域"),
    scope_id: str | None = Query(None, description="作用域 ID"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取变量列表"""
    query = select(GlobalVariable).where(
        GlobalVariable.scope == scope,
        GlobalVariable.is_active == True,
    )
    
    if scope_id:
        query = query.where(GlobalVariable.scope_id == scope_id)
    else:
        query = query.where(GlobalVariable.scope_id == None)
    
    result = await db.execute(query.order_by(GlobalVariable.name))
    variables = result.scalars().all()
    
    return {
        "total": len(variables),
        "items": [v.to_dict() for v in variables],
    }


@router.post("/variables", status_code=status.HTTP_201_CREATED)
async def create_variable(
    request: GlobalVariableSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建全局变量"""
    # 检查是否已存在
    result = await db.execute(
        select(GlobalVariable).where(
            GlobalVariable.scope == request.scope,
            GlobalVariable.scope_id == request.scope_id,
            GlobalVariable.name == request.name,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Variable {request.name} already exists"
        )
    
    variable = GlobalVariable(
        id=str(uuid.uuid4()),
        scope=request.scope,
        scope_id=request.scope_id,
        name=request.name,
        value=request.value,
        value_type=request.value_type,
        is_secret=request.is_secret,
        description=request.description,
    )
    
    db.add(variable)
    await db.commit()
    await db.refresh(variable)
    
    return variable.to_dict()


@router.put("/variables/{variable_id}")
async def update_variable(
    variable_id: str,
    request: GlobalVariableSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新全局变量"""
    result = await db.execute(
        select(GlobalVariable).where(GlobalVariable.id == variable_id)
    )
    variable = result.scalar_one_or_none()
    
    if not variable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable {variable_id} not found"
        )
    
    variable.name = request.name
    variable.value = request.value
    variable.value_type = request.value_type
    variable.is_secret = request.is_secret
    variable.description = request.description
    
    await db.commit()
    await db.refresh(variable)
    
    return variable.to_dict()


@router.delete("/variables/{variable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variable(
    variable_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除全局变量"""
    result = await db.execute(
        select(GlobalVariable).where(GlobalVariable.id == variable_id)
    )
    variable = result.scalar_one_or_none()
    
    if not variable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable {variable_id} not found"
        )
    
    await db.delete(variable)
    await db.commit()


# ==================== 缓存配置 ====================

@router.get("/cache", response_model=dict[str, Any])
async def get_cache_config(
    scope: ConfigScope = Query(ConfigScope.GLOBAL),
    scope_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取缓存配置"""
    query = select(CacheConfig).where(CacheConfig.scope == scope)
    
    if scope_id:
        query = query.where(CacheConfig.scope_id == scope_id)
    else:
        query = query.where(CacheConfig.scope_id == None)
    
    result = await db.execute(query)
    config = result.scalar_one_or_none()
    
    if not config:
        return {
            "scope": scope.value,
            "scope_id": scope_id,
            "strategy": "disabled",
            "cache_id_pattern": "${case_id}",
            "cache_dir": "./midscene_run/cache",
            "auto_cleanup": False,
        }
    
    return config.to_dict()


@router.put("/cache")
async def update_cache_config(
    request: CacheConfigSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新缓存配置"""
    result = await db.execute(
        select(CacheConfig).where(
            CacheConfig.scope == request.scope,
            CacheConfig.scope_id == request.scope_id,
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        config = CacheConfig(
            id=str(uuid.uuid4()),
            scope=request.scope,
            scope_id=request.scope_id,
        )
        db.add(config)
    
    config.strategy = request.strategy
    config.cache_id_pattern = request.cache_id_pattern
    config.cache_dir = request.cache_dir
    config.auto_cleanup = request.auto_cleanup
    config.cleanup_after_days = request.cleanup_after_days
    
    await db.commit()
    await db.refresh(config)
    
    return config.to_dict()
