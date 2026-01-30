"""
大模型配置与用量统计 API
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from apps.ui_automation.database import get_session
from apps.ui_automation.models.llm_config import (
    LLMProvider, LLMModel, LLMUsageLog,
    ModelType, ModelStatus
)

router = APIRouter(prefix="/llm", tags=["大模型配置"])


# ============ Pydantic Schemas ============

class ProviderCreate(BaseModel):
    name: str = Field(..., description="供应商名称")
    code: str = Field(..., description="供应商代码")
    base_url: str = Field(..., description="API Base URL")
    api_key: Optional[str] = Field(None, description="API Key")
    icon: Optional[str] = None
    description: Optional[str] = None


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ModelCreate(BaseModel):
    provider_id: str
    name: str
    model_id: str
    model_type: str = "chat"
    max_tokens: int = 4096
    supports_vision: bool = False
    supports_function_call: bool = False
    input_price: float = 0.0
    output_price: float = 0.0
    config: Optional[dict] = None


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    model_id: Optional[str] = None
    model_type: Optional[str] = None
    max_tokens: Optional[int] = None
    supports_vision: Optional[bool] = None
    supports_function_call: Optional[bool] = None
    input_price: Optional[float] = None
    output_price: Optional[float] = None
    status: Optional[str] = None
    is_default: Optional[bool] = None
    config: Optional[dict] = None


# ============ Provider APIs ============

@router.get("/providers")
async def list_providers(include_disabled: bool = False):
    """获取所有供应商列表"""
    async with get_session() as session:
        query = select(LLMProvider)
        if not include_disabled:
            query = query.where(LLMProvider.status == ModelStatus.ENABLED)
        query = query.order_by(LLMProvider.created_at.desc())
        
        result = await session.execute(query)
        providers = result.scalars().all()
        
        return {
            "providers": [p.to_dict() for p in providers],
            "total": len(providers),
            "enabled": sum(1 for p in providers if p.status == ModelStatus.ENABLED),
            "disabled": sum(1 for p in providers if p.status == ModelStatus.DISABLED)
        }


@router.post("/providers")
async def create_provider(data: ProviderCreate):
    """创建供应商"""
    async with get_session() as session:
        # 检查 code 是否重复
        existing = await session.execute(
            select(LLMProvider).where(LLMProvider.code == data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"供应商代码 {data.code} 已存在")
        
        provider = LLMProvider(
            name=data.name,
            code=data.code,
            base_url=data.base_url,
            api_key=data.api_key,
            icon=data.icon,
            description=data.description
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        
        return provider.to_dict()


@router.get("/providers/{provider_id}")
async def get_provider(provider_id: str, include_key: bool = False):
    """获取单个供应商详情"""
    async with get_session() as session:
        result = await session.execute(
            select(LLMProvider).where(LLMProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        return provider.to_dict(include_key=include_key)


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, data: ProviderUpdate):
    """更新供应商"""
    async with get_session() as session:
        result = await session.execute(
            select(LLMProvider).where(LLMProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "status" and value:
                value = ModelStatus(value)
            setattr(provider, key, value)
        
        await session.commit()
        await session.refresh(provider)
        
        return provider.to_dict()


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """删除供应商"""
    from sqlalchemy import delete as sql_delete
    
    async with get_session() as session:
        result = await session.execute(
            select(LLMProvider).where(LLMProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        # 先删除关联的模型
        await session.execute(
            sql_delete(LLMModel).where(LLMModel.provider_id == provider_id)
        )
        
        # 再删除供应商
        await session.delete(provider)
        await session.commit()
        
        return {"message": "删除成功"}


# ============ Model APIs ============

@router.get("/models")
async def list_models(
    provider_id: Optional[str] = None,
    model_type: Optional[str] = None,
    include_disabled: bool = False
):
    """获取模型列表"""
    async with get_session() as session:
        query = select(LLMModel)
        
        conditions = []
        if provider_id:
            conditions.append(LLMModel.provider_id == provider_id)
        if model_type:
            conditions.append(LLMModel.model_type == ModelType(model_type))
        if not include_disabled:
            conditions.append(LLMModel.status == ModelStatus.ENABLED)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(LLMModel.is_default.desc(), LLMModel.created_at.desc())
        
        result = await session.execute(query)
        models = result.scalars().all()
        
        # 获取供应商信息
        provider_ids = list(set(m.provider_id for m in models))
        providers_result = await session.execute(
            select(LLMProvider).where(LLMProvider.id.in_(provider_ids))
        )
        providers_map = {p.id: p.to_dict() for p in providers_result.scalars().all()}
        
        return {
            "models": [
                {**m.to_dict(), "provider": providers_map.get(m.provider_id)}
                for m in models
            ],
            "total": len(models)
        }


@router.post("/models")
async def create_model(data: ModelCreate):
    """创建模型"""
    async with get_session() as session:
        # 验证供应商存在
        provider_result = await session.execute(
            select(LLMProvider).where(LLMProvider.id == data.provider_id)
        )
        if not provider_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="供应商不存在")
        
        model = LLMModel(
            provider_id=data.provider_id,
            name=data.name,
            model_id=data.model_id,
            model_type=ModelType(data.model_type),
            max_tokens=data.max_tokens,
            supports_vision=data.supports_vision,
            supports_function_call=data.supports_function_call,
            input_price=data.input_price,
            output_price=data.output_price,
            config=data.config
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        
        return model.to_dict()


@router.put("/models/{model_id}")
async def update_model(model_id: str, data: ModelUpdate):
    """更新模型"""
    async with get_session() as session:
        result = await session.execute(
            select(LLMModel).where(LLMModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "status" and value:
                value = ModelStatus(value)
            elif key == "model_type" and value:
                value = ModelType(value)
            setattr(model, key, value)
        
        # 如果设置为默认，取消其他默认
        if data.is_default:
            await session.execute(
                select(LLMModel)
                .where(LLMModel.id != model_id)
                .where(LLMModel.model_type == model.model_type)
            )
        
        await session.commit()
        await session.refresh(model)
        
        return model.to_dict()


@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """删除模型"""
    async with get_session() as session:
        result = await session.execute(
            select(LLMModel).where(LLMModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        await session.delete(model)
        await session.commit()
        
        return {"message": "删除成功"}


# ============ Usage Statistics APIs ============

@router.get("/usage/stats")
async def get_usage_stats(
    hours: int = Query(24, description="统计时间范围(小时)"),
    provider_id: Optional[str] = None
):
    """获取用量统计概览"""
    async with get_session() as session:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        conditions = [LLMUsageLog.created_at >= since]
        if provider_id:
            conditions.append(LLMUsageLog.provider_id == provider_id)
        
        # 总体统计
        total_result = await session.execute(
            select(
                func.count(LLMUsageLog.id).label("requests"),
                func.sum(LLMUsageLog.total_tokens).label("tokens"),
                func.avg(LLMUsageLog.latency_ms).label("avg_latency"),
                func.sum(LLMUsageLog.cost).label("total_cost")
            ).where(and_(*conditions))
        )
        total = total_result.one()
        
        # 按供应商统计
        provider_stats_result = await session.execute(
            select(
                LLMUsageLog.provider_id,
                func.count(LLMUsageLog.id).label("requests"),
                func.sum(LLMUsageLog.total_tokens).label("tokens"),
                func.avg(LLMUsageLog.latency_ms).label("avg_latency"),
                func.sum(func.cast(LLMUsageLog.success, Integer)).label("success_count")
            )
            .where(and_(*conditions))
            .group_by(LLMUsageLog.provider_id)
        )
        provider_stats = provider_stats_result.all()
        
        # 获取供应商名称
        provider_ids = [s[0] for s in provider_stats]
        providers_result = await session.execute(
            select(LLMProvider).where(LLMProvider.id.in_(provider_ids))
        )
        providers_map = {p.id: p for p in providers_result.scalars().all()}
        
        return {
            "time_range_hours": hours,
            "total": {
                "requests": total.requests or 0,
                "tokens": total.tokens or 0,
                "avg_latency_ms": round(total.avg_latency or 0, 1),
                "total_cost": round(total.total_cost or 0, 4)
            },
            "by_provider": [
                {
                    "provider_id": s[0],
                    "provider_name": providers_map.get(s[0]).name if s[0] in providers_map else "Unknown",
                    "provider_code": providers_map.get(s[0]).code if s[0] in providers_map else "unknown",
                    "requests": s[1],
                    "tokens": s[2] or 0,
                    "avg_latency_ms": round(s[3] or 0, 1),
                    "success_rate": round((s[4] / s[1] * 100) if s[1] > 0 else 0, 1)
                }
                for s in provider_stats
            ],
            "providers_count": len(set(provider_ids))
        }


@router.get("/usage/trend")
async def get_usage_trend(
    hours: int = Query(24, description="统计时间范围(小时)"),
    interval: str = Query("hour", description="统计间隔: hour, day")
):
    """获取用量趋势"""
    async with get_session() as session:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # 按时间分组统计
        if interval == "hour":
            time_format = func.strftime('%Y-%m-%d %H:00', LLMUsageLog.created_at)
        else:
            time_format = func.strftime('%Y-%m-%d', LLMUsageLog.created_at)
        
        result = await session.execute(
            select(
                time_format.label("time"),
                func.count(LLMUsageLog.id).label("requests"),
                func.sum(LLMUsageLog.total_tokens).label("tokens")
            )
            .where(LLMUsageLog.created_at >= since)
            .group_by(time_format)
            .order_by(time_format)
        )
        
        trend_data = result.all()
        
        return {
            "interval": interval,
            "data": [
                {
                    "time": row.time,
                    "requests": row.requests,
                    "tokens": row.tokens or 0
                }
                for row in trend_data
            ]
        }


@router.get("/usage/by-model")
async def get_usage_by_model(hours: int = Query(24)):
    """按模型统计用量（用于饼图）"""
    async with get_session() as session:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await session.execute(
            select(
                LLMUsageLog.model_id,
                func.sum(LLMUsageLog.total_tokens).label("tokens")
            )
            .where(LLMUsageLog.created_at >= since)
            .group_by(LLMUsageLog.model_id)
            .order_by(desc("tokens"))
        )
        
        usage_data = result.all()
        
        # 获取模型名称
        model_ids = [row[0] for row in usage_data]
        models_result = await session.execute(
            select(LLMModel).where(LLMModel.id.in_(model_ids))
        )
        models_map = {m.id: m for m in models_result.scalars().all()}
        
        return {
            "data": [
                {
                    "model_id": row[0],
                    "model_name": models_map.get(row[0]).name if row[0] in models_map else "Unknown",
                    "tokens": row[1] or 0
                }
                for row in usage_data
            ]
        }


# ============ Utility: Record Usage ============

async def record_usage(
    provider_id: str,
    model_id: str,
    request_type: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: int = 0,
    success: bool = True,
    error_message: str = None,
    cost: float = 0.0
):
    """记录模型调用（供其他模块调用）"""
    async with get_session() as session:
        log = LLMUsageLog(
            provider_id=provider_id,
            model_id=model_id,
            request_type=request_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            cost=cost
        )
        session.add(log)
        await session.commit()
        
        # 更新供应商统计缓存
        provider = await session.execute(
            select(LLMProvider).where(LLMProvider.id == provider_id)
        )
        provider = provider.scalar_one_or_none()
        if provider:
            provider.total_requests = (provider.total_requests or 0) + 1
            provider.total_tokens = (provider.total_tokens or 0) + input_tokens + output_tokens
            await session.commit()
