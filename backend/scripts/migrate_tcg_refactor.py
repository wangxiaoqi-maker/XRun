"""
TCG 多智能体重构 — 数据库迁移脚本

执行方式：cd backend && python scripts/migrate_tcg_refactor.py

变更内容：
1. tcg_test_case: session_id → conversation_id（保留旧列，新增列并复制数据）
2. llm_providers: 新增 litellm_prefix 列
3. tcg_review_record: 新增 conversation_id / review_round / rejected_ids 列
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
    # ── tcg_test_case: 新增 conversation_id ──
    {
        "check": "SELECT 1 FROM information_schema.columns WHERE table_name='tcg_test_case' AND column_name='conversation_id'",
        "sql": "ALTER TABLE tcg_test_case ADD COLUMN conversation_id VARCHAR(36) DEFAULT NULL",
        "desc": "tcg_test_case: 添加 conversation_id 列",
    },
    {
        "check": None,
        "sql": "UPDATE tcg_test_case SET conversation_id = session_id WHERE conversation_id IS NULL AND session_id IS NOT NULL",
        "desc": "tcg_test_case: 将 session_id 数据复制到 conversation_id",
    },
    {
        "check": "SELECT 1 FROM information_schema.statistics WHERE table_name='tcg_test_case' AND index_name='ix_tcg_test_case_conversation_id'",
        "sql": "CREATE INDEX ix_tcg_test_case_conversation_id ON tcg_test_case(conversation_id)",
        "desc": "tcg_test_case: 创建 conversation_id 索引",
    },

    # ── llm_providers: 新增 litellm_prefix ──
    {
        "check": "SELECT 1 FROM information_schema.columns WHERE table_name='llm_providers' AND column_name='litellm_prefix'",
        "sql": "ALTER TABLE llm_providers ADD COLUMN litellm_prefix VARCHAR(50) DEFAULT 'openai'",
        "desc": "llm_providers: 添加 litellm_prefix 列",
    },

    # ── tcg_review_record: 新增字段 ──
    {
        "check": "SELECT 1 FROM information_schema.columns WHERE table_name='tcg_review_record' AND column_name='conversation_id'",
        "sql": "ALTER TABLE tcg_review_record ADD COLUMN conversation_id VARCHAR(36) DEFAULT NULL",
        "desc": "tcg_review_record: 添加 conversation_id 列",
    },
    {
        "check": "SELECT 1 FROM information_schema.columns WHERE table_name='tcg_review_record' AND column_name='review_round'",
        "sql": "ALTER TABLE tcg_review_record ADD COLUMN review_round INT DEFAULT 1",
        "desc": "tcg_review_record: 添加 review_round 列",
    },
    {
        "check": "SELECT 1 FROM information_schema.columns WHERE table_name='tcg_review_record' AND column_name='rejected_ids'",
        "sql": "ALTER TABLE tcg_review_record ADD COLUMN rejected_ids JSON DEFAULT NULL",
        "desc": "tcg_review_record: 添加 rejected_ids 列",
    },
]


async def run_migrations():
    async with engine.begin() as conn:
        for m in MIGRATIONS:
            desc = m["desc"]

            if m.get("check"):
                result = await conn.execute(text(m["check"]))
                if result.fetchone():
                    print(f"  跳过（已存在）: {desc}")
                    continue

            try:
                await conn.execute(text(m["sql"]))
                print(f"  ✓ {desc}")
            except Exception as e:
                err = str(e)
                if "Duplicate" in err or "already exists" in err:
                    print(f"  跳过（已存在）: {desc}")
                else:
                    print(f"  ✗ {desc}: {e}")


async def main():
    print("TCG 多智能体重构 — 数据库迁移")
    print("=" * 50)
    await run_migrations()
    print("=" * 50)
    print("迁移完成")


if __name__ == "__main__":
    asyncio.run(main())
