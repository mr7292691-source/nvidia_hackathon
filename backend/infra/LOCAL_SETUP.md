# Running LifeShield AI Locally

Parallel to `infra/CURIOSITY_V2_SETUP.md`, for running on your own
machine instead of the cluster. Simpler in most ways (no Slurm, no
module system) — the one piece that's the same either way is OpenShell
needing Docker.

## Prerequisites

- Python 3.11+
- Node 18+ (for the frontend)
- Docker Desktop running (only needed for OpenShell — see Step 6)
- Git

## Step 1 — Get the code

```bash
git clone <repo>   # or: git bundle create/pull if you were given a bundle
cd nvidia_hackathon/backend
```

## Step 2 — Backend venv and dependencies

A normal local machine usually doesn't hit the `ensurepip`/PEP 668 issues
found on Curiosity v2 (those are specific to that cluster's minimal
Debian image), so stdlib `venv` should just work:

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

If you *do* hit either of those errors locally too, use the same fix as
the cluster doc: `curl -LsSf https://astral.sh/uv/install.sh | sh` then
`uv venv .venv && uv pip install -e ".[dev]" --python .venv/bin/python`.

## Step 3 — Configure `.env`

```bash
cp .env.example .env
```

Edit it:
```
NVIDIA_API_KEY=nvapi-...
SWITCHYARD_BASE_URL=http://localhost:4100/v1
DATABASE_URL=sqlite+aiosqlite:///./var/lifeshield.db
NEMO_RELAY_ATOF_OUTPUT_DIR=./var/atof
```

## Step 4 — Confirm real NIM model IDs

Same caveat as the cluster doc: `infra/switchyard/routes.dev.yaml`'s
placeholders are not safe to use as-is. **`nvidia/vila` is confirmed
deprecated** (its own build.nvidia.com page says so). Go to
`build.nvidia.com/explore/vision` and `build.nvidia.com/explore` for
current model IDs, then edit both `model:` fields in that file.

## Step 5 — Run Switchyard + backend

Two terminals (or one with `&`):

```bash
# Terminal 1
switchyard serve --routing-profiles infra/switchyard/routes.dev.yaml --port 4100

# Terminal 2
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Checkpoint:**
```bash
curl -X POST http://localhost:8000/events/replay/houston-demo
curl http://localhost:8000/agents/gates/<event_id>
```
Both should return clean JSON — this doesn't need OpenShell or a live NIM
call yet.

## Step 6 — OpenShell (needs Docker Desktop)

Per NVIDIA's own quickstart, this is genuinely required locally — there's
no way around it, it's how OpenShell's sandboxing works.

```bash
# Docker Desktop must already be running
uv venv .openshell-cli && uv pip install openshell --python .openshell-cli/bin/python
source .openshell-cli/bin/activate
which openshell || echo "CLI not found -- NVIDIA's own docs are inconsistent about whether pip install openshell includes the CLI or just the SDK; check github.com/NVIDIA/OpenShell's current README for the correct install method"
openshell sandbox create --from base
openshell status
```

If this succeeds, leave `OPENSHELL_GATEWAY_ENDPOINT` unset in `.env` —
the backend's `from_active_cluster()` call will pick up the gateway this
just created.

## Step 7 — Full pipeline

```bash
curl -X POST http://localhost:8000/replay/houston-event
```
This is the real end-to-end call: evidence → DeepAgents supervisor →
OpenShell sandbox → real NIM call via Switchyard → NeMo Relay-governed →
decision outputs.

## Step 8 — Frontend

```bash
cd ../frontend
npm install
cp .env.example .env
# set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```
Open the printed local URL (usually `http://localhost:5173`) in a browser.

## Stopping everything

- `Ctrl-C` in each terminal running Switchyard/uvicorn/`npm run dev`
- OpenShell sandbox: check `openshell sandbox --help` for the real
  cleanup command (not confirmed from docs, same caveat as the cluster
  guide)
- Docker Desktop: quit normally, or leave it running for next time
