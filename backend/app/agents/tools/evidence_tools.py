"""
The ONLY tools agents may call to read evidence data. Deliberately thin:
no raw HTTP client, no adapter classes exposed here -- just lookups against
already-built EvidenceRecords. This file (plus portfolio_tools.py and
notify_tools.py) is the entire guardrail surface between the OpenShell-
sandboxed agents and the rest of the system.

Real SQLite-backed persistence (app/db/) -- replaces the in-memory dicts
that used to live here. Every write survives a process restart.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete

from app.db.models import EvidenceRecordRow, FieldImageRow
from app.db.session import get_session
from app.evidence.evidence_record import EvidenceRecord


async def register_event(record: EvidenceRecord) -> None:
    async with get_session() as session:
        row = EvidenceRecordRow(
            event_id=record.event_id,
            created_at=record.created_at,
            window_start=record.event_window[0],
            window_end=record.event_window[1],
            bbox=record.bbox,
            sources=record.sources,
            lineage=[entry.model_dump(mode="json") for entry in record.lineage],
            vision_confidence=record.vision_confidence,
            vision_lineage_ref=record.vision_lineage_ref,
        )
        await session.merge(row)
        await session.commit()


async def register_field_image(event_id: str, image_bytes: bytes) -> None:
    async with get_session() as session:
        row = FieldImageRow(event_id=event_id, image_bytes=image_bytes, uploaded_at=datetime.utcnow())
        await session.merge(row)
        await session.commit()


async def get_evidence_record(*, event_id: str) -> dict:
    async with get_session() as session:
        row = await session.get(EvidenceRecordRow, event_id)
        if row is None:
            return {"error": f"No evidence record for event_id={event_id}"}
        return {
            "event_id": row.event_id,
            "created_at": row.created_at.isoformat(),
            "event_window": [row.window_start.isoformat(), row.window_end.isoformat()],
            "bbox": row.bbox,
            "sources": row.sources,
            "lineage": row.lineage,
            "vision_confidence": row.vision_confidence,
            "vision_lineage_ref": row.vision_lineage_ref,
        }


async def get_field_image(*, event_id: str) -> bytes | None:
    async with get_session() as session:
        row = await session.get(FieldImageRow, event_id)
        return row.image_bytes if row else None


async def set_vision_confidence(*, event_id: str, confidence: float, lineage_ref: str) -> None:
    """Called by the vision specialist after a Relay-governed NIM call
    attaches a confidence score -- persists it onto the same evidence
    record so the confidence gate has a real number to threshold against."""
    async with get_session() as session:
        row = await session.get(EvidenceRecordRow, event_id)
        if row is None:
            return
        row.vision_confidence = confidence
        row.vision_lineage_ref = lineage_ref
        await session.commit()


async def _clear_all() -> None:
    """Test-only helper -- wipes evidence/field-image tables."""
    async with get_session() as session:
        await session.execute(delete(FieldImageRow))
        await session.execute(delete(EvidenceRecordRow))
        await session.commit()
