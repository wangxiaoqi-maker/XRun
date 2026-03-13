from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TcgConversation, TcgConversationMessage, generate_uuid, now_beijing


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Conversation CRUD ──

    async def create(self, **kwargs) -> TcgConversation:
        conv = TcgConversation(**kwargs)
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_by_id(self, conv_id: str) -> Optional[TcgConversation]:
        result = await self.db.execute(
            select(TcgConversation).where(TcgConversation.id == conv_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str, limit: int = 50) -> List[TcgConversation]:
        result = await self.db.execute(
            select(TcgConversation)
            .where(TcgConversation.project_id == project_id)
            .order_by(TcgConversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_title(self, conv_id: str, title: str):
        await self.db.execute(
            update(TcgConversation)
            .where(TcgConversation.id == conv_id)
            .values(title=title, updated_at=now_beijing())
        )
        await self.db.commit()

    async def update_config(self, conv_id: str, config: dict):
        await self.db.execute(
            update(TcgConversation)
            .where(TcgConversation.id == conv_id)
            .values(config=config, updated_at=now_beijing())
        )
        await self.db.commit()

    async def touch(self, conv_id: str):
        """Update updated_at to reflect recent activity."""
        await self.db.execute(
            update(TcgConversation)
            .where(TcgConversation.id == conv_id)
            .values(updated_at=now_beijing())
        )
        await self.db.commit()

    async def delete(self, conv_id: str):
        conv = await self.get_by_id(conv_id)
        if conv:
            await self.db.delete(conv)
            await self.db.commit()

    # ── Messages ──

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: dict = None,
    ) -> TcgConversationMessage:
        msg = TcgConversationMessage(
            id=generate_uuid(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_=metadata or {},
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_messages(
        self, conversation_id: str, limit: int = 200
    ) -> List[TcgConversationMessage]:
        result = await self.db.execute(
            select(TcgConversationMessage)
            .where(TcgConversationMessage.conversation_id == conversation_id)
            .order_by(TcgConversationMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def message_count(self, conversation_id: str) -> int:
        result = await self.db.execute(
            select(func.count(TcgConversationMessage.id))
            .where(TcgConversationMessage.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    async def delete_messages(self, conversation_id: str):
        msgs = await self.get_messages(conversation_id, limit=10000)
        for m in msgs:
            await self.db.delete(m)
        await self.db.commit()
