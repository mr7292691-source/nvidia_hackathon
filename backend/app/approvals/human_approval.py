"""
Final gate before either decision output is treated as actionable. Per
slide 3 guardrail: "no operational action leaves the system without a
passed gate" -- human approval is the last of those gates, deliberately not
automatable. Real DB-backed, not the in-memory dict this used to be.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.models import ApprovalRow
from app.db.session import get_session


class ApprovalNotFoundError(Exception):
    pass


async def approve(approval_id: str, *, approver: str) -> dict:
    async with get_session() as session:
        row = await session.get(ApprovalRow, approval_id)
        if row is None:
            raise ApprovalNotFoundError(approval_id)
        row.status = "approved"
        row.approver = approver
        await session.commit()
        return _row_to_dict(row)


async def reject(approval_id: str, *, approver: str, reason: str) -> dict:
    async with get_session() as session:
        row = await session.get(ApprovalRow, approval_id)
        if row is None:
            raise ApprovalNotFoundError(approval_id)
        row.status = "rejected"
        row.approver = approver
        row.reason = reason
        await session.commit()
        return _row_to_dict(row)


async def list_pending() -> list[dict]:
    async with get_session() as session:
        result = await session.execute(select(ApprovalRow).where(ApprovalRow.status == "pending"))
        return [_row_to_dict(row) for row in result.scalars().all()]


def _row_to_dict(row: ApprovalRow) -> dict:
    return {
        "approval_id": row.approval_id,
        "event_id": row.event_id,
        "proposed_action": row.proposed_action,
        "status": row.status,
        "approver": row.approver,
        "reason": row.reason,
    }
