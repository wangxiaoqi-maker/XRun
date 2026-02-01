"""
数据库配置 - 高性能优化版

优化点：
1. 连接池配置：复用连接，减少连接开销
2. 连接回收：避免 MySQL 超时断开
3. Pre-ping：自动检测并重连失效连接
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from apps.ui_automation.config import settings
import os

# 确保数据目录存在
os.makedirs("data", exist_ok=True)

# 根据数据库类型选择配置
is_mysql = "mysql" in settings.DATABASE_URL.lower()

if is_mysql:
    # MySQL 配置（带连接池优化）
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        # ========== 连接池配置 ==========
        poolclass=AsyncAdaptedQueuePool,
        pool_size=10,              # 保持 10 个常驻连接
        max_overflow=20,           # 最多可扩展到 30 个连接
        pool_recycle=3600,         # 1小时回收连接（避免 MySQL wait_timeout）
        pool_pre_ping=True,        # 使用前检测连接是否有效
        pool_timeout=30,           # 获取连接超时时间
        connect_args={
            "connect_timeout": 10  # MySQL 连接超时 10 秒
        }
    )
else:
    # SQLite 配置（简化版，不需要连接池）
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool  # SQLite 不需要连接池
    )

# 创建会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 基类
Base = declarative_base()

async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session():
    """获取数据库会话（上下文管理器）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

