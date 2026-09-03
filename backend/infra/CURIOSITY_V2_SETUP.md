# Running LifeShield AI on Curiosity v2 — Step by Step

Nothing in this doc has been run against the real cluster — this sandbox
has no cluster access and a network policy that blocks even
build.nvidia.com. Steps 1–4 are standard/low-risk. Step 5 (OpenShell) is
the genuinely open question — it's written to give you a real pass/fail,
not to assume the answer.

---

## Step 1 — Get the code onto the cluster

```bash
ssh <username>@slogin01
cd /storage/hackathon_teams/<your-team>/
git clone <this repo's URL, or apply the git bundle you were given>
cd nvidia_hackathon/backend
```

Everything from here on happens **inside a Slurm job, not on `slogin01`**
— per the cluster's own onboarding docs, the login node isn't for
compute.

## Step 2 — Get an interactive GPU session and set up the venv (once)

```bash
srun --qos=1gpu --gres=gpu:1 --pty bash

python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` and set at minimum:
```
NVIDIA_API_KEY=nvapi-...          # from build.nvidia.com
DATABASE_URL=sqlite+aiosqlite:///./var/lifeshield.db
NEMO_RELAY_ATOF_OUTPUT_DIR=./var/atof
```

## Step 3 — Confirm the real NIM model IDs

`infra/switchyard/routes.dev.yaml` currently has **placeholder** model
IDs (`nvidia/nemotron-4-340b-instruct`, `nvidia/vila`) — unverified since
this project's own sandbox couldn't reach build.nvidia.com. Before
anything else works:

1. Log into build.nvidia.com, find the actual reasoning model (Nemotron
   family) and vision model you want to use
2. Copy their exact catalog IDs
3. Edit `infra/switchyard/routes.dev.yaml`, replacing the two placeholder
   `model:` values

## Step 4 — Bring up Switchyard + the backend, verify the real dev path

Still inside your `srun` session:

```bash
source .venv/bin/activate

# Terminal/pane 1:
switchyard serve --routing-profiles infra/switchyard/routes.dev.yaml --port 4100

# Terminal/pane 2 (or background the above with &):
export SWITCHYARD_BASE_URL=http://localhost:4100/v1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Checkpoint — this should now work end-to-end for the first time:**

```bash
curl -X POST http://localhost:8000/events/replay/houston-demo
# copy the returned event_id, then:
curl http://localhost:8000/agents/gates/<event_id>
```

Both of these don't need OpenShell or a live NIM call — if they don't
return clean JSON, something in steps 1–3 needs fixing before going
further.

## Step 5 — OpenShell: the real open question

This is the part that genuinely needs testing, not assuming.

```bash
# Still in the same srun session:
module load rootless-docker
docker info   # confirm the rootless daemon actually started

which openshell || echo "CLI not found -- check github.com/NVIDIA/OpenShell's current README"

sbatch infra/slurm/openshell-bootstrap-test.sbatch
# or run its commands directly in your interactive session instead of
# submitting as a separate job, since you're already in one:
openshell sandbox create --from base
openshell status
```

- **If `openshell sandbox create` succeeds:** OpenShell's Docker-based
  sandboxing works against Curiosity v2's rootless Docker. Leave
  `OPENSHELL_GATEWAY_ENDPOINT` unset in `.env` (local-dev mode) and run
  the backend in this same session — `from_active_cluster()` will pick up
  the gateway state this just created.
- **If it fails:** read the actual error. Common failure modes to check
  first: rootless Docker socket path not matching what OpenShell expects,
  or a permissions issue specific to the cluster's rootless setup. This
  is real debugging territory now, not something this doc can predict.

## Step 6 — Run the full pipeline for real

Once step 5 resolves one way or another, in the same session:

```bash
curl -X POST http://localhost:8000/replay/houston-event
```

This is slide 5's full flow end to end: evidence bundling → DeepAgents
supervisor (inside the OpenShell sandbox, if step 5 worked) → real NIM
calls via Switchyard → NeMo Relay-governed → decision outputs. If step 5
didn't work, this call will fail specifically at the `openshell_session()`
context manager — that failure is informative (confirms exactly where the
gap is), not a dead end.

## Step 7 — Prod mode: self-hosted NIM containers

Once dev mode (steps 1–6) works:

```bash
# Get an NGC_API_KEY from ngc.nvidia.com first, needed to pull nvcr.io images
sbatch infra/slurm/nim-reasoning.sbatch
sbatch infra/slurm/nim-vision.sbatch
squeue -u $USER   # note the allocated node hostnames
```

Edit `infra/switchyard/routes.prod.yaml`'s `${NIM_REASONING_HOST}` /
`${NIM_VISION_HOST}` (or export them as env vars) to match those
hostnames, then:

```bash
export LIFESHIELD_ENV=prod
export SWITCHYARD_ROUTES_FILE=infra/switchyard/routes.prod.yaml
sbatch infra/slurm/switchyard.sbatch
sbatch infra/slurm/backend.sbatch
```

Re-run the Step 6 checkpoint against this prod deployment and confirm
identical output shape to dev.

## Step 8 — Frontend

On your own machine (not the cluster, unless you also want to serve it
from there):

```bash
cd frontend
npm install
cp .env.example .env
# set VITE_API_BASE_URL to wherever the backend from step 4/7 is reachable
npm run dev
```

If the backend is only reachable inside the cluster's network, you'll
need either an SSH tunnel (`ssh -L 8000:localhost:8000 ...`) or to serve
the frontend from a node with the right network access — same general
pattern as reaching JupyterHub per the cluster's own docs.

---

## Definition of done

- [ ] Step 4's checkpoint returns clean JSON
- [ ] Step 5 resolves (either OpenShell works against rootless Docker, or
      you've documented that it doesn't and picked a fallback)
- [ ] Step 6's full pipeline call completes without error
- [ ] Step 7's prod mode matches dev mode's output shape
- [ ] The blocked-egress test from `docs/plan.md` Phase 1 runs: confirm
      an agent inside a real OpenShell sandbox cannot reach an arbitrary
      external host

None of these are checked off yet — this doc exists so whoever has real
cluster access can work through them in order.
