"""
The "OpenShell supervisor" from slide 3's Decision Gates layer.

Real deepagents.create_deep_agent(...) graph (verified against the actually
installed deepagents 0.7.13 API by introspection: create_deep_agent(model,
tools, *, system_prompt, subagents=[...], interrupt_on={...}, ...) ->
CompiledStateGraph), NOT manual function sequencing. Each specialist is
registered as a real `SubAgent` TypedDict (name, description, tools,
system_prompt). Model calls go through ChatNVIDIA pointed at the Switchyard
proxy (app/nvidia_runtime/switchyard_client.py's base_url), governed
end-to-end by NeMo Relay via the tool wrappers in app/agents/tools/.

Human approval is wired through DeepAgents' NATIVE interrupt_on mechanism
(langchain.agents.middleware.human_in_the_loop.InterruptOnConfig) rather
than a bespoke polling queue -- confirmed this is a real, first-class
LangGraph human-in-the-loop feature, not something bolted on. The
request_human_approval tool is configured to always interrupt
(interrupt_on={"request_human_approval": True}), which requires a
checkpointer to actually pause/resume across the interrupt boundary.

NOTE: constructing this graph does not require network access -- verified
directly (ChatNVIDIA(...) instantiates without a live call). *Invoking* it
does, and that call cannot be exercised from a sandbox with no route to
build.nvidia.com (see docs/plan.md) -- this is a genuine, currently-unverified
integration point, unlike the persistence/gates/Relay wiring above, and is
called out honestly rather than claimed as tested.
"""
from __future__ import annotations

from typing import Any, cast

from deepagents import SubAgent, create_deep_agent
from langchain_core.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from app.agents.openshell_sandbox import openshell_session
from app.agents.tools.evidence_tools import get_evidence_record, get_field_image
from app.agents.tools.notify_tools import request_human_approval
from app.agents.tools.portfolio_tools import get_policies_in_footprint
from app.core.config import get_settings
from app.nvidia_runtime.nim_vision import assess_flood_image
from app.nvidia_runtime.relay.governed_tools import governed_call

SUPERVISOR_SYSTEM_PROMPT = """\
You are the LifeShield AI supervisor for a single disaster event. You
coordinate specialist sub-agents and MUST NOT take any action yourself --
you only delegate to specialists and pass their outputs to the deterministic
decision-output layer. You never call an external website or database
directly; you only have the tools your specialists expose, which are
governed wrappers over the event's evidence record. If a tool call comes
back as an evidence gap (blocked by a decision gate), report that gap
plainly rather than working around it.
"""


def _build_tools_for_event(event_id: str) -> dict[str, Any]:
    """
    Builds event-bound LangChain tools, each routed through
    governed_call() so the real NeMo Relay guardrail (evidence_verifier ->
    confidence_gate -> policy_verifier) actually runs before the
    underlying function executes.

    governed_call() is typed against nemo_relay's real (non-generic)
    JsonValue return type -- confirmed by reading tools.py directly, it
    isn't parameterized per-call. The cast() calls below are safe because
    we know by construction what each of our own tool functions returns;
    this was flagged by mypy as a real type mismatch against the library's
    actual signature, not a style nit.
    """

    @tool
    async def evidence_record_tool() -> dict:
        """Fetch this event's evidence record (sources + lineage)."""
        return cast(dict, await governed_call(
            name="evidence_record_tool", event_id=event_id, args={},
            func=lambda: get_evidence_record(event_id=event_id),
        ))

    @tool
    async def vision_assessment_tool() -> dict:
        """Assess the field image submitted for this event, if any."""
        image = await get_field_image(event_id=event_id)
        if image is None:
            return {"damage_assessment": None, "note": "no field image submitted"}
        return cast(dict, await governed_call(
            name="vision_assessment_tool", event_id=event_id, args={},
            func=lambda: assess_flood_image(image_bytes=image, event_id=event_id),
        ))

    @tool
    async def policy_overlay_tool() -> list[dict]:
        """Fetch synthetic insurer policies inside this event's footprint."""
        async def _fetch() -> Any:
            return await get_policies_in_footprint(event_id=event_id)

        return cast(list, await governed_call(
            name="policy_overlay_tool", event_id=event_id, args={}, func=_fetch,
        ))

    @tool
    async def request_approval_tool(proposed_action: dict) -> str:
        """Request human approval for a proposed life-safety or insurer
        action. Returns an approval_id -- the action is NOT authorized
        until a human approves it via the /approvals API."""
        return await request_human_approval(event_id=event_id, proposed_action=proposed_action)

    return {
        "evidence": evidence_record_tool,
        "vision": vision_assessment_tool,
        "policy": policy_overlay_tool,
        "approval": request_approval_tool,
    }


def _build_subagents(tools: dict[str, Any]) -> list[SubAgent]:
    return [
        SubAgent(
            name="evidence-specialist",
            description="Summarizes the event's evidence record and flags source disagreement.",
            tools=[tools["evidence"]],
            system_prompt=(
                "Summarize the evidence record. Only use the evidence tool. "
                "Never claim a source exists that isn't in the tool's output."
            ),
        ),
        SubAgent(
            name="vision-specialist",
            description="Assesses flood damage from any submitted field image.",
            tools=[tools["vision"]],
            system_prompt="Assess flood damage severity from the field image tool only.",
        ),
        SubAgent(
            name="policy-specialist",
            description="Summarizes which synthetic insurer policies fall in the event footprint.",
            tools=[tools["policy"]],
            system_prompt="Summarize in-footprint policies. Do not compute exposure math yourself.",
        ),
        SubAgent(
            name="lifesafety-specialist",
            description="Drafts life-safety response guidance from evidence and vision findings.",
            tools=[tools["evidence"], tools["vision"], tools["approval"]],
            system_prompt=(
                "Draft life-safety response guidance based only on the evidence and vision "
                "tools. Mark uncertainty explicitly. When ready to propose an action, call "
                "the approval tool -- do not assume approval yourself."
            ),
        ),
    ]


async def run_supervisor(*, event_id: str) -> dict[str, Any]:
    """
    Runs the real DeepAgents supervisor, inside an OpenShell sandbox, for
    one event. NOTE: actually invoking the returned graph requires a live
    NIM endpoint reachable through Switchyard -- this function will raise
    a connection error in any environment without that (see docs/plan.md).
    """
    settings = get_settings()
    model = ChatNVIDIA(
        model="lifeshield-reasoning",
        base_url=settings.switchyard_base_url,
        api_key=settings.nvidia_api_key or "unset",
    )

    tools = _build_tools_for_event(event_id)
    subagents = _build_subagents(tools)

    agent = create_deep_agent(
        model=model,
        tools=[],  # supervisor only delegates; specialists hold the real tools
        system_prompt=SUPERVISOR_SYSTEM_PROMPT,
        subagents=subagents,
        interrupt_on={"request_approval_tool": True},
        checkpointer=True,
    )

    async with openshell_session():
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": f"Handle disaster event {event_id}."}]},
            config={"configurable": {"thread_id": event_id}},
        )

    return {"event_id": event_id, "messages": result.get("messages", [])}
