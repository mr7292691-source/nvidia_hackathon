"""
FEMA flood-zone adapter. Supplies the flood-zone overlay used both for
evidence corroboration and for the insurer portfolio overlay in decisions/.

Live mode target: FEMA National Flood Hazard Layer (NFHL) public feed.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.evidence.adapters.base import SourceAdapter, SourceRecord

REPLAY_FIXTURE = Path(__file__).parent / "replay" / "fema_sample.json"


class FEMAAdapter(SourceAdapter):
    source_name = "FEMA"

    def __init__(self, mode: str = "replay"):
        self.mode = mode  # type: ignore[assignment]

    async def fetch(self, *, event_window: tuple[datetime, datetime],
                     bbox: dict[str, Any]) -> list[SourceRecord]:
        if self.mode == "replay":
            return self._load_replay()
        raise NotImplementedError("Live FEMA NFHL polling not wired yet.")

    def _load_replay(self) -> list[SourceRecord]:
        data = json.loads(REPLAY_FIXTURE.read_text())
        return [
            SourceRecord(
                source=self.source_name,
                fetched_at=datetime.utcnow(),
                observed_at=datetime.fromisoformat(item["observed_at"]),
                location=item["location"],
                payload=item["payload"],
                confidence_hint=item.get("confidence_hint"),
            )
            for item in data
        ]
