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

## Step 2 — Interactive GPU session and set up the venv (once)

```bash
srun --qos=1gpu --gres=gpu:1 --pty bash

# Confirmed on the real cluster, three real issues in sequence:
# 1. `python3 -m venv` fails: "ensurepip is not available" (missing
#    python3.12-venv system package, no sudo on a shared cluster).
# 2. `pip install --user uv` (the obvious workaround) then fails with a
#    DIFFERENT error: "externally-managed-environment" (PEP 668 --
#    modern Debian/Ubuntu blocks pip installs outside a venv).
# 3. After fixing 1+2 with uv's own installer, `uv pip install -e .`
#    failed with a THIRD error: setuptools' flat-layout auto-discovery
#    choked on `infra/` sitting next to `app/` at the repo root. Fixed in
#    pyproject.toml (explicit packages.find + build-system block) --
#    pull the latest commit/bundle to get this fix.
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv venv .venv
uv pip install -e ".[dev]" --python .venv/bin/python

cp .env.example .env
```

Fallback if the cluster blocks outbound HTTPS to astral.sh (unlikely --
`module load rootless-docker` already needs network access): pip's
explicit override flag, still without a venv:
```bash
python3 -m pip install --user --break-system-packages -e ".[dev]"
```

Edit `.env` and set at minimum:
```
NVIDIA_API_KEY=nvapi-...          # from build.nvidia.com
DATABASE_URL=sqlite+aiosqlite:///./var/lifeshield.db
NEMO_RELAY_ATOF_OUTPUT_DIR=./var/atof
```

## Step 3 — Confirm the real NIM model IDs

`infra/switchyard/routes.dev.yaml` has **placeholder** model IDs — and one
of them is worse than just unverified: **`nvidia/vila` is confirmed
deprecated** (its own build.nvidia.com page says so directly). The
reasoning model ID (`nvidia/nemotron-4-340b-instruct`) is merely
unverified, not confirmed-bad, but the catalog is volatile enough right
now (several other models across NVIDIA's catalog are mid-deprecation on
short notice) that it shouldn't be trusted either.

1. Go to `build.nvidia.com/explore/vision` for a current vision model,
   and `build.nvidia.com/explore` (or search Nemotron directly) for the
   reasoning model
2. Copy their exact current catalog IDs
3. Edit `infra/switchyard/routes.dev.yaml`, replacing both `model:` values

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

---

## Alternative: running via JupyterHub instead of SSH + Slurm

Everything above assumes SSH access and `srun`/`sbatch`. If you're running
through the Axis Portal's Curiosity Hub app (JupyterHub) instead, the
steps are similar but not identical — and it introduces one new open
question worth flagging up front.

**New uncertainty this path introduces:** JupyterHub notebook sessions
are a different execution environment than an `srun` shell — the cluster
docs list "Kubernetes workloads" and "web-based interactive notebooks" as
separate items, which suggests the Jupyter environment may be a
Kubernetes pod rather than a direct Slurm compute-node shell. That
matters because:
- `module load rootless-docker` (Lmod-style, shown in the Slurm docs) may
  or may not be available inside a Jupyter session's shell at all
- Even if it is, nested Docker-in-a-pod is often blocked or needs a
  privileged pod in typical Kubernetes setups — unrelated to anything in
  this project, just how Kubernetes usually works
- **This needs to be tested directly as step 1 below, not assumed either way.**

### JB-1. Launch the notebook session

Axis Portal → Curiosity Hub app → log in with cluster credentials → for
hackathons, choose your GPU/CPU/memory allocation (pick at least 1 GPU,
matching what Switchyard/NIM need elsewhere in this setup).

### JB-2. Open a Terminal, not just notebook cells

JupyterLab has a real terminal (File → New → Terminal). Use it for
anything long-running (Switchyard, the backend) — a notebook cell that
runs `uvicorn ...` directly will just block forever rather than let you
continue working. If you specifically want notebook cells instead, use
`!command &` with `nohup` and output redirection so the process detaches
(shown below); the Terminal is simpler and more predictable for this.

### JB-3. Test the module system first (the actual open question)

