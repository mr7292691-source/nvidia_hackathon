"""
Agent-facing tool for requesting human approval. This is the ONLY way a
specialist's output can move toward becoming an "action" -- it never fires a
real notification/action itself, it only enqueues a request that a human
must approve via app/approvals/human_approval.py + the /approvals route.

Real SQLite-backed persistence -- survives a process restart, unlike the
in-memory dict this used to be.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.db.models import ApprovalRow
from app.db.session import get_session


async def request_human_approval(*, event_id: str, proposed_action: dict[str, Any]) -> str:
    approval_id = f"appr_{uuid.uuid4().hex[:12]}"
    async with get_session() as session:
        row = ApprovalRow(
            approval_id=approval_id,
            event_id=event_id,
            proposed_action=proposed_action,
            status="pending",
            created_at=datetime.utcnow(),
        )
        session.add(row)
        await session.commit()
    return approval_id
