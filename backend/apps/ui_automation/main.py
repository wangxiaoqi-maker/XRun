"""
UI 自动化平台 - FastAPI 后端
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from apps.ui_automation.api import devices, cases, execution, ai_config
from apps.ui_automation.database import init_db
from apps.ui_automation.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    import asyncio
    
    # 启动时
    await init_db()
    
    # 创建必要目录
    os.makedirs("static/screenshots", exist_ok=True)
    os.makedirs("static/reports", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # 启动 iOS 设备监听服务（后台任务，不阻塞启动）
    ios_service = None
    ios_startup_task = None
    
    async def start_ios_service():
        nonlocal ios_service
        try:
            from apps.ui_automation.services.ios_device_service import ios_device_service
            ios_service = ios_device_service
            # 仅扫描设备，不阻塞等待 WDA
            await ios_service._scan_devices()
            # 启动后台监听
            ios_service._running = True
            ios_service._watch_task = asyncio.create_task(ios_service._watch_devices())
            print("✓ iOS 设备监听服务已启动")
        except Exception as e:
            print(f"⚠ iOS 设备监听服务启动失败: {e}")
    
    # 后台启动 iOS 服务
    ios_startup_task = asyncio.create_task(start_ios_service())
    
    yield
    
    # 关闭时
    if ios_startup_task:
        ios_startup_task.cancel()
    if ios_service:
        await ios_service.stop()
        print("✓ iOS 设备监听服务已停止")

app = FastAPI(
    title="UI 自动化平台",
    description="基于 Midscene AI 的 iOS/Android UI 自动化测试平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(devices.router, prefix="/api/devices", tags=["设备管理"])
app.include_router(cases.router, prefix="/api/cases", tags=["用例管理"])
app.include_router(execution.router, prefix="/api/execution", tags=["用例执行"])
app.include_router(ai_config.router, prefix="/api/ai-config", tags=["AI配置"])

# 静态文件
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {
        "name": "UI 自动化平台",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
