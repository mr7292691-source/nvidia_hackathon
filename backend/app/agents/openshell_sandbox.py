"""
OpenShell sandbox session manager.

Pattern followed from langchain-ai/openshell-deepagent: a DeepAgents agent
runs INSIDE an OpenShell sandbox — an isolated, policy-governed Linux
environment whose network policy blocks arbitrary egress. This is the actual
mechanism behind the deck's guardrail: "Agents never consume raw websites or
databases — they receive validated tools and evidence records."

The sandbox's network allowlist should contain ONLY:
  - this backend's own internal API (so agents can call
    app/agents/tools/*.py, which in turn read EvidenceRecords / portfolio
    data — never the public internet or a raw DB connection string)

Everything else (NWS, USGS, TranStar, etc.) is fetched by the evidence
adapters running in the backend process itself, outside any agent's reach.

TODO: once the team vendors OpenShell (github.com/NVIDIA/OpenShell) and the
openshell-deepagent reference, replace the stub below with real sandbox
create/destroy calls. Keep OPENSHELL_SANDBOX_NAME from settings as the
sandbox identity so it matches whatever `.env` the sandbox process reads.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenShellSandboxSession:
    def __init__(self, sandbox_name: str) -> None:
        self.sandbox_name = sandbox_name

    async def start(self) -> None:
        logger.info("OpenShell sandbox '%s' start — STUB, not yet wired.", self.sandbox_name)
        # TODO: actual OpenShell sandbox bring-up (see openshell-deepagent
        # README for the sandbox lifecycle + network policy config).

    async def stop(self) -> None:
        logger.info("OpenShell sandbox '%s' stop — STUB.", self.sandbox_name)


@asynccontextmanager
async def openshell_session() -> AsyncIterator[OpenShellSandboxSession]:
    settings = get_settings()
    session = OpenShellSandboxSession(settings.openshell_sandbox_name)
    await session.start()
    try:
        yield session
    finally:
        await session.stop()
