"""
LLMModel 新增 context_window 列

执行方式：cd backend && python scripts/add_context_window_column.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv("../.Env")

from sqlalchemy import text
from apps.ui_automation.database import engine

MIGRATIONS = [
    {
        "check": "SELECT 1 FROM information_schema.columns WHERE table_name='llm_models' AND column_name='context_window'",
        "sql": "ALTER TABLE llm_models ADD COLUMN context_window INT DEFAULT 32768 COMMENT '上下文窗口大小(tokens)'",
        "desc": "llm_models: 添加 context_window 列",
    },
]


async def run():
    async with engine.begin() as conn:
        for m in MIGRATIONS:
            row = (await conn.execute(text(m["check"]))).first()
            if row:
                print(f"  [跳过] {m['desc']}（已存在）")
            else:
                await conn.execute(text(m["sql"]))
                print(f"  [执行] {m['desc']}")
    print("迁移完成")


if __name__ == "__main__":
    asyncio.run(run())
