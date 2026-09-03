"""
The single choke point every agent-facing tool call must go through. Wraps
`nemo_relay.tools.execute()` (the real, verified pipeline that runs the
registered conditional-execution guardrail -- i.e. the three decision
gates -- before `func` is allowed to run) and turns its real
`RuntimeError("guardrail rejected: <reason>")` into a typed
`EvidenceGapError` that routes can catch cleanly.

This is the concrete mechanism behind the deck's guardrail: "no operational
action leaves the system without a passed gate." Any tool that calls its
underlying function directly instead of through `governed_call` bypasses
Relay entirely -- there is no other enforcement point.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable

import nemo_relay

# nemo_relay's real `tools.execute` signature is typed against its own
# `JsonValue` union (str | int | float | bool | None | list | dict), not an
# arbitrary generic -- confirmed by running mypy against an earlier draft
# that used a plain TypeVar here, which failed with real type errors
# (incompatible callback/return types), not stylistic ones. Every tool this
# app wraps already returns a JSON-compatible dict, so this isn't a
# practical limitation, just a more accurate type.
JsonValue = nemo_relay.JsonValue


class EvidenceGapError(Exception):
    """Raised when a decision gate blocks a tool call. Callers (routes)
    should catch this and return a clean 'evidence gap' response rather
    than letting it become an unhandled 500 -- this is the deck's slide 6
    proof requirement: 'Show a blocked low-confidence case returning an
    evidence gap.'"""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


async def governed_call(
    *,
    name: str,
    event_id: str,
    args: dict[str, JsonValue],
    func: Callable[[], Awaitable[JsonValue]],
) -> JsonValue:
    """
    `args` MUST include event_id (the registered guardrail in
    relay/guardrails.py reads it from here) plus anything else a gate might
    need (e.g. `asserted_total_exposure_usd` for the policy verifier).
    """
    full_args: dict[str, JsonValue] = {"event_id": event_id, **args}

    async def _wrapped(_args: nemo_relay.JsonValue) -> nemo_relay.ToolExecutionResult:
        result = await func()
        return nemo_relay.ToolExecutionResult(result)

    try:
        result = await nemo_relay.tools.execute(name, full_args, _wrapped)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("guardrail rejected:"):
            raise EvidenceGapError(message.removeprefix("guardrail rejected:").strip()) from exc
        raise

    return result.result