**CONFIRMED WORKING on the real cluster (2026-09-03):** `module load
rootless-docker` succeeds inside a JupyterHub session and starts the
daemon correctly ("✓ Rootless Docker daemon started successfully!").
This means the Jupyter environment does have Slurm module-system access,
at least for this — the earlier concern that Jupyter sessions might be a
more restricted Kubernetes pod without this access turned out not to
apply here. Good news for the OpenShell path specifically.

```bash
module load rootless-docker 2>&1
docker info 2>&1 | head -5
```

### JB-4. Set up the project (same as the SSH path, in the Terminal)

**Real issues hit on the cluster (2026-09-03), in order:**

1. `python3 -m venv .venv` fails: `ensurepip is not available` (missing
   `python3.12-venv` system package, no `sudo` on a shared cluster).
2. `pip install --user uv` (the obvious workaround) then fails with a
   **different** real error: `externally-managed-environment` (PEP 668 --
   modern Debian/Ubuntu blocks `pip install` outside a venv by default).
3. After fixing 1+2 with `uv`, `uv pip install -e ".[dev]"` fails with a
   **third** real error: `Multiple top-level packages discovered in a
   flat-layout: ['app', 'infra']` -- setuptools' auto-discovery got
   confused by `infra/` (Slurm scripts/YAML/markdown, not Python code)
   sitting alongside `app/` at the repo root, and refused to guess which
   one to package. **Fixed in `pyproject.toml`** (explicit
   `[tool.setuptools.packages.find] include = ["app*"]` + an explicit
   `[build-system]` block) -- verified with a clean install into a fresh
   throwaway venv, package imports correctly, full test suite still
   17/17 passing. If you pulled this repo before that fix landed,
   `git pull`/re-apply the bundle to pick it up.

**Working sequence, all three fixes applied:**

```bash
cd /storage/hackathon_teams/<your-team>/
git clone <repo>   # or apply the git bundle you were given
cd nvidia_hackathon/backend

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv venv .venv
uv pip install -e ".[dev]" --python .venv/bin/python

cp .env.example .env
# edit .env: NVIDIA_API_KEY, etc. -- nano .env or JupyterLab's file editor
```

**Fallback** if the cluster blocks outbound HTTPS to astral.sh (unlikely
-- `module load rootless-docker` already needed network access): use
pip's explicit override flag instead, still without a venv:
```bash
python3 -m pip install --user --break-system-packages -e ".[dev]"
```
If you use this fallback, drop `source .venv/bin/activate` from the steps
below — there's no venv to activate.

### JB-5. Run Switchyard + backend as detached background processes

From the Terminal:

```bash
source .venv/bin/activate
nohup switchyard serve --routing-profiles infra/switchyard/routes.dev.yaml --port 4100 > switchyard.log 2>&1 &
export SWITCHYARD_BASE_URL=http://localhost:4100/v1
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
tail -f switchyard.log backend.log   # Ctrl-C to stop watching, processes keep running
```

If doing this from notebook cells instead of the Terminal, each `!`
shell-magic line becomes its own cell, e.g.:
```python
!nohup switchyard serve --routing-profiles infra/switchyard/routes.dev.yaml --port 4100 > switchyard.log 2>&1 &
```

### JB-6. Hit the same checkpoint as the SSH path -- from within the notebook, not a browser

Since JupyterHub likely doesn't expose arbitrary backend ports to your
browser without a proxy extension (unconfirmed either way for this
cluster), the reliable way to test is from Python in a notebook cell,
same machine:

```python
import httpx
r = httpx.post("http://localhost:8000/events/replay/houston-demo")
print(r.json())
event_id = r.json()["event_id"]
print(httpx.get(f"http://localhost:8000/agents/gates/{event_id}").json())
```

This should return clean JSON exactly like the SSH path's `curl`
checkpoint — if it does, dev-mode Switchyard + backend genuinely works
from a JupyterHub session, independent of the OpenShell question above.

### JB-7. Frontend access

Getting a browser to actually reach the backend from outside the Jupyter
session likely needs either `jupyter-server-proxy` (if installed on this
JupyterHub — check `pip list | grep jupyter-server-proxy` from the
Terminal) or an SSH tunnel if SSH access to the same node is available in
parallel. Neither is confirmed for this specific cluster. If neither
works, the notebook-based `httpx` calls in JB-6 are still a complete way
to exercise and demo the backend's real behavior without needing the
React frontend running against it live.
