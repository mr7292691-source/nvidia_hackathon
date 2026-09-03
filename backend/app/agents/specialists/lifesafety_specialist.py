"""
Life-safety specialist — drafts response guidance from evidence + vision
findings. Its output is a DRAFT for app/decisions/lifesafety_guidance.py,
and still has to pass the policy_verifier gate + human approval before it's
treated as an "output" rather than a suggestion.
"""
from __future__ import annotations

from typing import Any

from app.nvidia_runtime.nim_reasoning import reasoning_call

SYSTEM_PROMPT = """\
Draft life-safety response guidance for a disaster event based ONLY on the
evidence and vision findings you are given. Do not invent facts. Be concise
and actionable. Mark any uncertainty explicitly rather than smoothing over it.
"""


class LifeSafetySpecialist:
    async def run(self, *, event_id: str, evidence: dict, vision: dict) -> dict[str, Any]:
        response = await reasoning_call(
            event_id=event_id,
            scope_name="agents.lifesafety_specialist",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Evidence: {evidence}\nVision: {vision}"},
            ],
        )
        draft = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"draft_guidance": draft}


def build_lifesafety_specialist() -> LifeSafetySpecialist:
    return LifeSafetySpecialist()
