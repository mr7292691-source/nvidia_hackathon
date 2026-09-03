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
        return {"event_id": event_id, "blocked": False, **findings}
    except EvidenceGapError as exc:
        return {"event_id": event_id, "blocked": True, "evidence_gap_reason": exc.reason}


@router.get("/gates/{event_id}")
async def check_gates(event_id: str):
    """
    Runs the three real gates directly (without needing a live NIM call)
    and returns each one's pass/fail/reason -- this is what GatesPanel.tsx
    on the frontend actually renders, replacing its previous static
    "unknown" defaults with real per-gate state.
    """
    from app.agents.gates.confidence_gate import confidence_gate_check
    from app.agents.gates.evidence_verifier import evidence_verifier_check
    from app.agents.gates.policy_verifier import policy_verifier_check

    evidence_result = await evidence_verifier_check(event_id=event_id)
    confidence_result = await confidence_gate_check(event_id=event_id)
    policy_result = await policy_verifier_check(event_id=event_id, args={})

    return {
        "event_id": event_id,
        "gates": [
            {"name": "Evidence Verifier", "passed": evidence_result.passed, "reason": evidence_result.reason},
            {"name": "Confidence Gate", "passed": confidence_result.passed, "reason": confidence_result.reason},
            {"name": "Policy Verifier", "passed": policy_result.passed, "reason": policy_result.reason},
        ],
    }
