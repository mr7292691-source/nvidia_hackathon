from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ApprovalDecisionRequest(BaseModel):
    approver: str
    reason: str | None = None


class ApprovalRecord(BaseModel):
    approval_id: str
    event_id: str
    proposed_action: dict
    status: Literal["pending", "approved", "rejected"]
    approver: str | None = None
    reason: str | None = None
