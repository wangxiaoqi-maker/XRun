"""
AI 配置 API

注意：此模块已废弃，执行用例时直接使用 llm_providers + llm_models 表中的模型配置。
保留此文件是为了向后兼容，新功能请使用 llm_config.py 中的 API。
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from apps.ui_automation.database import get_db
from apps.ui_automation.models.ai_config import AIConfig
from apps.ui_automation.schemas.ai_config import (
    AIConfigCreate, AIConfigUpdate, AIConfigResponse, AIConfigList
)

router = APIRouter()

def mask_api_key(key: str) -> str:
    """脱敏 API Key"""
    if not key or len(key) < 10:
        return "***"
    return key[:6] + "****" + key[-4:]

def model_to_response(config: AIConfig, mask: bool = True) -> AIConfigResponse:
    """模型转响应"""
    return AIConfigResponse(
        id=config.id,
        name=config.name,
        base_url=config.base_url,
        api_key=mask_api_key(config.api_key) if mask else config.api_key,
        model_name=config.model_name,
        model_family=config.model_family,
        is_active=config.is_active,
        description=config.description,
        created_at=config.created_at,
        updated_at=config.updated_at
    )

@router.get("/", response_model=AIConfigList)
async def list_configs(db: AsyncSession = Depends(get_db)):
    """获取所有 AI 配置"""
    result = await db.execute(
        select(AIConfig).order_by(AIConfig.created_at.desc())
    )
    configs = result.scalars().all()
    
    return AIConfigList(
        items=[model_to_response(c) for c in configs]
    )

@router.post("/", response_model=AIConfigResponse)
async def create_config(
    config_data: AIConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建 AI 配置"""
    config = AIConfig(
        id=str(uuid.uuid4()),
        name=config_data.name,
        base_url=config_data.base_url,
        api_key=config_data.api_key,
        model_name=config_data.model_name,
        model_family=config_data.model_family,
        description=config_data.description,
        is_active=False
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return model_to_response(config)

@router.get("/{config_id}", response_model=AIConfigResponse)
async def get_config(config_id: str, db: AsyncSession = Depends(get_db)):
    """获取配置详情"""
    result = await db.execute(
        select(AIConfig).where(AIConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return model_to_response(config)

@router.put("/{config_id}", response_model=AIConfigResponse)
async def update_config(
    config_id: str,
    config_data: AIConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新配置"""
    result = await db.execute(
        select(AIConfig).where(AIConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    if config_data.name is not None:
        config.name = config_data.name
    if config_data.base_url is not None:
        config.base_url = config_data.base_url
    if config_data.api_key is not None:
        config.api_key = config_data.api_key
    if config_data.model_name is not None:
        config.model_name = config_data.model_name
    if config_data.model_family is not None:
        config.model_family = config_data.model_family
    if config_data.description is not None:
        config.description = config_data.description
    if config_data.is_active is not None:
        config.is_active = config_data.is_active
    
    await db.commit()
    await db.refresh(config)
    
    return model_to_response(config)

@router.delete("/{config_id}")
async def delete_config(config_id: str, db: AsyncSession = Depends(get_db)):
    """删除配置"""
    result = await db.execute(
        select(AIConfig).where(AIConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    await db.delete(config)
    await db.commit()
    
    return {"message": "删除成功"}

@router.post("/{config_id}/activate")
async def activate_config(config_id: str, db: AsyncSession = Depends(get_db)):
    """激活配置（设为默认）"""
    # 先取消所有激活
    result = await db.execute(select(AIConfig))
    all_configs = result.scalars().all()
    for c in all_configs:
        c.is_active = False
    
    # 激活指定配置
    result = await db.execute(
        select(AIConfig).where(AIConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    config.is_active = True
    await db.commit()
    
    return {"message": "激活成功"}

@router.get("/active/current")
async def get_active_config(db: AsyncSession = Depends(get_db)):
    """获取当前激活的配置"""
    result = await db.execute(
        select(AIConfig).where(AIConfig.is_active == True)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        return {"active": False, "config": None}
    
    return {
        "active": True,
        "config": model_to_response(config)
    }

@router.post("/test")
async def test_config(config_data: AIConfigCreate):
    """测试 AI 配置是否可用"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {config_data.api_key}",
                "Content-Type": "application/json"
            }
            
            # 简单测试请求
            async with session.post(
                f"{config_data.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": config_data.model_name,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return {"success": True, "message": "连接成功"}
                else:
                    error = await resp.text()
                    return {"success": False, "message": f"API 返回错误: {error}"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
