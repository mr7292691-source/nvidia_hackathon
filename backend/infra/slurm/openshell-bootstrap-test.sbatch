#!/bin/bash
# Bootstraps OpenShell's local-mode auto-gateway on a Curiosity v2 compute
# node, using the cluster's rootless-docker module as the closest
# equivalent to OpenShell's "Docker Desktop running" prerequisite.
#
# HONEST STATUS: this is real, runnable code following the cluster's own
# documented rootless-docker pattern and OpenShell's own documented local
# quickstart -- but the combination of the two (OpenShell's Docker-based
# sandboxing against Curiosity v2's rootless Docker specifically) has NOT
# been tested. This script is the actual first thing to run on the real
# cluster to find out. If it fails, the error message itself is the next
# real debugging input -- don't assume either direction without running it.
#
#SBATCH --job-name=lifeshield-openshell-bootstrap
#SBATCH --output=lifeshield-openshell-bootstrap_%j.log
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1

set -euo pipefail
cd "$(dirname "$0")/../.."

# 1. Rootless Docker, per the cluster's own onboarding docs: "Request an
#    interactive Slurm session on a compute node, load the module, the
#    rootless docker daemon will start automatically."
module load rootless-docker

echo "Rootless Docker status:"
docker info 2>&1 | head -20 || {
  echo "docker info failed -- rootless-docker module may not have started the daemon correctly."
  exit 1
}

# 2. Activate the project venv (assumes it was already created once per
#    the cluster's own docs: python3 -m venv .venv && .venv/bin/pip install -e .)
source .venv/bin/activate

# 3. Confirm the openshell CLI is available. Per NVIDIA's docs, the PyPI
#    `openshell` package installs the SDK; whether it also provides the
#    `openshell` CLI binary is inconsistent between two pages of NVIDIA's
#    own documentation (one says pip is SDK-only and points to a separate
#    installer script; the quickstart page shows `uv pip install openshell`
#    as the CLI install step). Check which is actually true against
#    whatever version lands here:
which openshell || echo "openshell CLI not found on PATH -- check NVIDIA/OpenShell's current README for the correct CLI install method."

# 4. Bootstrap a sandbox once, which (per the quickstart) auto-creates a
#    local gateway against the Docker daemon found in this environment
#    (rootless-docker, in this case) if one doesn't already exist.
#    `--from base` is NVIDIA's own documented example command, used here
#    only to prove the gateway bootstrap path works.
#    NOTE: flags beyond what's shown in NVIDIA's quickstart (e.g. a
#    `--name` flag, or a `sandbox delete` subcommand) are NOT confirmed --
#    run `openshell sandbox create --help` / `openshell sandbox --help` on
#    the real system to find the actual flags for naming and cleanup
#    before scripting those parts.
openshell sandbox create --from base || {
  echo "openshell sandbox create failed. This is the real signal for whether"
  echo "OpenShell's Docker-based sandboxing works against rootless-docker on"
  echo "this cluster -- read the actual error above, don't guess."
  exit 1
}

echo "Bootstrap sandbox created successfully. Gateway state should now be at"
echo "~/.config/openshell/active_gateway for from_active_cluster() to use."
openshell status || true

echo "Bootstrap test complete. Clean up the sandbox manually with whatever"
echo "the real 'openshell sandbox ...' cleanup command turns out to be --"
echo "check 'openshell sandbox --help' since this wasn't confirmed from docs."
