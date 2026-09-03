"""
Builds the single "auditable evidence record with source lineage" that the
deck's Layer 1 promises. This is the ONLY object agents are ever allowed to
see (via app/agents/tools/evidence_tools.py) — never the raw adapters.

Flow (mirrors slide 5):
  1. NWSAdapter defines the event polygon + time window.
  2. USGS / HCFCD / TranStar / FEMA adapters corroborate within that window/bbox.
  3. build_event_bundle() joins everything into one EvidenceRecord and stamps
     an event_id (issued by the /events route — see slide 5 step 3: "FastAPI
     issues an event_id").
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.evidence.adapters.base import SourceAdapter, SourceRecord
from app.evidence.adapters.fema_adapter import FEMAAdapter
from app.evidence.adapters.hcfcd_gauge_adapter import HCFCDGaugeAdapter
from app.evidence.adapters.nws_adapter import NWSAdapter
from app.evidence.adapters.transtar_adapter import TranStarAdapter
from app.evidence.adapters.usgs_gauge_adapter import USGSGaugeAdapter
from app.evidence.lineage import LineageEntry, build_lineage


class EvidenceRecord(BaseModel):
    event_id: str
    created_at: datetime
    event_window: tuple[datetime, datetime]
    bbox: dict
    sources: dict[str, list[dict]]      # source_name -> [SourceRecord as dict]
    lineage: list[LineageEntry]
    # populated later, after the vision NIM call attaches confidence:
    vision_confidence: float | None = None
    vision_lineage_ref: str | None = None


DEFAULT_ADAPTERS: list[SourceAdapter] = [
    NWSAdapter(mode="replay"),
    USGSGaugeAdapter(mode="replay"),
    HCFCDGaugeAdapter(mode="replay"),
    TranStarAdapter(mode="replay"),
    FEMAAdapter(mode="replay"),
]


async def build_event_bundle(
    *,
    event_window: tuple[datetime, datetime],
    bbox: dict,
    adapters: list[SourceAdapter] | None = None,
) -> EvidenceRecord:
    adapters = adapters or DEFAULT_ADAPTERS
    sources: dict[str, list[SourceRecord]] = {}
    for adapter in adapters:
        sources[adapter.source_name] = await adapter.fetch(event_window=event_window, bbox=bbox)

    lineage = build_lineage(sources)

    return EvidenceRecord(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        created_at=datetime.utcnow(),
        event_window=event_window,
        bbox=bbox,
        sources={name: [_source_record_to_json(r) for r in records] for name, records in sources.items()},
        lineage=lineage,
    )


def _source_record_to_json(record: SourceRecord) -> dict:
    """SourceRecord.__dict__ contains raw datetime objects, which aren't
    JSON-serializable -- this was caught by actually trying to persist a
    record (SQLAlchemy's JSON column raised TypeError), not by inspection.
    Converts to ISO strings so it can round-trip through the JSON column."""
    data = dict(record.__dict__)
    data["fetched_at"] = record.fetched_at.isoformat()
    data["observed_at"] = record.observed_at.isoformat()
    return data
