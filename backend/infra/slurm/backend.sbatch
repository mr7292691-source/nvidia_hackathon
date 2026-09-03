#!/bin/bash
# Runs the LifeShield backend as a plain Python process on a Curiosity v2
# compute node — no Docker. Submit with: sbatch infra/slurm/backend.sbatch
#SBATCH --job-name=lifeshield-backend
#SBATCH --output=lifeshield-backend_%j.log
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=2

set -euo pipefail
cd "$(dirname "$0")/../.."   # repo root (backend/)

# Assumes a venv has already been created once per the cluster's own docs:
#   python3 -m venv .venv && .venv/bin/pip install -e .
source .venv/bin/activate

export LIFESHIELD_ENV="${LIFESHIELD_ENV:-prod}"
export SWITCHYARD_BASE_URL="${SWITCHYARD_BASE_URL:-http://localhost:4100/v1}"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
