"""ReviewRecordRepository — 审核记录数据访问"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TcgReviewRecord, generate_uuid


class ReviewRecordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        conversation_id: str,
        review_type: str,
        review_status: str,
        reviewer: str = "",
        comment: str = "",
        review_round: int = 1,
        rejected_ids: list[str] = None,
        case_id: str = None,
    ) -> TcgReviewRecord:
        record = TcgReviewRecord(
            id=generate_uuid(),
            conversation_id=conversation_id,
            case_id=case_id or "",
            review_type=review_type,
            review_status=review_status,
            reviewer=reviewer,
            comment=comment,
            review_round=review_round,
            rejected_ids=rejected_ids or [],
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_by_conversation(
        self, conversation_id: str, review_type: str = None,
    ) -> list[TcgReviewRecord]:
        stmt = select(TcgReviewRecord).where(
            TcgReviewRecord.conversation_id == conversation_id
        )
        if review_type:
            stmt = stmt.where(TcgReviewRecord.review_type == review_type)
        stmt = stmt.order_by(TcgReviewRecord.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_case(self, case_id: str) -> list[TcgReviewRecord]:
        stmt = (
            select(TcgReviewRecord)
            .where(TcgReviewRecord.case_id == case_id)
            .order_by(TcgReviewRecord.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
