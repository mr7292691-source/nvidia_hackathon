# LifeShield AI — Remaining Work Plan

NVIDIA GSI Open Hackathon · Team Cognitive Core
Repo target: `https://github.com/mr7292691-source/nvidia_hackathon.git`

**Revision note:** this replaces the previous version. Two changes at your
request: (1) no Docker anywhere — replaced with Apptainer/Slurm-native
tooling, which is what the Curiosity v2 cluster actually supports; (2) no
stubs — every task below is scoped as "build the real thing," not
"placeholder now, replace later." See §5 for what I need from you before
any of this can actually run.

---

## 0. Assumption this plan is built on — please confirm

You previously chose **separate frontend/backend repos**, but only **one**
GitHub URL has been given. This plan assumes `nvidia_hackathon.git` is a
**monorepo**:

```
nvidia_hackathon/
├── backend/     <- current lifeshield-backend/ contents, minus infra/docker/
├── frontend/    <- current lifeshield-frontend/ contents
├── infra/       <- Apptainer + Slurm job definitions (replaces infra/docker)
├── docs/        <- architecture notes, this plan, demo script
└── README.md    <- top-level project overview + quickstart for both halves
```

If you actually want two separate GitHub repos, say so and I'll adjust.

**No git commands have been run yet.** Every push to `nvidia_hackathon.git`
is proposed in chat first, with the exact commit message and file list, and
only run after you say yes.

---

## 1. What "no Docker" changes, concretely

