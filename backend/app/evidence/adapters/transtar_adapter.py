"""
TranStar roadway incident adapter. Slide 5 step 2: "TranStar flags flooded
roads." Slide 6 blocker: "Some TranStar live feeds require access
coordination" — response is to build against published JSON samples first,
then swap to approved live endpoints WITHOUT changing the evidence contract.
That contract is `SourceRecord`; do not change its shape when live mode lands.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.evidence.adapters.base import SourceAdapter, SourceRecord

REPLAY_FIXTURE = Path(__file__).parent / "replay" / "transtar_sample.json"


class TranStarAdapter(SourceAdapter):
    source_name = "TranStar"

    def __init__(self, mode: str = "replay"):
        self.mode = mode  # type: ignore[assignment]

    async def fetch(self, *, event_window: tuple[datetime, datetime],
                     bbox: dict[str, Any]) -> list[SourceRecord]:
        if self.mode == "replay":
            return self._load_replay()
        raise NotImplementedError(
            "Live TranStar endpoint pending access coordination (see deck slide 6 blocker)."
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
