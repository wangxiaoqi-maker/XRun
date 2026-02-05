"""
XRun - AI 驱动的自动化测试平台
FastAPI 后端主文件
"""
# 加载环境变量（必须在其他导入之前）
from dotenv import load_dotenv
load_dotenv("../.Env")  # 加载项目根目录的 .Env 文件

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

# 导入各个模块的路由
from apps.ui_automation.api import devices, cases, execution, ai_config, llm_config, auth, project
from apps.ui_automation.api import app as app_router
from apps.ui_automation.knowledge.api import router as knowledge_router
from apps.ui_automation.knowledge.api import exploration_router
from apps.ui_automation.knowledge.api import module_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    print("🚀 XRun 后端服务启动中...")
    
    # 初始化 Redis（多进程数据共享）
    from apps.ui_automation.services.redis_service import init_redis, close_redis
    from apps.ui_automation.config import settings
    await init_redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD
    )

    # 初始化数据库（主应用）
    from apps.ui_automation.database import init_db, engine
    await init_db()
    
    # 初始化知识库数据库表
    from apps.ui_automation.knowledge.models import KnowledgeBase
    async with engine.begin() as conn:
        await conn.run_sync(KnowledgeBase.metadata.create_all)
    print("✓ 知识库数据表初始化完成")
    
    # 初始化 LLM 配置表、用户表、项目表和应用表
    from apps.ui_automation.models.llm_config import LLMProvider, LLMModel, LLMUsageLog
    from apps.ui_automation.models.user import User
    from apps.ui_automation.models.project import Project, ProjectMember
    from apps.ui_automation.models.app import App
    from apps.ui_automation.database import Base as MainBase
    async with engine.begin() as conn:
        await conn.run_sync(MainBase.metadata.create_all)
    print("✓ 数据表初始化完成")
    
    # 初始化执行引擎数据库表
    from apps.ui_automation.execution.models import (
        TestCaseV2, ExecutionConfig, DataSet, 
        ExecutionRecord, GlobalVariable, CacheConfig
    )
    async with engine.begin() as conn:
        await conn.run_sync(MainBase.metadata.create_all)
    print("✓ 执行引擎数据表初始化完成")
    
    # 初始化管理员账号
    from apps.ui_automation.database import AsyncSessionLocal
    from apps.ui_automation.services.auth_service import AuthService
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        await auth_service.init_admin_user()
    print("✓ 用户认证模块初始化完成")

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
    
    # 关闭 Redis 连接
    await close_redis()
    print("✓ Redis 连接已关闭")

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

# 路由 - 认证模块
app.include_router(auth.router, prefix="/api", tags=["认证"])

# 路由 - 项目管理模块
app.include_router(project.router, prefix="/api", tags=["项目管理"])

# 路由 - 应用管理模块
app.include_router(app_router.router, prefix="/api", tags=["应用管理"])

# 路由 - UI 自动化模块
app.include_router(devices.router, prefix="/api/devices", tags=["设备管理"])
app.include_router(cases.router, prefix="/api/cases", tags=["用例管理"])
app.include_router(execution.router, prefix="/api/execution", tags=["用例执行"])
app.include_router(ai_config.router, prefix="/api/ai-config", tags=["AI配置"])

# 路由 - AI 知识库模块
app.include_router(knowledge_router, prefix="/api/ai", tags=["AI教学模式"])
app.include_router(exploration_router, prefix="/api/knowledge", tags=["知识图谱探索"])
app.include_router(module_router, prefix="/api/knowledge", tags=["功能模块管理"])

# 路由 - LLM 配置模块
app.include_router(llm_config.router, prefix="/api", tags=["大模型配置"])

# 路由 - 执行引擎 V2 模块
from apps.ui_automation.execution.api import cases_router, config_router, execution_router, suites_router
app.include_router(cases_router, prefix="/api/v2", tags=["用例管理 V2"])
app.include_router(config_router, prefix="/api/v2", tags=["执行配置 V2"])
app.include_router(execution_router, prefix="/api/v2", tags=["执行管理 V2"])
app.include_router(suites_router, prefix="/api/v2", tags=["测试套件 V2"])

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
