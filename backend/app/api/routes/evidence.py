from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from app.agents.tools.evidence_tools import get_evidence_record, register_field_image

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/{event_id}")
async def get_evidence(event_id: str):
    record = await get_evidence_record(event_id=event_id)
    if "error" in record:
        raise HTTPException(status_code=404, detail=record["error"])
    return record


@router.post("/{event_id}/field-image")
async def upload_field_image(event_id: str, file: UploadFile):
    """Slide 5 step 2: 'a field image is submitted.' Accepts the image that
    the vision specialist will later assess via the Relay-governed NIM call."""
    contents = await file.read()
    await register_field_image(event_id, contents)
    return {"event_id": event_id, "bytes_received": len(contents)}
