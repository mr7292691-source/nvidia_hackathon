"""
Confidence gate -- second decision gate.

Per slide 6: "the confidence gate blocks weak evidence." Real
implementation: reads the persisted vision confidence
(EvidenceRecordRow.vision_confidence, set by
app/agents/tools/evidence_tools.py:set_vision_confidence after the vision
specialist's Relay-governed NIM call) combined with the evidence verifier's
own corroboration score.

Slide 6 proof target: "Show a blocked low-confidence case returning an
evidence gap" -- this is the gate that produces that block. If no vision
confidence has been recorded yet (vision specialist hasn't run), this gate
blocks rather than assuming a default -- silently passing an event with
literally no vision evidence would be worse than a false block.
"""
from __future__ import annotations

from app.agents.gates.evidence_verifier import GateResult, evidence_verifier_check
from app.db.models import EvidenceRecordRow
from app.db.session import get_session

MIN_CONFIDENCE = 0.6


async def confidence_gate_check(
    *, event_id: str | None, tool_name: str | None = None, args: dict | None = None
) -> GateResult:
    if not event_id:
        return GateResult(passed=False, reason="No event_id provided -- cannot assess confidence.")

    evidence_result = await evidence_verifier_check(event_id=event_id)
    if not evidence_result.passed:
        # Confidence gate runs after evidence_verifier in the composed
        # guardrail (see relay/guardrails.py) so this branch shouldn't
        # normally be reached, but stays defensive if called standalone.
        return evidence_result

    async with get_session() as session:
        row = await session.get(EvidenceRecordRow, event_id)

    if row is None:
        return GateResult(passed=False, reason=f"No evidence record for event_id={event_id}.")

    if row.vision_confidence is None:
        return GateResult(
            passed=False,
            reason="No vision confidence recorded yet -- evidence gap (vision specialist "
            "has not assessed a field image for this event).",
        )

    combined = (row.vision_confidence + (evidence_result.score or 0.0)) / 2
    if combined < MIN_CONFIDENCE:
        return GateResult(
            passed=False,
            reason=f"Combined confidence {combined:.2f} below threshold {MIN_CONFIDENCE} "
            "-- evidence gap.",
            score=combined,
        )

    return GateResult(passed=True, score=combined)
