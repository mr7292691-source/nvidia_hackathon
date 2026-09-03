from __future__ import annotations

from fastapi import APIRouter

from app.agents.tools.portfolio_tools import get_policies_in_footprint
from app.decisions.insurer_exposure import build_insurer_exposure_report
from app.decisions.lifesafety_guidance import build_lifesafety_guidance

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("/{event_id}/finalize")
async def finalize_decisions(event_id: str, findings: dict):
    """
    Turns supervisor findings (from POST /agents/run/{event_id}) into the two
    decision outputs from slide 3/5: life-safety guidance + insurer exposure,
    both citing the same evidence record (evidence_ref=event_id). Neither is
    `approved=True` until a human signs off via /approvals.
    """
    draft_guidance = findings.get("lifesafety", {}).get("draft_guidance", "")
    guidance = build_lifesafety_guidance(event_id=event_id, draft_guidance=draft_guidance)

    policies = await get_policies_in_footprint(event_id=event_id)
    # TODO: derive damage_severity_factor deterministically from the vision
    # specialist's structured output once that schema is defined; 0.5 is a
    # placeholder mid-severity value for the demo only.
    damage_severity_factor = 0.5
    exposure_report = build_insurer_exposure_report(
        event_id=event_id, policies=policies, damage_severity_factor=damage_severity_factor
    )

    return {
        "lifesafety_guidance": guidance.model_dump(),
        "insurer_exposure": exposure_report.model_dump(),
    }
