"""
Slide 5 step 3: "FastAPI issues an event_id." This route is that literal
moment — it builds the joined evidence bundle (Layer 1) and returns the
event_id the rest of the flow keys off of.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.tools.evidence_tools import register_event
from app.evidence.evidence_record import build_event_bundle

router = APIRouter(prefix="/events", tags=["events"])


class CreateEventRequest(BaseModel):
    window_start: datetime
    window_end: datetime
    bbox: dict


@router.post("")
async def create_event(req: CreateEventRequest):
    record = await build_event_bundle(
        event_window=(req.window_start, req.window_end),
        bbox=req.bbox,
    )
    await register_event(record)
    return {"event_id": record.event_id, "lineage": record.lineage}


@router.post("/replay/houston-demo")
async def replay_houston_demo():
    """One-click trigger for the slide-5 demo: replays the bundled Houston
    fixtures end to end and returns the event_id, ready for /agents/run."""
    demo_window = (datetime(2026, 6, 14, 6, 0, 0), datetime(2026, 6, 14, 20, 0, 0))
    demo_bbox = {"type": "Polygon", "coordinates": [[[-95.55, 29.60], [-95.30, 29.60],
                                                       [-95.30, 29.85], [-95.55, 29.85],
                                                       [-95.55, 29.60]]]}
    record = await build_event_bundle(event_window=demo_window, bbox=demo_bbox)
    await register_event(record)
    return {"event_id": record.event_id, "lineage": record.lineage}
