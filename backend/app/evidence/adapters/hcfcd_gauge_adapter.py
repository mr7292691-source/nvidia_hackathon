"""
Harris County Flood Control District (HCFCD) gauge adapter — Houston-specific
corroborating signal, paired with USGS gauges per slide 5 step 2.

Live mode target: HCFCD's public gauge data feed (access coordination TBD,
same category of blocker the deck calls out for TranStar).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.evidence.adapters.base import SourceAdapter, SourceRecord

REPLAY_FIXTURE = Path(__file__).parent / "replay" / "hcfcd_sample.json"


class HCFCDGaugeAdapter(SourceAdapter):
    source_name = "HCFCD"

    def __init__(self, mode: str = "replay"):
        self.mode = mode  # type: ignore[assignment]

    async def fetch(self, *, event_window: tuple[datetime, datetime],
                     bbox: dict[str, Any]) -> list[SourceRecord]:
        if self.mode == "replay":
            return self._load_replay()
        raise NotImplementedError("Live HCFCD feed not wired yet — pending access coordination.")

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
