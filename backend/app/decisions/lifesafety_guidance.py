"""
Turns the life-safety specialist's draft into a formal decision output.
Unlike insurer_exposure.py, the guidance TEXT itself does come from the LLM
specialist (it's advisory language, not arithmetic) — but it cannot be
`approved=True` until app/approvals/human_approval.py records a human sign-off.
"""
from __future__ import annotations

from app.decisions.schemas import LifeSafetyGuidance


def build_lifesafety_guidance(*, event_id: str, draft_guidance: str) -> LifeSafetyGuidance:
    return LifeSafetyGuidance(
        event_id=event_id,
        guidance_text=draft_guidance,
        evidence_ref=event_id,
        approved=False,
    )
