#!/bin/bash
# Runs the LifeShield backend as a plain Python process on a Curiosity v2
# compute node -- no Docker in OUR deployment stack. Submit with:
#   sbatch infra/slurm/backend.sbatch
#
# NOTE: `module load rootless-docker` below exists ONLY because the
# backend process itself calls into the OpenShell SDK
# (app/agents/openshell_sandbox.py), and OpenShell's own sandboxing is
# built on Docker -- that's NVIDIA's tool's requirement, not a choice made
# in this project's own infra. See infra/CURIOSITY_V2_SETUP.md for the
# full explanation and what's actually been verified vs. not.
#SBATCH --job-name=lifeshield-backend
#SBATCH --output=lifeshield-backend_%j.log
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=2

set -euo pipefail
cd "$(dirname "$0")/../.."   # repo root (backend/)

# Cluster docs' own examples always pair rootless-docker with a GPU
# allocation (--gres=gpu:1) -- unconfirmed whether that's a hard
# requirement of the module itself or just how NVIDIA's examples happen
# to be written. If this module load fails on a CPU-only allocation,
# that's the answer; add --gres=gpu:1 to this script's #SBATCH lines above.
module load rootless-docker

# Assumes a venv has already been created once per the cluster's own docs:
#   python3 -m venv .venv && .venv/bin/pip install -e .
source .venv/bin/activate

export LIFESHIELD_ENV="${LIFESHIELD_ENV:-prod}"
export SWITCHYARD_BASE_URL="${SWITCHYARD_BASE_URL:-http://localhost:4100/v1}"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
