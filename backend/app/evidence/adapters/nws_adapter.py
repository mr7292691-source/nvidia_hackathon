"""
NWS alerts adapter. Slide 5 demo step 1: "NWS alert with heavy-rain forecast
defines the event polygon and time window" — this adapter is the entry point
that establishes the official event.

Live mode target: https://api.weather.gov/alerts (no key required).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.evidence.adapters.base import SourceAdapter, SourceRecord

REPLAY_FIXTURE = Path(__file__).parent / "replay" / "nws_sample.json"


class NWSAdapter(SourceAdapter):
    source_name = "NWS"

    def __init__(self, mode: str = "replay"):
        self.mode = mode  # type: ignore[assignment]

    async def fetch(self, *, event_window: tuple[datetime, datetime],
                     bbox: dict[str, Any]) -> list[SourceRecord]:
        if self.mode == "replay":
            return self._load_replay()
        raise NotImplementedError(
            "Live NWS polling not wired yet — see README 'Environments'. "
            "api.weather.gov/alerts requires no key; TODO once approved."
        )

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
