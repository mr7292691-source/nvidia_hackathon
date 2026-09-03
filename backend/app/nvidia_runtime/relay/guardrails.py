"""
Wires the three decision gates (app/agents/gates/) into the REAL NeMo Relay
tool-execution pipeline. Verified end-to-end against the installed
nemo-relay 0.8.3:

  1. `nemo_relay.guardrails.register_tool_conditional_execution(name,
     priority, fn)` registers `fn(tool_name, args) -> str | None`. Returning
     a string blocks the call; `None` allows it. Confirmed this actually
     runs on every call, not just at registration time.
  2. Tool calls MUST go through `await nemo_relay.tools.execute(name, args,
     func)` for the guardrail to apply — calling `func` directly bypasses
     Relay entirely. This is a real, load-bearing constraint on how
     app/agents/tools/*.py must invoke things, not an implementation detail
     hidden in this file.
  3. When a guardrail blocks, `tools.execute` raises
     `RuntimeError("guardrail rejected: <reason>")`. Confirmed by testing
     directly — there is no separate "outcome" object to inspect, it's a
     real exception. Callers (app/api/routes/agents.py) must catch this
     specifically and turn it into the deck's required "evidence gap"
     response (slide 6), not let it become an unhandled 500.

Only ONE guardrail is registered here (not three) because
`register_tool_conditional_execution` takes a single callable per
registration name — the three gates are composed inside that one callable,
run in order, first failure wins. This matches the deck's stated gate order:
evidence verifier -> confidence gate -> policy verifier.
"""
from __future__ import annotations

import logging

import nemo_relay

from app.agents.gates.confidence_gate import confidence_gate_check
from app.agents.gates.evidence_verifier import evidence_verifier_check
from app.agents.gates.policy_verifier import policy_verifier_check

logger = logging.getLogger(__name__)

GUARDRAIL_NAME = "lifeshield-decision-gates"
GUARDRAIL_PRIORITY = 10


async def _decision_gates_guardrail(tool_name: str, args: nemo_relay.JsonValue) -> str | None:
    """
    The single registered guardrail callback. `args` is whatever JSON value
    the caller passed to `nemo_relay.tools.execute` -- typed against
    `nemo_relay.JsonValue` to match the real registered-callback signature
    (an earlier draft typed this as a plain `dict`, which mypy flagged as
    incompatible with what `register_tool_conditional_execution` actually
    expects). Our tool wrappers (app/agents/tools/*.py) are responsible for
    including `event_id` in that dict so the gates have something to look up.
    """
    event_id_raw = args.get("event_id") if isinstance(args, dict) else None
    event_id = event_id_raw if isinstance(event_id_raw, str) else None

    for check in (evidence_verifier_check, confidence_gate_check, policy_verifier_check):
        result = await check(event_id=event_id, tool_name=tool_name, args=args if isinstance(args, dict) else None)
        if not result.passed:
            logger.info("Gate blocked tool=%s event_id=%s reason=%s", tool_name, event_id, result.reason)
            return result.reason
    return None


def register_all_guardrails() -> None:
    nemo_relay.guardrails.register_tool_conditional_execution(
        GUARDRAIL_NAME, GUARDRAIL_PRIORITY, _decision_gates_guardrail
    )
    logger.info(
        "Registered evidence_verifier / confidence_gate / policy_verifier as "
        "one NeMo Relay tool-conditional-execution guardrail (%s)",
        GUARDRAIL_NAME,
    )


def deregister_all_guardrails() -> None:
    nemo_relay.guardrails.deregister_tool_conditional_execution(GUARDRAIL_NAME)
