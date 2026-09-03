"""
Re-exports the request/response shapes that cross the API boundary, kept in
one place so the frontend's src/types/ can be hand-mirrored from here without
hunting through route files.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EventWindow(BaseModel):
    window_start: datetime
    window_end: datetime
    bbox: dict


class EventCreatedResponse(BaseModel):
    event_id: str
    lineage: list[dict]
