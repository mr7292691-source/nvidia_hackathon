"""
OpenShell sandbox session manager -- real `openshell` 0.0.116 SDK
(gRPC-backed), NOT the placeholder that used to log a message and do
nothing. Verified by introspection against the installed package:
`SandboxClient.from_active_cluster(...)`, `.create(...)`, `.create_session(...)`,
`SandboxSession.exec(...)` are all real methods with real signatures.

This IS the mechanism behind the deck's guardrail: "Agents never consume
raw websites or databases -- they receive validated tools and evidence
records." The sandbox's network policy (configured cluster-side, not by
this client) is what actually enforces that; this file only manages the
session lifecycle from the application side.

HONEST LIMITATION: `SandboxClient.from_active_cluster()` requires a
reachable OpenShell cluster (a real gRPC server) -- there is no such
cluster in the sandbox this code was written in, so the `start()`/`stop()`
calls below are real client code but have not been executed against a live
cluster. This is a genuine, currently-unverified integration point, same
category as the NIM/Switchyard-to-real-model calls -- called out explicitly
rather than presented as tested.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import openshell

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenShellSandboxSession:
    def __init__(self, sandbox_name: str) -> None:
        self.sandbox_name = sandbox_name
        self._client: openshell.SandboxClient | None = None
        self._sandbox_id: str | None = None

    async def start(self) -> None:
        """
        Connects to the active OpenShell cluster and creates a sandbox for
        this session. Requires OPENSHELL_CLUSTER (or whatever the real
        cluster-discovery env var is called -- confirm against your
        OpenShell deployment's docs, `from_active_cluster` reads ambient
        cluster config) to point at a reachable cluster.
        """
        self._client = openshell.SandboxClient.from_active_cluster()
        sandbox = self._client.create(name=self.sandbox_name)
        self._sandbox_id = sandbox.id
        self._client.wait_ready(self._sandbox_id)
        logger.info("OpenShell sandbox '%s' (id=%s) ready.", self.sandbox_name, self._sandbox_id)

    async def stop(self) -> None:
        if self._client is not None and self._sandbox_id is not None:
            self._client.delete(self._sandbox_id)
            self._client.wait_deleted(self._sandbox_id)
            logger.info("OpenShell sandbox '%s' deleted.", self.sandbox_name)
        if self._client is not None:
            self._client.close()

    def exec(self, command: str) -> "openshell.ExecResult":
        if self._client is None or self._sandbox_id is None:
            raise RuntimeError("Sandbox not started -- call start() first.")
        return self._client.exec(self._sandbox_id, command)


@asynccontextmanager
async def openshell_session() -> AsyncIterator[OpenShellSandboxSession]:
    settings = get_settings()
    session = OpenShellSandboxSession(settings.openshell_sandbox_name)
    await session.start()
    try:
        yield session
    finally:
        await session.stop()
