"""
数据库迁移脚本 - 添加 creator 字段到 tcg_test_case 表
支持 SQLite 和 MySQL
"""
import asyncio
import os
from sqlalchemy import text, inspect

# 加载.env配置
from pathlib import Path
env_file = Path(__file__).parent.parent / ".Env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key] = val

from apps.ui_automation.database import engine


async def migrate():
    async with engine.begin() as conn:
        is_mysql = 'mysql' in str(engine.url).lower()
        print(f"检测到数据库类型: {'MySQL' if is_mysql else 'SQLite'}")
        
        if is_mysql:
            # MySQL 语法
            try:
                result = await conn.execute(text("SHOW COLUMNS FROM tcg_test_case LIKE 'creator'"))
                exists = result.fetchone()
                if not exists:
                    await conn.execute(text("ALTER TABLE tcg_test_case ADD COLUMN creator VARCHAR(100)"))
                    print("✅ 字段 creator 添加成功")
                else:
                    print("ℹ️ 字段 creator 已存在")
            except Exception as e:
                print(f"tcg_test_case表操作: {e}")
            
            try:
                result = await conn.execute(text("SHOW COLUMNS FROM tcg_export_template LIKE 'project_id'"))
                exists = result.fetchone()
                if not exists:
                    await conn.execute(text("ALTER TABLE tcg_export_template ADD COLUMN project_id VARCHAR(36)"))
                    print("✅ 字段 project_id 添加成功")
                else:
                    print("ℹ️ 字段 project_id 已存在")
            except Exception as e:
                print(f"tcg_export_template表操作: {e}")
        else:
            # SQLite 语法
            inspector = inspect(conn.sync_connection)
            tables = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            table_names = [row[0] for row in tables.fetchall()]
            print(f"现有表: {table_names}")
            
            if 'tcg_test_case' in table_names:
                columns = [col['name'] for col in inspector.get_columns('tcg_test_case')]
                if 'creator' not in columns:
                    await conn.execute(text("ALTER TABLE tcg_test_case ADD COLUMN creator VARCHAR(100)"))
                    print("✅ 字段 creator 添加成功")
                else:
                    print("ℹ️ 字段 creator 已存在")
            else:
                print("⚠️ tcg_test_case 表不存在（将在应用启动时自动创建）")
                
            if 'tcg_export_template' in table_names:
                columns = [col['name'] for col in inspector.get_columns('tcg_export_template')]
                if 'project_id' not in columns:
                    await conn.execute(text("ALTER TABLE tcg_export_template ADD COLUMN project_id VARCHAR(36)"))
                    print("✅ 字段 project_id 添加成功")
                else:
                    print("ℹ️ 字段 project_id 已存在")
            
        print("✅ 迁移完成")


if __name__ == "__main__":
    asyncio.run(migrate())