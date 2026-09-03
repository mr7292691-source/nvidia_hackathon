"""
Policy specialist — reads the synthetic insurer portfolio overlay for the
event footprint via app/agents/tools/portfolio_tools.py. Does NOT compute
TIV/limit/deductible math itself (that's deterministic, see
app/decisions/insurer_exposure.py) — it only summarizes which policies are
in-footprint for the supervisor and downstream policy_verifier gate.
"""
from __future__ import annotations

from typing import Any

from app.agents.tools.portfolio_tools import get_policies_in_footprint


class PolicySpecialist:
    async def run(self, *, event_id: str) -> dict[str, Any]:
        policies = await get_policies_in_footprint(event_id=event_id)
        return {"policies_in_footprint": policies}


def build_policy_specialist() -> PolicySpecialist:
    return PolicySpecialist()
