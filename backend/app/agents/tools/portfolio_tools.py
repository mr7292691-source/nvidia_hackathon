"""
Agent-facing tool over the SYNTHETIC insurer portfolio only. Per slide 6:
"Use de-identified portfolio cohorts, field-level redaction and
insurer-controlled connectors" — this file is where that boundary is
enforced. No raw customer records are ever exposed here, and none should be
added later without a redaction step in front of them.
"""
from __future__ import annotations

import json
from pathlib import Path

FIXTURE = Path(__file__).parent.parent.parent / "evidence" / "adapters" / "replay" / "synthetic_portfolio.json"


async def get_policies_in_footprint(*, event_id: str) -> list[dict]:
    """
    Returns de-identified synthetic policies whose location falls inside the
    event's footprint. TODO: replace the "return everything" stub with a
    real point-in-polygon filter against the event's bbox once persistence
    for EvidenceRecord.bbox is wired through from evidence_tools.
    """
    if not FIXTURE.exists():
        return []
    return json.loads(FIXTURE.read_text())
