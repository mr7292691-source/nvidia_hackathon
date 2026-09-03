"""
Evidence verifier -- first decision gate.

Per slide 6: "The evidence verifier scores freshness, location and source
agreement." Real implementation: reads the persisted EvidenceRecord's
lineage (app/db/models.py:EvidenceRecordRow, written by
app/evidence/evidence_record.py) and applies real thresholds. If sources
are stale or too few corroborate, the record fails here before anything
downstream (confidence gate, agents, decision outputs) ever sees it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.models import EvidenceRecordRow
from app.db.session import get_session

MAX_STALENESS = timedelta(hours=6)
MIN_CORROBORATING_SOURCES = 2


@dataclass
class GateResult:
    passed: bool
    reason: str = ""
    score: float | None = None


async def evidence_verifier_check(
    *, event_id: str | None, tool_name: str | None = None, args: dict | None = None
) -> GateResult:
    if not event_id:
        return GateResult(passed=False, reason="No event_id provided -- cannot verify evidence.")

    async with get_session() as session:
        row = await session.get(EvidenceRecordRow, event_id)

    if row is None:
        return GateResult(passed=False, reason=f"No evidence record found for event_id={event_id}.")

    # Freshness is judged relative to the event's OWN time window, not real
    # wall-clock time -- this is a replay of a historical/synthetic
    # scenario (deck slide 5: "Illustrative synthetic scenario"), so
    # comparing a June 2026 fixture's timestamps against September 2026
    # wall-clock time would make every replay fail freshness by
    # construction. The event's window_end is the simulated "now" within
    # the scenario being replayed.
    simulated_now = row.window_end
    if simulated_now.tzinfo is None:
        simulated_now = simulated_now.replace(tzinfo=timezone.utc)

    corroborating = 0
    stale_sources: list[str] = []

    for entry in row.lineage:
        record_count = entry.get("record_count", 0)
        latest_raw = entry.get("latest_observed_at")
        if record_count <= 0:
            continue
        corroborating += 1
        if latest_raw:
            latest = datetime.fromisoformat(latest_raw)
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=timezone.utc)
            if simulated_now - latest > MAX_STALENESS:
                stale_sources.append(entry.get("source", "unknown"))

    if stale_sources:
        return GateResult(
            passed=False,
            reason=f"Stale evidence from source(s): {', '.join(stale_sources)} "
            f"(older than {MAX_STALENESS}).",
            score=corroborating / max(len(row.lineage), 1),
        )

    if corroborating < MIN_CORROBORATING_SOURCES:
        return GateResult(
            passed=False,
            reason=f"Only {corroborating} corroborating source(s); "
            f"need at least {MIN_CORROBORATING_SOURCES}.",
            score=corroborating / max(len(row.lineage), 1),
        )

    return GateResult(passed=True, score=corroborating / max(len(row.lineage), 1))
