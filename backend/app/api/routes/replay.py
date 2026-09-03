"""
Single-button version of slide 5's whole demo flow: official event ->
corroborate -> build event bundle -> run agents -> finalize decisions.
Exists purely for the demo UI's "Run Houston replay" action so the frontend
doesn't have to orchestrate four separate calls itself.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.agents.supervisor import run_supervisor
from app.agents.tools.evidence_tools import register_event
from app.agents.tools.portfolio_tools import get_policies_in_footprint
from app.decisions.insurer_exposure import build_insurer_exposure_report
from app.decisions.lifesafety_guidance import build_lifesafety_guidance
from app.evidence.evidence_record import build_event_bundle

router = APIRouter(prefix="/replay", tags=["replay"])

DEMO_WINDOW = (datetime(2026, 6, 14, 6, 0, 0), datetime(2026, 6, 14, 20, 0, 0))
DEMO_BBOX = {
    "type": "Polygon",
    "coordinates": [[[-95.55, 29.60], [-95.30, 29.60], [-95.30, 29.85], [-95.55, 29.85], [-95.55, 29.60]]],
}


@router.post("/houston-event")
async def replay_houston_event():
    record = await build_event_bundle(event_window=DEMO_WINDOW, bbox=DEMO_BBOX)
    await register_event(record)

    findings = await run_supervisor(event_id=record.event_id)

    guidance = build_lifesafety_guidance(
        event_id=record.event_id,
        draft_guidance=findings.get("lifesafety", {}).get("draft_guidance", ""),
    )
    policies = await get_policies_in_footprint(event_id=record.event_id)
    exposure_report = build_insurer_exposure_report(
        event_id=record.event_id, policies=policies, damage_severity_factor=0.5
    )

    return {
        "event_id": record.event_id,
        "lineage": record.lineage,
        "findings": findings,
        "lifesafety_guidance": guidance.model_dump(),
        "insurer_exposure": exposure_report.model_dump(),
        "note": "Illustrative synthetic scenario — proves the flow, not a real prediction.",
    }