| Was (previous plan/code) | Becomes |
|---|---|
| `infra/docker/Dockerfile.backend` | Backend runs as a plain Python process (`uvicorn app.main:app`), launched via a Slurm batch script (`infra/slurm/backend.sbatch`) on the B300 node, or directly with `srun` for interactive dev sessions |
| `infra/docker/docker-compose.yml` (backend + Switchyard sidecar) | Switchyard runs as its own native binary (built once via `cargo build --release -p switchyard-server`, no container) as a separate Slurm job/service; backend talks to it over the cluster's internal network by hostname:port, same as before — only the packaging changes |
| `infra/switchyard/Dockerfile.switchyard` | Deleted. Switchyard is a single Rust binary — build it once on a compute node, keep the binary in team shared storage (`/storage/hackathon_teams/...` per the cluster's storage layout), no image to maintain |
| Self-hosted NIM containers via `docker run --gpus all ...` | Same NIM images, pulled and run via **Apptainer**: `apptainer pull nim-reasoning.sif docker://nvcr.io/nim/nvidia/<model>:latest` then `apptainer run --nv nim-reasoning.sif`, scheduled via `sbatch`/`srun --gres=gpu:1`. This is literally the pattern the cluster's own onboarding docs demonstrate for NGC images without root. |
| `infra/k8s/*.yaml` | Deprioritized, not deleted yet — Kubernetes on this cluster still expects OCI images, which without a Docker daemon means building via `apptainer build --oci` or `buildah`. This is unresolved tooling, flagged in §4, and shouldn't block the Slurm/Apptainer path which is proven to work per the cluster's own docs. |
| Local dev via `docker-compose up` | No local containers at all. Dev backend talks **directly** to `https://integrate.api.nvidia.com/v1` through Switchyard-the-binary running locally (or even bypassed entirely for the earliest dev loop — Switchyard only matters once you need the dev/prod routing swap). No Docker Desktop, no daemon, nothing to install beyond Python + the Switchyard binary. |

---

## 2. What "no stubs" changes, concretely

Every item below was previously either an always-pass function, an
in-memory dict standing in for persistence, or manual function-calling
sequencing standing in for a real agent graph. All of that gets replaced
directly — there is no intermediate "stub" checkpoint being planned for.

| File (as it exists today) | Stub behavior today | Real implementation required |
|---|---|---|
| `app/agents/gates/evidence_verifier.py` | Always returns `passed=True` | Real freshness/location/source-agreement scoring against a persisted `EvidenceRecord`, with the thresholds (`MAX_STALENESS`, `MIN_CORROBORATING_SOURCES`) actually enforced |
| `app/agents/gates/confidence_gate.py` | Always returns `passed=True` | Real threshold check against the vision NIM's structured confidence output + evidence verifier score |
| `app/agents/gates/policy_verifier.py` | Always returns `passed=True` | Real check against `insurer_exposure.py`'s computed figures |
| `app/agents/tools/evidence_tools.py` `_EVENT_STORE`, `_FIELD_IMAGES` | In-memory dicts | Real persistence (Postgres or SQLite via `app/db/`, tables actually defined and migrated) |
| `app/agents/tools/notify_tools.py` `_APPROVAL_QUEUE` | In-memory dict | Same — real persistence, survives a process restart |
| `app/agents/openshell_sandbox.py` | `start()`/`stop()` log a message and do nothing | Real OpenShell sandbox lifecycle calls, with a verified test that egress to a non-allowlisted host is actually blocked from inside it |
| `app/agents/supervisor.py` | Manually calls each specialist in a fixed sequence | Real `deepagents.create_deep_agent(...)` supervisor with the four specialists registered as sub-agents, letting the model decide delegation/re-query order |
| `app/nvidia_runtime/relay/relay_runtime.py`, `guardrails.py` | `try/except ImportError` falls back to an ungoverned call | `nemo-relay` actually installed, imported, and required — if it's not importable, the app should fail to start, not silently run ungoverned |
| Evidence adapters' `mode="replay"` | Fine to keep for the demo dataset, but... | ...the `live` branches currently `raise NotImplementedError` — these need real implementations for NWS/USGS/FEMA (open, no-key endpoints) rather than staying permanently unimplemented |
| `damage_severity_factor = 0.5` hardcoded in `decisions.py`/`replay.py` | Placeholder constant | Real deterministic mapping from the vision NIM's structured output to a severity factor |

**Practical effect on sequencing:** the plan is no longer "scaffold everything,
then circle back." Each phase below only counts as done when the real
version works — there's no partial-credit "the interface exists" milestone.

---

## 3. Phase plan

### Phase 0 — Repo + infra setup
- [ ] Confirm monorepo structure (§0) and branching model (§6)
- [ ] Restructure into `backend/` + `frontend/` + `infra/` + `docs/`
- [ ] Delete `infra/docker/` and `infra/switchyard/Dockerfile.switchyard`
- [ ] Add `infra/slurm/backend.sbatch`, `infra/slurm/switchyard.sbatch`, `infra/slurm/nim-reasoning.sbatch`, `infra/slurm/nim-vision.sbatch`
- [ ] Add `infra/apptainer/` with the `.def` files (or documented `apptainer pull` commands) for each NIM image
- [ ] Root `README.md`, root `.gitignore`
- [ ] **First commit + push** — proposed in chat, needs your go-ahead

### Phase 1 — NVIDIA runtime, built real from the start
- [ ] Pin exact NIM model IDs (reasoning + vision) after testing candidates on build.nvidia.com
- [ ] Build Switchyard from source once (`cargo build --release -p switchyard-server`), place the binary in team shared storage, write `infra/slurm/switchyard.sbatch` to run it
- [ ] Validate `routes.dev.toml` with `switchyard-server --config routes.dev.toml --dry-run`
- [ ] Install `nemo-relay`, confirm the actual Python API matches what's coded in `relay_runtime.py`/`guardrails.py` — adjust to match reality, not the other way around
- [ ] Wire real ATOF export, confirm a trajectory file is produced after a real run
- [ ] Install `deepagents` + `langchain-nvidia-ai-endpoints`, rewrite `supervisor.py` as a real `create_deep_agent(...)` graph
- [ ] Stand up a real OpenShell sandbox per the `langchain-ai/openshell-deepagent` reference; write and run an actual blocked-egress test (agent tries to reach an external host, confirm it fails)
- [ ] **Definition of done:** one real end-to-end call — DeepAgents supervisor → specialist → NIM via Switchyard → Relay-recorded ATOF trajectory — succeeds against build.nvidia.com, no fallback paths taken

### Phase 2 — Persistence (prerequisite for real gates)
- [ ] Choose SQLite (simplicity) or Postgres (durability across cluster restarts) — recommend SQLite for the demo given time constraints, revisit if the team wants it running unattended for longer
- [ ] Define real tables in `app/db/models.py` for `EvidenceRecord`, `LifeSafetyGuidance`, `InsurerExposureReport`, approval queue entries
- [ ] Replace `_EVENT_STORE`, `_FIELD_IMAGES`, `_APPROVAL_QUEUE` with real DB-backed reads/writes
- [ ] Add a migration tool (Alembic) so schema changes are tracked, not ad hoc

### Phase 3 — Decision gates, built real
- [ ] Implement real scoring in `evidence_verifier.py` against persisted lineage data
- [ ] Define the vision NIM's structured output schema so `confidence_gate.py` has a real number to threshold
- [ ] Implement `policy_verifier.py` against real computed exposure figures
- [ ] **Proof required by the deck (slide 6):** a deliberately low-confidence case returns a clean "evidence gap" response, not a 500
- [ ] Surface structured gate pass/fail/reason through `/agents/run` so `GatesPanel.tsx` shows real state

### Phase 4 — Evidence layer, live sources where feasible now
- [ ] NWS: implement `live` mode against `api.weather.gov/alerts` (no key required) — no reason this stays unimplemented
- [ ] USGS: implement `live` mode against `waterservices.usgs.gov/nwis/iv/` (no key required)
- [ ] FEMA: implement `live` mode against the NFHL public feed
- [ ] HCFCD / TranStar: genuinely blocked on access coordination (per the deck itself) — replay mode stays until access is granted, at which point implement without changing the `SourceRecord` contract. This is the one legitimate exception to "no stubs," because it's an external dependency outside the team's control, not a shortcut.

### Phase 5 — Frontend, real backend integration
- [ ] Replace `EventMap.tsx`'s JSON dump with a real MapLibre GL map (event polygon + gauge/roadway markers)
- [ ] Wire `GatesPanel` to real per-gate results (needs Phase 3 first)
- [ ] Fix `Dashboard.tsx`'s navigation to trigger off a real store update, not a timing assumption
- [ ] Real auth/identity for `ApprovalQueue.tsx`, replacing the hardcoded `"demo-operator"` — needs a decision on what auth the team is using (see §5, item 6)
- [ ] Consistent loading/error states across all pages
- [ ] Run the frontend against the real backend (not just isolated `tsc`/`vite build` checks) and fix whatever breaks

### Phase 6 — Testing & CI
- [ ] Backend: unit tests for the real gate logic, evidence lineage builder, live adapter parsing
- [ ] Backend: integration test against a real (or recorded) NIM response via Switchyard
- [ ] Frontend: component tests (Vitest + React Testing Library) for `GatesPanel`, `InsurerExposureCard`, `LifeSafetyCard`
- [ ] GitHub Actions: `backend-ci.yml` (ruff, mypy, pytest) and `frontend-ci.yml` (eslint, tsc, vite build) — no Docker needed for either, both run directly on GitHub's runners
- [ ] Both must pass before any push to `main` per §6

### Phase 7 — Deployment on Curiosity v2 (Slurm + Apptainer, no Docker)
- [ ] Pull NIM images via Apptainer (`apptainer pull ... docker://nvcr.io/nim/...`), confirm they run with `--nv` GPU passthrough
- [ ] Submit `sbatch` jobs for backend, Switchyard, and both NIM containers
- [ ] Confirm `routes.prod.toml` targets resolve to the running Slurm jobs' node hostnames/ports
- [ ] Flip `LIFESHIELD_ENV=prod`, re-run the Houston replay demo against the B300-hosted stack, confirm identical output shape to dev
- [ ] Rehearse the full demo end to end at least twice before presenting

### Phase 8 — Demo readiness
- [ ] `docs/demo_script.md` — exact click-path reproducing the deck's slide 5 flow
- [ ] Fallback recording/screenshots in case live B300 access is flaky during presentation
- [ ] Live confirmation in front of the team that an agent genuinely cannot reach the open internet from inside its OpenShell sandbox

---

## 4. Open risks

| Risk | Response | Status |
|---|---|---|
| TranStar/HCFCD live feeds need access coordination | Replay fixtures stay until access is granted (only sanctioned exception to "no stubs") | Tracked, Phase 4 |
| Insurer data sensitivity | Synthetic/de-identified portfolio only | Already enforced by design |
| Sources can conflict/go stale | Evidence verifier real scoring | Phase 3, not yet built |
| Model cold-start on B300 | Keep model weights cached in team storage between Slurm job restarts | Not started |
| `nemo-relay`/`deepagents` real API may differ from documented shape assumed in code | First thing to verify, Phase 1 | Unverified |
| Kubernetes path needs an OCI image without Docker | Unresolved — Slurm+Apptainer path doesn't depend on this, so it's not blocking, but flag if the team specifically needs K8s | Deprioritized, not solved |
| No Docker means no `docker-compose up` one-liner for local dev | Slightly more manual local setup (run Switchyard binary + uvicorn separately) — acceptable trade-off for matching cluster-native tooling | Accepted |

---

## 5. What I need from you (credentials & access)

I want to be specific about what's actually needed, who needs to hold it, and
what I should never be given directly.

1. **`NVIDIA_API_KEY` (starts with `nvapi-`)** — from build.nvidia.com. Needed
   for all dev-time NIM calls (reasoning + vision) via Switchyard.
   → Put this in `backend/.env` yourself (or whoever sets up the dev
   environment). **Please don't paste it into this chat** — I don't need to
   see the raw value to write the code that reads it from the environment.

2. **`NGC_API_KEY`** — from ngc.nvidia.com (the same key associated with your
   build.nvidia.com account usually works). Needed to pull NIM container
   images from `nvcr.io` via Apptainer on the B300 node
   (`apptainer pull ... docker://nvcr.io/nim/...`).
   → Same as above: goes into the cluster environment directly, not into
   chat.

3. **Curiosity v2 cluster SSH credentials** (username/password, separate
   from the Axis event portal login) — needed by whoever actually runs the
   `sbatch`/`srun`/`apptainer` commands on the cluster. **I cannot SSH into
   the cluster from this sandboxed environment** — I can write the job
   scripts and commands for your team to run, but someone with cluster
   access has to execute them.

4. **Axis event portal login** — for the web UI (JupyterHub, Curiosity v2
   Login app, DGX Cloud Login app). Same as above — for your team's use,
   not something I need.

5. **GitHub authentication for `nvidia_hackathon.git`** — I can stage
   commits locally and show you exactly what would be pushed, but the
   actual `git push` needs authenticated access to GitHub. I won't accept a
   personal access token or password from you to use on your behalf —
   entering credentials like that is something I avoid by design. Cleanest
   options:
   - You run the final `git push` yourself after I prepare the commit, or
   - If this environment has its own git credential setup you control
     (e.g. you're driving this from an authenticated terminal/Claude Code
     session rather than this chat), that's fine — just let me know so I
     don't ask twice.

6. **A decision on frontend auth** (Phase 5) — right now `ApprovalQueue.tsx`
   hardcodes `"demo-operator"` as the approver identity. If the hackathon
   demo doesn't need real auth, that's fine to leave as-is and just say so
   explicitly; if it does, I need to know what identity provider (if any)
   the team wants — this isn't a credential I need now, just a decision.

**Nothing else is needed from you to keep writing code.** Items 3–4 only
matter once someone is ready to actually run things on the cluster; items
1–2 only matter once Phase 1 starts.

---

## 6. Git / GitHub workflow

**Cadence:** commit at the end of each completed checklist item — small,
reviewable, revertable units, not one giant commit per phase.

**Process for every push:**
1. I show you the diff summary and proposed commit message in chat.
2. You confirm.
3. I run `git add`/`git commit`/`git push` only after that confirmation.
4. Repeats for every push — no batching approval across future commits.

**Branching:** trunk-based (`main` only) suggested given hackathon time
constraints — small frequent commits rather than long-lived feature
branches. Say the word if you'd rather use `feature/*` + PRs instead.

**What must never be committed:**
- `.env`, any real API keys/tokens
- `var/` (DB files, ATOF trajectory output)
- `node_modules/`, `__pycache__/`, any Apptainer `.sif` build artifacts

**Commit message format:**
```
<area>: <what changed>

<optional body — why, not what>
```
e.g. `backend/agents: implement real evidence_verifier scoring against persisted lineage`

---

## 7. Immediate next step

Confirm:
1. Monorepo layout (§0) — yes/no?
2. Trunk-based vs. feature-branch workflow (§6)?
3. Start with **Phase 1** (NVIDIA runtime, built real) — agree?

Once confirmed, and once you've set `NVIDIA_API_KEY` in your own environment
(item 1 above — I don't need to see it), I'll restructure the repo layout,
remove the Docker infra, add the Apptainer/Slurm infra, and start replacing
the gate/persistence stubs with real implementations — showing you the first
commit before anything gets pushed.
