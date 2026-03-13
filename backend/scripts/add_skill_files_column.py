"""数据库迁移 - 给 skill 表添加 files JSON 字段"""
import asyncio
import os
from sqlalchemy import text
from pathlib import Path

env_file = Path(__file__).parent.parent.parent / ".Env"
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

        if is_mysql:
            result = await conn.execute(text("SHOW COLUMNS FROM skill LIKE 'files'"))
            if not result.fetchone():
                await conn.execute(text("ALTER TABLE skill ADD COLUMN files JSON"))
                print("✅ skill.files 字段添加成功")
            else:
                print("ℹ️ skill.files 字段已存在")
        else:
            tables = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='skill'"))
            if not tables.fetchone():
                print("ℹ️ skill 表不存在，应用启动时会自动创建（含 files 列）")
                return
            columns_result = await conn.execute(text("PRAGMA table_info(skill)"))
            columns = [row[1] for row in columns_result.fetchall()]
            if 'files' not in columns:
                await conn.execute(text("ALTER TABLE skill ADD COLUMN files TEXT DEFAULT '[]'"))
                print("✅ skill.files 字段添加成功")
            else:
                print("ℹ️ skill.files 字段已存在")

    print("✅ 迁移完成")


if __name__ == "__main__":
    asyncio.run(migrate())
