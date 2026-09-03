# Running LifeShield AI on Curiosity v2

This doc separates what's actually verified from what's a reasonable next
step someone needs to test on the real cluster. Nothing here has been run
against Curiosity v2 -- the sandbox this project was built in has no
cluster access and a network policy that blocks even build.nvidia.com.

## 1. Baseline setup (standard for any Python project on this cluster)

Per the cluster's own onboarding docs:

```bash
ssh username@slogin01
cd /storage/hackathon_teams/<your-team>/
git clone <this repo>
cd nvidia_hackathon/backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
# edit .env: set NVIDIA_API_KEY, DATABASE_URL, etc.
```

**Not run on the login node** -- per the cluster's own warning, all of the
below should happen inside an `srun`/`sbatch` job on a compute node, not
`slogin01`.

## 2. Switchyard + NeMo Relay + DeepAgents: verified logic, unverified network

These three run as plain processes, no special cluster accommodation
needed beyond a working venv:

```bash
srun --qos=1gpu --gres=gpu:1 --pty bash
module load rootless-docker   # only needed if you'll also test OpenShell in this session
source .venv/bin/activate
switchyard serve --routing-profiles infra/switchyard/routes.dev.yaml --port 4100 &
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

What's real and tested (in a sandboxed environment with no route to
build.nvidia.com, but the code paths themselves): Switchyard starts,
serves `/v1/models` correctly, and correctly attempts a real upstream
call. On Curiosity v2, with real internet access and a real
`NVIDIA_API_KEY`, this call should actually complete -- that's the one
thing this project genuinely could not verify end-to-end and needs
someone with real access to confirm.

**Before this works**: confirm the exact NIM model IDs in
`infra/switchyard/routes.dev.yaml` against build.nvidia.com's current
catalog -- the ones there now (`nvidia/nemotron-4-340b-instruct`,
`nvidia/vila`) are unverified placeholders.

## 3. OpenShell: the genuinely open question

NVIDIA's own OpenShell quickstart lists **Docker Desktop running** as a
hard prerequisite for local-mode sandboxing. Curiosity v2 doesn't have
Docker Desktop, but does have `rootless-docker` as a loadable module
(per the cluster's own docs, automatically starting a rootless Docker
daemon in that session).

**What's confirmed:**
- OpenShell can run "on a single local machine" using Docker/Podman/VM as
  its backend (from NVIDIA's own architecture docs)
- The `openshell` Python package's `SandboxClient` supports both
  `from_active_cluster()` (reads local CLI state) and a direct
  `SandboxClient(endpoint="host:port")` constructor (explicit gRPC
  address) -- this project's `openshell_sandbox.py` supports both,
  switchable via `OPENSHELL_GATEWAY_ENDPOINT`

**What's NOT confirmed** (this is the actual list of things to test, in
order):

1. **Does OpenShell's Docker-based sandboxing work against rootless
   Docker at all?** Untested by NVIDIA's docs or by this project. Run
   `infra/slurm/openshell-bootstrap-test.sbatch` -- it's written to
   surface exactly this as a pass/fail with a real error message, not to
   assume the answer either way.
2. **Whether the `openshell` PyPI package includes the CLI binary.**
   NVIDIA's own docs disagree with each other on this (the GitHub README
   says pip installs SDK-only; the quickstart page shows `uv pip install
   openshell` as the CLI install step). Check `github.com/NVIDIA/OpenShell`'s
   current README before assuming either is still true.
3. **Whether a long-lived, network-reachable gateway can be started as
   its own persistent Slurm job**, so the backend (running in a separate
   job) can connect via `OPENSHELL_GATEWAY_ENDPOINT=host:port` instead of
   both processes needing to share the same session's on-disk CLI state.
   NVIDIA's docs only clearly document local auto-creation (same session)
   and remote-over-SSH (`--remote user@host`, for deploying TO a
   different machine you SSH into) -- neither is quite "start a daemon
   here, let other processes on other nodes connect to it by address."
   This may just work with `openshell gateway start` run without
   `--remote`; it may not. Test it.

**If none of this works within your hackathon timeline**: the fallback is
running the backend (with `OPENSHELL_GATEWAY_ENDPOINT` unset, i.e. local
mode) and the OpenShell-dependent code in the *same* Slurm session/job
where `module load rootless-docker` ran and a sandbox was already created
once -- this is the one flow NVIDIA's docs actually walk through
end-to-end, even though it wasn't tested against rootless Docker
specifically.

## 4. NIM containers (self-hosted, prod routing)

```bash
sbatch infra/slurm/nim-reasoning.sbatch
sbatch infra/slurm/nim-vision.sbatch
squeue -u $USER   # find the allocated node hostnames
```

Update `infra/switchyard/routes.prod.yaml`'s `${NIM_REASONING_HOST}` /
`${NIM_VISION_HOST}` (or export them as env vars) to match, then:

```bash
export LIFESHIELD_ENV=prod
export SWITCHYARD_ROUTES_FILE=infra/switchyard/routes.prod.yaml
sbatch infra/slurm/switchyard.sbatch
sbatch infra/slurm/backend.sbatch
```

Requires `NGC_API_KEY` to pull the NIM images from `nvcr.io` via Apptainer
-- see `docs/plan.md` §5 for what credentials are needed from whom.

## 5. Definition of done for "runs on Curiosity v2"

- [ ] `switchyard serve` completes a real chat completion against
      build.nvidia.com (dev mode) or self-hosted NIM (prod mode)
- [ ] `openshell-bootstrap-test.sbatch` succeeds, proving OpenShell +
      rootless-docker actually works (or documents that it doesn't, with
      a real error to work from)
- [ ] `POST /replay/houston-event` completes end-to-end against real
      infrastructure, including an actual DeepAgents graph invocation
- [ ] The blocked-egress test from `docs/plan.md` Phase 1 actually runs:
      confirm an agent inside a real OpenShell sandbox cannot reach an
      arbitrary external host

None of these are done yet. This doc exists so whoever has real cluster
access can work through them in order, with the genuinely uncertain parts
flagged instead of glossed over.
