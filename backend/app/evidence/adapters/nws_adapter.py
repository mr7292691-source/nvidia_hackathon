"""
NWS alerts adapter. Slide 5 demo step 1: "NWS alert with heavy-rain forecast
defines the event polygon and time window" -- this adapter is the entry
point that establishes the official event.

Live mode: real implementation against https://api.weather.gov/alerts (no
API key required, per NWS's public API). NOTE: this environment's network
policy does not permit reaching api.weather.gov (see docs/plan.md's network
notes), so this code is written for real but genuinely unverified against
the live endpoint -- called out explicitly rather than claimed as tested.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.evidence.adapters.base import SourceAdapter, SourceRecord

REPLAY_FIXTURE = Path(__file__).parent / "replay" / "nws_sample.json"
NWS_ALERTS_URL = "https://api.weather.gov/alerts"


class NWSAdapter(SourceAdapter):
    source_name = "NWS"

    def __init__(self, mode: str = "replay"):
        self.mode = mode  # type: ignore[assignment]

    async def fetch(self, *, event_window: tuple[datetime, datetime],
                     bbox: dict[str, Any]) -> list[SourceRecord]:
        if self.mode == "replay":
            return self._load_replay()
        return await self._fetch_live(event_window=event_window, bbox=bbox)

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

    async def _fetch_live(self, *, event_window: tuple[datetime, datetime],
                           bbox: dict[str, Any]) -> list[SourceRecord]:
        """
        NWS's /alerts endpoint supports an `area` query param (state
        abbreviation) but not an arbitrary bbox directly -- for a bbox
        query, /alerts?point={lat},{lon} or /alerts/active with a polygon
        filter applied client-side is the documented pattern. This
        implementation filters client-side against the bbox's bounding
        coordinates, which is correct but unverified against live data.
        """
        params = {"status": "actual", "message_type": "alert"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(NWS_ALERTS_URL, params=params,
                                     headers={"User-Agent": "LifeShieldAI/0.1 (hackathon demo)"})
            resp.raise_for_status()
            data = resp.json()

        records: list[SourceRecord] = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            geometry = feature.get("geometry")
            if geometry is None:
                continue
            if not _geometry_intersects_bbox(geometry, bbox):
                continue
            effective_raw = props.get("effective") or props.get("sent")
            if not effective_raw:
                continue
            observed_at = datetime.fromisoformat(effective_raw.replace("Z", "+00:00"))
            records.append(
                SourceRecord(
                    source=self.source_name,
                    fetched_at=datetime.utcnow(),
                    observed_at=observed_at,
                    location=geometry,
                    payload={
                        "alert_id": props.get("id"),
                        "event_type": props.get("event"),
                        "severity": props.get("severity"),
                        "headline": props.get("headline"),
                        "effective": props.get("effective"),
                        "expires": props.get("expires"),
                    },
                    confidence_hint=None,
                    raw_source_url=NWS_ALERTS_URL,
                )
            )
        return records


def _geometry_intersects_bbox(geometry: dict, bbox: dict) -> bool:
    """Cheap bounding-box overlap check -- not a real polygon intersection,
    sufficient for filtering a national alert feed down to the event area.
    A real implementation should use shapely; kept dependency-free here."""
    bbox_coords = bbox.get("coordinates", [[]])[0]
    if not bbox_coords:
        return True
    bbox_lons = [c[0] for c in bbox_coords]
    bbox_lats = [c[1] for c in bbox_coords]
    bmin_lon, bmax_lon = min(bbox_lons), max(bbox_lons)
    bmin_lat, bmax_lat = min(bbox_lats), max(bbox_lats)

    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if coords is None:
        return False
    if geom_type == "Point":
        lon, lat = coords
        return bmin_lon <= lon <= bmax_lon and bmin_lat <= lat <= bmax_lat
    if geom_type in ("Polygon", "MultiPolygon"):
        flat = _flatten_coords(coords)
        return any(bmin_lon <= lon <= bmax_lon and bmin_lat <= lat <= bmax_lat for lon, lat in flat)
    return False


def _flatten_coords(coords: Any) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if not coords:
        return points
    if isinstance(coords[0], (int, float)):
        return [(coords[0], coords[1])]
    for item in coords:
        points.extend(_flatten_coords(item))
    return points
