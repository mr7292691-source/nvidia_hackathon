"""
OpenShell sandbox session manager -- real `openshell` 0.0.116 SDK
(gRPC-backed). Confirmed against the real SDK signatures (mypy caught real
missing-argument bugs in an earlier draft, see git history).

CONNECTION MODES:
  1. Local dev (default, OPENSHELL_GATEWAY_ENDPOINT unset): calls
     `SandboxClient.from_active_cluster()`, which reads the CLI's on-disk
     gateway state (`~/.config/openshell/active_gateway` or
     `$OPENSHELL_GATEWAY`). Per NVIDIA's own quickstart, this requires
     Docker Desktop running locally, and the gateway is auto-created the
     first time `openshell sandbox create` runs. This is NVIDIA's
     documented, supported local flow.

  2. Curiosity v2 / cluster (OPENSHELL_GATEWAY_ENDPOINT set to "host:port"):
     calls `SandboxClient(endpoint=...)` directly against an explicit
     gRPC address, bypassing the on-disk CLI state entirely -- necessary
     because Slurm jobs get fresh, ephemeral environments per submission,
     so relying on a CLI-populated home-directory file across separate job
     invocations would be fragile. This mirrors exactly how this project
     already handles Switchyard and the NIM containers: a persistent
     Slurm-scheduled service at a known hostname:port, referenced by env
     var, never hardcoded.

HONEST LIMITATION: mode 2 assumes the team can stand up a long-lived,
network-reachable OpenShell gateway as its own Slurm job (see
infra/slurm/openshell-gateway.sbatch and infra/CURIOSITY_V2_SETUP.md).
The exact CLI command to start such a gateway in "standalone daemon,
reachable by other processes" form -- as opposed to the auto-created
local flow -- is NOT confirmed against NVIDIA's documentation, which
only clearly documents local auto-creation and remote-over-SSH
(`openshell gateway start --remote user@host`, or `openshell gateway add
<url>` for an already-running gateway e.g. on Brev). This is flagged as
the first thing to verify on the real cluster, not asserted as tested.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import openshell

from app.core.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_WORKSPACE = "default"


class OpenShellSandboxSession:
    def __init__(self, sandbox_name: str, workspace: str = DEFAULT_WORKSPACE) -> None:
        self.sandbox_name = sandbox_name
        self.workspace = workspace
        self._client: openshell.SandboxClient | None = None

    def _connect(self) -> openshell.SandboxClient:
        settings = get_settings()
        if settings.openshell_gateway_endpoint:
            logger.info(
                "Connecting to OpenShell gateway at explicit endpoint %s (cluster mode).",
                settings.openshell_gateway_endpoint,
            )
            return openshell.SandboxClient(endpoint=settings.openshell_gateway_endpoint)
        logger.info("Connecting to OpenShell via from_active_cluster() (local dev mode).")
        return openshell.SandboxClient.from_active_cluster()

    async def start(self) -> None:
        self._client = self._connect()
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
