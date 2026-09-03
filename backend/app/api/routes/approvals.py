from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.approvals.human_approval import ApprovalNotFoundError, approve, list_pending, reject

router = APIRouter(prefix="/approvals", tags=["approvals"])


class DecisionBody(BaseModel):
    approver: str
    reason: str | None = None


@router.get("")
async def get_pending():
    return await list_pending()


@router.post("/{approval_id}/approve")
async def approve_action(approval_id: str, body: DecisionBody):
    try:
        return await approve(approval_id, approver=body.approver)
    except ApprovalNotFoundError:
        raise HTTPException(status_code=404, detail="Approval not found")


@router.post("/{approval_id}/reject")
async def reject_action(approval_id: str, body: DecisionBody):
    try:
        return await reject(approval_id, approver=body.approver, reason=body.reason or "")
    except ApprovalNotFoundError:
        raise HTTPException(status_code=404, detail="Approval not found")
