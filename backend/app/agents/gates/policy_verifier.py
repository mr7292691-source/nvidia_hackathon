"""
Policy verifier -- third decision gate, sits right before human approval.

Verifies that a proposed agent action stays within the deterministic
insurer-exposure figures already computed for this event
(app/decisions/insurer_exposure.py) rather than recomputing or trusting
whatever number an LLM specialist asserts. Real implementation: reads the
persisted InsurerExposureReportRow and checks the proposed action's
asserted figure (if any, passed in `args`) against it.
"""
from __future__ import annotations

from app.agents.gates.evidence_verifier import GateResult
from app.db.models import InsurerExposureReportRow
from app.db.session import get_session

# How much an agent-asserted figure is allowed to drift from the
# deterministic computed total before the gate blocks it. Kept generous
# (10%) since this catches gross fabrication, not rounding differences.
MAX_RELATIVE_DRIFT = 0.10


async def policy_verifier_check(
    *, event_id: str | None, tool_name: str | None = None, args: dict | None = None
) -> GateResult:
    if not event_id:
        return GateResult(passed=False, reason="No event_id provided -- cannot verify policy.")

    args = args or {}
    asserted_exposure = args.get("asserted_total_exposure_usd")

    async with get_session() as session:
        row = await session.get(InsurerExposureReportRow, event_id)

    if row is None:
        # No exposure report computed yet for this event -- nothing to
        # verify against, so this gate has nothing to block on. It is not
        # this gate's job to require an exposure report exists; that's
        # confidence_gate/evidence_verifier's domain.
        return GateResult(passed=True, reason="No insurer exposure report yet -- nothing to check.")

    if asserted_exposure is None:
        # The proposed action doesn't assert a dollar figure at all
        # (e.g. it's a life-safety action, not an insurer one) -- nothing
        # for this gate to verify.
        return GateResult(passed=True)

    computed = row.total_estimated_exposure_usd
    if computed == 0:
        drift_ok = asserted_exposure == 0
    else:
        drift_ok = abs(asserted_exposure - computed) / computed <= MAX_RELATIVE_DRIFT

    if not drift_ok:
        return GateResult(
            passed=False,
            reason=f"Asserted exposure ${asserted_exposure:,.2f} diverges from the "
            f"deterministic computed total ${computed:,.2f} by more than "
            f"{MAX_RELATIVE_DRIFT:.0%}.",
        )

    return GateResult(passed=True, score=1.0 - abs(asserted_exposure - computed) / max(computed, 1))
