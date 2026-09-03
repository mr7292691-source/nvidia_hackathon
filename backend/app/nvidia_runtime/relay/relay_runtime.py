"""
NeMo Relay integration point. Every LLM call and every tool call the agents
make is required to pass through here — this is the literal implementation
of "NeMo Relay governs every call" from the deck.

This file uses the REAL `nemo-relay` 0.8.3 Python API, verified by
introspecting the installed package (not the docs, which describe a
slightly different surface in places) — specifically:

  - `nemo_relay.scope.scope(name, scope_type, attributes=...)` is a
    contextmanager yielding a `ScopeHandle` — this is the real equivalent
    of what earlier drafts called `push_scope`/`pop_scope`.
  - `nemo_relay.ScopeType` is a real enum: Agent, Tool, Llm, Function,
    Guardrail, Retriever, Reranker, Embedder, Evaluator, Custom, Unknown.
  - Guardrail registration is `nemo_relay.guardrails.register_tool_conditional_execution(name, priority, guardrail_fn)`
    and `...register_llm_conditional_execution(...)` — NOT
    `register_tool_conditional_execution_guardrail` as earlier drafts
    guessed. `guardrail_fn(tool_name, args) -> str | None | Awaitable[...]`;
    returning a string blocks the call with that string as the reason.

`nemo_relay` is a required dependency, not an optional one — if it's not
importable, the app fails to start rather than silently running ungoverned.
This is a deliberate design choice per the "no stubs" requirement: an
ungoverned fallback path defeats the entire point of this layer.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

import nemo_relay

from app.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

_atof_exporter: nemo_relay.AtofExporter | None = None


def init_relay() -> None:
    """
    Call once at app startup (see app/main.py's lifespan). Registers a file
    ATOF exporter pointed at NEMO_RELAY_ATOF_OUTPUT_DIR — this is the
    auditable, source-lineage-linked trail the deck's Layer 1 promises;
    vision/reasoning calls become part of the same trajectory record as the
    evidence adapters via the shared event_id scope attribute.
    """
    global _atof_exporter
    settings = get_settings()

    import os
    os.makedirs(settings.nemo_relay_atof_output_dir, exist_ok=True)

    # AtofExporterConfig is a native (PyO3) class that takes ZERO
    # constructor arguments — properties are set on the instance after
    # construction, not passed as kwargs. Confirmed by testing directly:
    # `AtofExporterConfig(output_directory=...)` raises "unexpected keyword
    # argument"; `AtofExporterConfig()` then `.output_directory = ...`
    # works, and a full register -> scope -> deregister -> shutdown cycle
    # produces real ATOF JSONL with our metadata (event_id) attached to
    # both the scope-start and scope-end records.
    try:
        config = nemo_relay.AtofExporterConfig()
        config.output_directory = settings.nemo_relay_atof_output_dir
        config.filename = "lifeshield.jsonl"
        _atof_exporter = nemo_relay.AtofExporter(config)
        _atof_exporter.register("lifeshield-atof")
        logger.info(
            "NeMo Relay ATOF exporter registered, writing to %s",
            _atof_exporter.path,
        )
    except Exception:
        logger.exception("Failed to construct/register the NeMo Relay ATOF exporter.")
        raise

    logger.info("NeMo Relay runtime initialized (real, not stubbed).")


def shutdown_relay() -> None:
    global _atof_exporter
    if _atof_exporter is not None:
        _atof_exporter.deregister("lifeshield-atof")
        _atof_exporter.shutdown()
        _atof_exporter = None


async def relay_llm_call(
    *, scope_name: str, event_id: str, call: Callable[[], Awaitable[T]]
) -> T:
    """
    Wrap a Switchyard chat-completion call in a real Relay LLM scope.

    NOTE: `attributes=` on `scope.scope()` is NOT for arbitrary key/value
    metadata — `ScopeAttributes` is a bitflag type (PARALLEL/RELOCATABLE),
    confirmed by testing it directly; passing a plain dict raises
    `TypeError: 'dict' object is not an instance of 'ScopeAttributes'`.
    Arbitrary metadata (like event_id) goes in `metadata=`, confirmed
    working the same way.
    """
    with nemo_relay.scope.scope(
        scope_name, nemo_relay.ScopeType.Llm, metadata={"event_id": event_id}
    ):
        return await call()


async def relay_tool_call(
    *, scope_name: str, event_id: str, call: Callable[[], Awaitable[T]]
) -> T:
    """Wrap a tool call in a real Relay Tool scope."""
    with nemo_relay.scope.scope(
        scope_name, nemo_relay.ScopeType.Tool, metadata={"event_id": event_id}
    ):
        return await call()
