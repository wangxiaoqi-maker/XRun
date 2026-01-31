#!/usr/bin/env python3
"""
SQLite 到 MySQL 数据迁移脚本

将本地 SQLite 数据迁移到云端 MySQL
"""
import asyncio
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv("../.Env")

from loguru import logger


# SQLite 数据库路径
SQLITE_PATH = "data/app.db"

# 需要迁移的表（按依赖顺序）
TABLES_TO_MIGRATE = [
    # LLM 配置
    ("llm_providers", "id"),
    ("llm_models", "id"),
    ("llm_usage_logs", "id"),
    
    # 知识库
    ("kb_app_info", "id"),
    ("kb_page_analysis", "id"),
    ("kb_page_element", "id"),
    ("kb_element_relation", "id"),
    ("kb_page_transition", "id"),
    
    # 测试用例
    ("test_cases", "id"),
    ("executions", "id"),
]


def get_sqlite_data(table_name: str):
    """从 SQLite 读取数据"""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            return [], []
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        
        # 转换为字典列表
        data = [dict(row) for row in rows]
        
        return columns, data
    except sqlite3.OperationalError as e:
        logger.warning(f"表 {table_name} 不存在或无法读取: {e}")
        return [], []
    finally:
        conn.close()


async def migrate_table(table_name: str, pk_column: str):
    """迁移单个表"""
    from apps.ui_automation.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    
    columns, data = get_sqlite_data(table_name)
    
    if not data:
        logger.info(f"  {table_name}: 无数据，跳过")
        return 0
    
    logger.info(f"  {table_name}: {len(data)} 条记录")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    migrated = 0
    skipped = 0
    
    async with engine.begin() as conn:
        for row in data:
            try:
                # 检查是否已存在
                pk_value = row.get(pk_column)
                if pk_value:
                    check_sql = text(f"SELECT 1 FROM {table_name} WHERE {pk_column} = :pk")
                    result = await conn.execute(check_sql, {"pk": pk_value})
                    if result.fetchone():
                        skipped += 1
                        continue
                
                # 构建插入语句
                cols = ", ".join(columns)
                placeholders = ", ".join([f":{c}" for c in columns])
                insert_sql = text(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})")
                
                # 处理 None 值和特殊类型
                clean_row = {}
                for k, v in row.items():
                    if isinstance(v, bytes):
                        v = v.decode('utf-8', errors='ignore')
                    clean_row[k] = v
                
                await conn.execute(insert_sql, clean_row)
                migrated += 1
                
            except Exception as e:
                logger.warning(f"    插入失败 ({pk_value}): {e}")
    
    await engine.dispose()
    
    if skipped > 0:
        logger.info(f"    迁移: {migrated}, 跳过(已存在): {skipped}")
    
    return migrated


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 SQLite → MySQL 数据迁移")
    logger.info("=" * 60)
    
    # 检查 SQLite 文件
    if not os.path.exists(SQLITE_PATH):
        logger.error(f"❌ SQLite 文件不存在: {SQLITE_PATH}")
        return
    
    logger.info(f"源数据库: {SQLITE_PATH}")
    
    from apps.ui_automation.config import settings
    logger.info(f"目标数据库: {settings.DATABASE_URL[:50]}...")
    
    logger.info("")
    logger.info("开始迁移...")
    
    total_migrated = 0
    
    for table_name, pk_column in TABLES_TO_MIGRATE:
        try:
            count = await migrate_table(table_name, pk_column)
            total_migrated += count
        except Exception as e:
            logger.error(f"  {table_name}: 迁移失败 - {e}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"✅ 迁移完成! 共迁移 {total_migrated} 条记录")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
