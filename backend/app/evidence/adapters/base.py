"""
Common interface for every evidence source (NWS, USGS, HCFCD, TranStar, FEMA).

Guardrail this enforces: agents never touch these adapters directly. Adapters
are called only by app/evidence/evidence_record.py, which produces validated,
lineage-stamped EvidenceRecord objects. Agents only ever see EvidenceRecords
through app/agents/tools/evidence_tools.py.

Each adapter can run in two modes, chosen by SourceAdapter.mode:
  - "replay": reads from app/evidence/adapters/replay/*.json (today's build)
  - "live":   calls the real upstream endpoint (future, once access is
              coordinated — the deck flags TranStar live access explicitly
              as a to-be-approved blocker)
Swapping modes must never change the shape of the returned SourceRecord.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class SourceRecord:
    source: str                       # e.g. "NWS", "USGS", "HCFCD", "TranStar", "FEMA"
    fetched_at: datetime
    observed_at: datetime
    location: dict[str, Any]          # geojson point/polygon
    payload: dict[str, Any]           # raw-but-typed source-specific fields
    confidence_hint: float | None = None
    raw_source_url: str | None = None  # populated only in "live" mode, for lineage
    extra: dict[str, Any] = field(default_factory=dict)


class SourceAdapter(abc.ABC):
    source_name: str
    mode: Literal["replay", "live"] = "replay"

    @abc.abstractmethod
    async def fetch(self, *, event_window: tuple[datetime, datetime],
                     bbox: dict[str, Any]) -> list[SourceRecord]:
        """Return all records for this source relevant to the event window/bbox."""
        raise NotImplementedError
