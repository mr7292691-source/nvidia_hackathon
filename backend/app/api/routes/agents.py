from __future__ import annotations

from fastapi import APIRouter

from app.agents.supervisor import run_supervisor
from app.nvidia_runtime.relay.governed_tools import EvidenceGapError

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run/{event_id}")
async def run_agents(event_id: str):
    """
    Runs the OpenShell-sandboxed DeepAgents supervisor for this event.
    A blocked NeMo Relay guardrail (evidence_verifier / confidence_gate /
    policy_verifier) surfaces here as a clean 200 response with an
    "evidence gap" shape (deck slide 6's required proof point), not a 500.
    """
    try:
        findings = await run_supervisor(event_id=event_id)
        return findings
    except EvidenceGapError as exc:
        return {"event_id": event_id, "blocked": True, "evidence_gap_reason": exc.reason}
