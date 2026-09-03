"""
FEMA flood-zone adapter. Supplies the flood-zone overlay used both for
evidence corroboration and for the insurer portfolio overlay in decisions/.

Live mode: real implementation against FEMA's National Flood Hazard Layer
(NFHL) ArcGIS REST feature service (no API key required). Same
network-policy caveat applies -- written for real, unverified against the
live endpoint from this environment.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.evidence.adapters.base import SourceAdapter, SourceRecord

REPLAY_FIXTURE = Path(__file__).parent / "replay" / "fema_sample.json"
# NFHL "Flood Hazard Zones" layer (layer 28) query endpoint.
FEMA_NFHL_QUERY_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)


class FEMAAdapter(SourceAdapter):
    source_name = "FEMA"

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
        envelope = {
            "xmin": min(lons), "ymin": min(lats), "xmax": max(lons), "ymax": max(lats),
            "spatialReference": {"wkid": 4326},
        }
        params = {
            "geometry": json.dumps(envelope),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,STATIC_BFE,DFIRM_ID",
            "returnGeometry": "false",
            "f": "json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(FEMA_NFHL_QUERY_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        records: list[SourceRecord] = []
        for feature in data.get("features", []):
            attrs = feature.get("attributes", {})
            records.append(
                SourceRecord(
                    source=self.source_name,
                    # NFHL zone designations are a standing reference
                    # dataset, not a timestamped reading -- fetched_at is
                    # the only real timestamp available; observed_at is set
                    # to the same value since FEMA doesn't publish an
                    # "as-of" date per feature via this endpoint.
                    fetched_at=datetime.utcnow(),
                    observed_at=datetime.utcnow(),
                    location=bbox,
                    payload={
                        "zone_id": attrs.get("DFIRM_ID"),
                        "flood_zone": attrs.get("FLD_ZONE"),
                        "base_flood_elevation_ft": attrs.get("STATIC_BFE"),
                    },
                    confidence_hint=1.0,
                    raw_source_url=FEMA_NFHL_QUERY_URL,
                )
            )
        return records
