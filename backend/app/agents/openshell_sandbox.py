"""
OpenShell sandbox session manager -- real `openshell` 0.0.116 SDK
(gRPC-backed), NOT the placeholder that used to log a message and do
nothing. Verified by introspection against the installed package, and
corrected once already by running `mypy` against it: every
`SandboxClient` lifecycle method (`create`, `wait_ready`, `delete`,
`wait_deleted`) requires a `workspace` keyword argument that isn't
optional -- an earlier draft of this file omitted it, which mypy caught
as a real type error (missing required argument), not a style nit.

This IS the mechanism behind the deck's guardrail: "Agents never consume
raw websites or databases -- they receive validated tools and evidence
records." The sandbox's network policy (configured cluster-side, not by
this client) is what actually enforces that; this file only manages the
session lifecycle from the application side.

HONEST LIMITATION: `SandboxClient.from_active_cluster()` requires a
reachable OpenShell cluster (a real gRPC server) -- there is no such
cluster in the sandbox this code was written in, so this has been
type-checked and read carefully against the real SDK, but never actually
executed against a live cluster. Genuinely unverified, called out
explicitly rather than presented as tested.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import openshell

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# TODO: confirm the real workspace name/convention once a live OpenShell
# cluster is available -- "default" is a placeholder, not verified against
# any actual cluster configuration.
DEFAULT_WORKSPACE = "default"


class OpenShellSandboxSession:
    def __init__(self, sandbox_name: str, workspace: str = DEFAULT_WORKSPACE) -> None:
        self.sandbox_name = sandbox_name
        self.workspace = workspace
        self._client: openshell.SandboxClient | None = None

    async def start(self) -> None:
        self._client = openshell.SandboxClient.from_active_cluster()
        self._client.create(workspace=self.workspace, name=self.sandbox_name)
        self._client.wait_ready(self.sandbox_name, workspace=self.workspace)
        logger.info("OpenShell sandbox '%s' (workspace=%s) ready.", self.sandbox_name, self.workspace)

    async def stop(self) -> None:
        if self._client is not None:
            self._client.delete(self.sandbox_name, workspace=self.workspace)
            self._client.wait_deleted(self.sandbox_name, workspace=self.workspace)
            logger.info("OpenShell sandbox '%s' deleted.", self.sandbox_name)
            self._client.close()

    def exec(self, command: list[str]) -> "openshell.ExecResult":
        """`command` is argv-style (e.g. ["python3", "-c", "..."]), not a
        shell string -- confirmed against the real signature, which takes
        `Sequence[str]`. `exec` itself takes no `workspace` kwarg (unlike
        create/delete/wait_ready/wait_deleted), since it addresses the
        sandbox by id directly."""
        if self._client is None:
            raise RuntimeError("Sandbox not started -- call start() first.")
        return self._client.exec(self.sandbox_name, command)


@asynccontextmanager
async def openshell_session() -> AsyncIterator[OpenShellSandboxSession]:
    settings = get_settings()
    session = OpenShellSandboxSession(settings.openshell_sandbox_name)
    await session.start()
    try:
        yield session
    finally:
        await session.stop()
