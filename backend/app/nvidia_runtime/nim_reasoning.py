"""
Reasoning NIM call — powers the DeepAgents specialists (Nemotron via NIM).

Route id "lifeshield-reasoning" is resolved by Switchyard:
  dev  -> a build.nvidia.com Nemotron NIM (e.g. nvidia/nemotron family —
          pin the exact model card the team settles on; TODO)
  prod -> the equivalent NIM container self-hosted on the B300 node
"""
from __future__ import annotations

from typing import Any

from app.nvidia_runtime.relay.relay_runtime import relay_llm_call
from app.nvidia_runtime.switchyard_client import get_switchyard_client


async def reasoning_call(
    *,
    event_id: str,
    scope_name: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    async def _call() -> dict[str, Any]:
        client = get_switchyard_client()
        return await client.chat_completion(
            route="lifeshield-reasoning", messages=messages, tools=tools
        )

    return await relay_llm_call(scope_name=scope_name, event_id=event_id, call=_call)
