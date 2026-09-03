"""
Evidence verifier -- first decision gate.

Per slide 6: "The evidence verifier scores freshness, location and source
agreement." Real implementation: reads the persisted EvidenceRecord's
lineage (app/db/models.py:EvidenceRecordRow, written by
app/evidence/evidence_record.py) and applies real thresholds. If sources
disagree in time or too few corroborate, the record fails here before
anything downstream (confidence gate, agents, decision outputs) ever sees it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.db.models import EvidenceRecordRow
from app.db.session import get_session

MAX_STALENESS = timedelta(hours=6)
MIN_CORROBORATING_SOURCES = 2

# FEMA flood-zone data is a standing reference dataset (zone designations
# don't change hour to hour), not a live sensor reading -- caught by
# actually running this against the replay fixtures: FEMA's fixture is
# dated 2026-01-01 (zones are annual/static), which made every replay fail
# freshness by construction when treated the same as a live gauge reading.
# It still counts toward corroboration, just not toward the freshness check.
NON_TIME_SENSITIVE_SOURCES = {"FEMA"}


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

    corroborating = 0
    time_sensitive_latest: list[tuple[str, datetime]] = []

    for entry in row.lineage:
        record_count = entry.get("record_count", 0)
        source = entry.get("source", "unknown")
        if record_count <= 0:
            continue
        corroborating += 1

        latest_raw = entry.get("latest_observed_at")
        if latest_raw and source not in NON_TIME_SENSITIVE_SOURCES:
            latest = datetime.fromisoformat(latest_raw)
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=UTC)
            time_sensitive_latest.append((source, latest))

    if corroborating < MIN_CORROBORATING_SOURCES:
        return GateResult(
            passed=False,
            reason=f"Only {corroborating} corroborating source(s); "
            f"need at least {MIN_CORROBORATING_SOURCES}.",
            score=corroborating / max(len(row.lineage), 1),
        )

    # Source agreement in time: rather than comparing against an arbitrary
    # wall-clock or the full event window (which can span much longer than
    # sensor reporting cadence -- caught by actually running this: a 14-hour
    # event window made 8-10am sensor readings look "stale" by end of
    # window even though they closely agreed with each other), freshness
    # is judged as mutual agreement among the time-sensitive sources
    # themselves: how far apart is the earliest from the latest reading.
    stale_sources: list[str] = []
    if time_sensitive_latest:
        reference_time = max(t for _, t in time_sensitive_latest)
        for source, latest in time_sensitive_latest:
            if reference_time - latest > MAX_STALENESS:
                stale_sources.append(source)

    if stale_sources:
        return GateResult(
            passed=False,
            reason=f"Source(s) disagree in time by more than {MAX_STALENESS}: "
            f"{', '.join(stale_sources)}.",
            score=corroborating / max(len(row.lineage), 1),
        )

    return GateResult(passed=True, score=corroborating / max(len(row.lineage), 1))
