#!/bin/bash
# Pulls and runs the reasoning NIM container via Apptainer (no Docker),
# following the exact pattern the Curiosity v2 cluster docs demonstrate for
# NGC images: `apptainer pull ... docker://nvcr.io/...` then
# `apptainer run --nv`.
#SBATCH --job-name=lifeshield-nim-reasoning
#SBATCH --output=lifeshield-nim-reasoning_%j.log
#SBATCH --time=04:00:00
#SBATCH --gres=gpu:1

set -euo pipefail
cd "$(dirname "$0")/../.."

SIF_DIR="${SIF_DIR:-/storage/hackathon_teams/lifeshield/sif}"
mkdir -p "$SIF_DIR"

# TODO: confirm the exact NIM image tag once the team can reach nvcr.io and
# has generated an NGC_API_KEY (see plan.md item 2). Requires:
#   echo "$NGC_API_KEY" | apptainer registry login --username '$oauthtoken' --password-stdin docker://nvcr.io
NIM_IMAGE="${NIM_REASONING_IMAGE:-docker://nvcr.io/nim/nvidia/nemotron-4-340b-instruct:latest}"
SIF_PATH="$SIF_DIR/nim-reasoning.sif"

if [ ! -f "$SIF_PATH" ]; then
  apptainer pull "$SIF_PATH" "$NIM_IMAGE"
fi

echo "NIM reasoning container running on: $(hostname)"
exec apptainer run --nv "$SIF_PATH"
