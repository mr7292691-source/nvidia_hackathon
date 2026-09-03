"""
USGS stream gauge adapter. Corroborating signal (slide 5 step 2): gauge rise
supports the NWS-defined event.

Live mode: real implementation against
https://waterservices.usgs.gov/nwis/iv/ (Instantaneous Values web service,
no API key required). Same network-policy caveat as nws_adapter.py applies
-- written for real, unverified against the live endpoint from this
environment.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.evidence.adapters.base import SourceAdapter, SourceRecord

REPLAY_FIXTURE = Path(__file__).parent / "replay" / "usgs_sample.json"
USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"

# USGS parameter code 00065 = gauge height, feet
GAUGE_HEIGHT_PARAM_CODE = "00065"


class USGSGaugeAdapter(SourceAdapter):
    source_name = "USGS"

    def __init__(self, mode: str = "replay"):
        self.mode = mode  # type: ignore[assignment]

    async def fetch(self, *, event_window: tuple[datetime, datetime],
                     bbox: dict[str, Any]) -> list[SourceRecord]:
        if self.mode == "replay":
            return self._load_replay()
        return await self._fetch_live(bbox=bbox)

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

    async def _fetch_live(self, *, bbox: dict[str, Any]) -> list[SourceRecord]:
        bbox_coords = bbox.get("coordinates", [[]])[0]
        lons = [c[0] for c in bbox_coords]
        lats = [c[1] for c in bbox_coords]
        bbox_param = f"{min(lons)},{min(lats)},{max(lons)},{max(lats)}"

        params = {
            "format": "json",
            "bBox": bbox_param,
            "parameterCd": GAUGE_HEIGHT_PARAM_CODE,
            "siteStatus": "active",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(USGS_IV_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        records: list[SourceRecord] = []
        for series in data.get("value", {}).get("timeSeries", []):
            site = series.get("sourceInfo", {})
            site_code = site.get("siteCode", [{}])[0].get("value")
            site_name = site.get("siteName")
            geo = site.get("geoLocation", {}).get("geogLocation", {})
            lat, lon = geo.get("latitude"), geo.get("longitude")

            values = series.get("values", [{}])[0].get("value", [])
            if not values:
                continue
            latest = values[-1]

            records.append(
                SourceRecord(
                    source=self.source_name,
                    fetched_at=datetime.utcnow(),
                    observed_at=datetime.fromisoformat(latest["dateTime"]),
                    location={"type": "Point", "coordinates": [lon, lat]},
                    payload={
                        "site_id": site_code,
                        "site_name": site_name,
                        "gauge_height_ft": float(latest["value"]),
                    },
                    confidence_hint=None,
                    raw_source_url=USGS_IV_URL,
                )
            )
        return records
