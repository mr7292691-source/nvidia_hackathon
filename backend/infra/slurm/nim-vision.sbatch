#!/bin/bash
# Same pattern as nim-reasoning.sbatch, for the vision NIM.
#SBATCH --job-name=lifeshield-nim-vision
#SBATCH --output=lifeshield-nim-vision_%j.log
#SBATCH --time=04:00:00
#SBATCH --gres=gpu:1

set -euo pipefail
cd "$(dirname "$0")/../.."

SIF_DIR="${SIF_DIR:-/storage/hackathon_teams/lifeshield/sif}"
mkdir -p "$SIF_DIR"

NIM_IMAGE="${NIM_VISION_IMAGE:-docker://nvcr.io/nim/nvidia/vila:latest}"
SIF_PATH="$SIF_DIR/nim-vision.sif"

if [ ! -f "$SIF_PATH" ]; then
  apptainer pull "$SIF_PATH" "$NIM_IMAGE"
fi

echo "NIM vision container running on: $(hostname)"
exec apptainer run --nv "$SIF_PATH"
