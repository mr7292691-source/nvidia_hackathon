#!/bin/bash
# Runs the real Switchyard proxy (pip package `nemo-switchyard`, verified
# working — see infra/switchyard/routes.dev.yaml) as a native process.
# No Docker, no Rust toolchain needed — it ships a prebuilt manylinux wheel.
#SBATCH --job-name=lifeshield-switchyard
#SBATCH --output=lifeshield-switchyard_%j.log
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=1

set -euo pipefail
cd "$(dirname "$0")/../.."

source .venv/bin/activate

ROUTES_FILE="${SWITCHYARD_ROUTES_FILE:-infra/switchyard/routes.prod.yaml}"

exec switchyard serve --routing-profiles "$ROUTES_FILE" --host 0.0.0.0 --port 4100
