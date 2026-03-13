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
        echo=settings.SQL_ECHO,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
        pool_timeout=30,
        connect_args={
            "connect_timeout": 10,
            "init_command": "SET SESSION sort_buffer_size = 4194304",
        }
    )
else:
    # SQLite 配置（简化版，不需要连接池）
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.SQL_ECHO,
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
        if is_mysql:
            await _ensure_indexes(conn)


async def _ensure_indexes(conn):
    """补建模型中定义但数据库中缺失的索引"""
    from sqlalchemy import text
    indexes_to_check = [
        ("tcg_conversation", "ix_tcg_conv_proj_updated", "project_id, updated_at"),
    ]
    for table, idx_name, columns in indexes_to_check:
        result = await conn.execute(text(
            f"SELECT COUNT(*) FROM information_schema.STATISTICS "
            f"WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table}' AND INDEX_NAME = '{idx_name}'"
        ))
        if result.scalar() == 0:
            await conn.execute(text(f"CREATE INDEX {idx_name} ON {table} ({columns})"))
            print(f"  ✓ 补建索引: {idx_name} ON {table}({columns})")

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

