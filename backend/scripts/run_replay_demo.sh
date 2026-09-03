#!/usr/bin/env bash
# Convenience script for the hackathon demo: hits the one-button replay
# endpoint and pretty-prints the result. Run the backend first (uvicorn
# app.main:app --reload) or via docker-compose.
set -euo pipefail

BASE_URL="${LIFESHIELD_BASE_URL:-http://localhost:8000}"

curl -s -X POST "${BASE_URL}/replay/houston-event" | python3 -m json.tool
