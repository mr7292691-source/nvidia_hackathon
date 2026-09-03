"""
Source lineage — the audit trail behind every evidence record. Every gate in
app/agents/gates/ reads this to score freshness/location/source-agreement
before anything is allowed to proceed (per slide 6: "The evidence verifier
scores freshness, location and source agreement; the confidence gate blocks
weak evidence").
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.evidence.adapters.base import SourceRecord


class LineageEntry(BaseModel):
    source: str
    record_count: int
    earliest_observed_at: datetime | None
    latest_observed_at: datetime | None
    mode: str  # "replay" | "live"


def build_lineage(sources: dict[str, list[SourceRecord]]) -> list[LineageEntry]:
    entries: list[LineageEntry] = []
    for source_name, records in sources.items():
        timestamps = [r.observed_at for r in records]
        entries.append(
            LineageEntry(
                source=source_name,
                record_count=len(records),
                earliest_observed_at=min(timestamps) if timestamps else None,
                latest_observed_at=max(timestamps) if timestamps else None,
                mode="replay",  # TODO: read from adapter.mode once live wiring lands
            )
        )
    return entries
