from __future__ import annotations

from fastapi import APIRouter

from app.agents.supervisor import run_supervisor

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run/{event_id}")
async def run_agents(event_id: str):
    """
    Runs the OpenShell-sandboxed DeepAgents supervisor for this event.
    Every LLM/tool call inside is subject to the evidence_verifier /
    confidence_gate / policy_verifier NeMo Relay guardrails — a blocked gate
    surfaces here as a normal (non-500) response with the block reason, not
    an exception, so the frontend can show an "evidence gap" state cleanly.
    """
    findings = await run_supervisor(event_id=event_id)
    return findings
