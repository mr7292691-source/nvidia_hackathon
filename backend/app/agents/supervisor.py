"""
The "OpenShell supervisor" from slide 3's Decision Gates layer.

Built on LangChain DeepAgents (create_deep_agent), running inside an
OpenShell sandbox (see openshell_sandbox.py), with sub-agent delegation to
the specialists in app/agents/specialists/. Model calls go through
app/nvidia_runtime/nim_reasoning.py -> Switchyard -> NIM (Nemotron), and are
governed end-to-end by NeMo Relay (app/nvidia_runtime/relay/).

DeepAgents lets a CompiledStateGraph be passed in as a sub-agent, so each
specialist below can itself be a small LangGraph graph rather than a plain
function — useful once evidence/vision/policy specialists need their own
internal tool loops.
"""
from __future__ import annotations

from typing import Any

from app.agents.openshell_sandbox import openshell_session
from app.agents.specialists.evidence_specialist import build_evidence_specialist
from app.agents.specialists.lifesafety_specialist import build_lifesafety_specialist
from app.agents.specialists.policy_specialist import build_policy_specialist
from app.agents.specialists.vision_specialist import build_vision_specialist

SUPERVISOR_SYSTEM_PROMPT = """\
You are the LifeShield AI supervisor for a single disaster event. You
coordinate specialist sub-agents and MUST NOT take any action yourself —
you only delegate to specialists and pass their outputs to the deterministic
decision-output layer. You never call an external website or database
directly; you only have the tools your specialists expose, which are
validated wrappers over the event's evidence record.
"""


async def run_supervisor(*, event_id: str) -> dict[str, Any]:
    """
    Orchestrates one event through: evidence specialist -> vision specialist
    -> policy specialist -> life-safety specialist. Returns the specialists'
    combined findings for app/decisions/ to turn into the two final outputs.

    NOTE: this stub sequences specialists directly; once `deepagents` is
    pinned, replace the body with a real `create_deep_agent(...)` supervisor
    whose sub_agents list is the four specialists below, so the model itself
    decides delegation order and can re-query a specialist if a gate blocks it.
    """
    async with openshell_session():
        evidence_specialist = build_evidence_specialist()
        vision_specialist = build_vision_specialist()
        policy_specialist = build_policy_specialist()
        lifesafety_specialist = build_lifesafety_specialist()

        evidence_findings = await evidence_specialist.run(event_id=event_id)
        vision_findings = await vision_specialist.run(event_id=event_id)
        policy_findings = await policy_specialist.run(event_id=event_id)
        lifesafety_findings = await lifesafety_specialist.run(
            event_id=event_id,
            evidence=evidence_findings,
            vision=vision_findings,
        )

        return {
            "event_id": event_id,
            "evidence": evidence_findings,
            "vision": vision_findings,
            "policy": policy_findings,
            "lifesafety": lifesafety_findings,
        }
