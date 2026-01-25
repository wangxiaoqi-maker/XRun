"""
XRun - AI 驱动的自动化测试平台
FastAPI 后端主文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

# 导入各个模块的路由
from apps.ui_automation.api import devices, cases, execution, ai_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    print("🚀 XRun 后端服务启动中...")

    # 初始化数据库
    from apps.ui_automation.database import init_db
    await init_db()

    # 创建必要目录
    os.makedirs("../data/screenshots", exist_ok=True)
    os.makedirs("../data/reports", exist_ok=True)
    os.makedirs("../data/logs", exist_ok=True)

    # 启动 iOS 设备监听服务（后台任务，不阻塞启动）
    import asyncio
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

    print("✅ XRun 后端服务启动成功")

    yield

    # 关闭时
    if ios_startup_task:
        ios_startup_task.cancel()
    if ios_service:
        await ios_service.stop()
        print("✓ iOS 设备监听服务已停止")

    print("👋 XRun 后端服务关闭")

app = FastAPI(
    title="XRun - AI 驱动的自动化测试平台",
    description="支持 UI 自动化、API 测试、Web 自动化的一站式测试平台",
    version="2.0.0",
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

# 路由 - UI 自动化模块
app.include_router(devices.router, prefix="/api/devices", tags=["设备管理"])
app.include_router(cases.router, prefix="/api/cases", tags=["用例管理"])
app.include_router(execution.router, prefix="/api/execution", tags=["用例执行"])
app.include_router(ai_config.router, prefix="/api/ai-config", tags=["AI配置"])

# 静态文件
os.makedirs("../data", exist_ok=True)
app.mount("/data", StaticFiles(directory="../data"), name="data")

@app.get("/")
async def root():
    return {
        "name": "XRun - AI 驱动的自动化测试平台",
        "version": "2.0.0",
        "modules": ["UI 自动化", "API 测试", "Web 自动化"],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
