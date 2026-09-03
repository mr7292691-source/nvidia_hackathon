"""
Thin OpenAI-compatible client pointed at the NVIDIA-NeMo/Switchyard proxy
(run as a sidecar — see infra/switchyard/). This is the ONLY place backend
code should hold a base_url for model traffic.

Switchyard translates OpenAI Chat / Anthropic Messages / OpenAI Responses
formats and dispatches to whichever backend the active route config names:

  dev  (infra/switchyard/routes.dev.toml)  -> https://integrate.api.nvidia.com/v1
                                                (build.nvidia.com, NVIDIA_API_KEY)
  prod (infra/switchyard/routes.prod.toml) -> self-hosted NIM containers on
                                                the Curiosity B300 cluster

Application code never branches on environment — it always calls
`switchyard_chat_completion(...)`. NeMo Relay wraps this call (see relay/)
so every request/response is observed and can be blocked by a guardrail.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class SwitchyardClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.switchyard_base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=60.0)

    async def chat_completion(
        self,
        *,
        route: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        tools: list[dict[str, Any]] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        `route` is the Switchyard route id from routes.<env>.toml (e.g.
        "lifeshield-reasoning" or "lifeshield-vision"), NOT a raw model name —
        Switchyard resolves the route to whatever backend/model is configured
        for the active environment.
        """
        body: dict[str, Any] = {
            "model": route,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            body["tools"] = tools
        if extra:
            body.update(extra)

        resp = await self._client.post("/chat/completions", json=body)
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._client.aclose()


_client: SwitchyardClient | None = None


def get_switchyard_client() -> SwitchyardClient:
    global _client
    if _client is None:
        _client = SwitchyardClient()
    return _client
