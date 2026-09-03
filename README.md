# LifeShield AI

**NVIDIA GSI Open Hackathon — Team Cognitive Core**

Multi-agent disaster response, accelerated by NVIDIA. A city-scale digital
twin that turns live hazard signals into coordinated, explainable action.

> ⚠️ **Work in progress.** This commit reflects an active mid-refactor state
> — see `docs/plan.md` for exactly what's real vs. still open, and the note
> at the bottom of this README for the current known-broken paths.

## Structure

```
nvidia_hackathon/
├── backend/     FastAPI + real NVIDIA stack (Switchyard, NeMo Relay,
│                DeepAgents, OpenShell) — see backend/README.md
├── frontend/    React + TypeScript UI — see frontend/README.md
└── docs/
    └── plan.md  Detailed remaining-work plan, phased, with an explicit
                 credentials/access section
```

## Architecture

Four layers, mapped to specific NVIDIA products (not generic placeholders):

| Layer | Real product |
|---|---|
| Evidence | NWS / USGS / HCFCD / TranStar / FEMA adapters, replay-mode fixtures today |
| NVIDIA Runtime | **build.nvidia.com** NIM (dev) / self-hosted NIM on Curiosity B300 (prod), fronted by **NVIDIA-NeMo/Switchyard** |
| Decision Gates | **NVIDIA/NeMo-Relay** (governance/guardrails) + **OpenShell** sandboxed **LangChain DeepAgents** specialists |
| Decision Outputs | Deterministic insurer exposure math + life-safety guidance, human-approval gated |

No Docker anywhere — Apptainer + Slurm on the cluster side, plain
processes for local dev (see `backend/infra/`).

## Current known state (be aware before running)

This snapshot was committed mid-refactor at the user's request, to get real
work into version control frequently rather than waiting for a fully clean
checkpoint. Specifically:

- ✅ Real, tested: Switchyard routing (YAML bundle format, verified against
  the installed `nemo-switchyard` package), NeMo Relay scope + ATOF export
  (verified real JSONL trajectory output), SQLite persistence, real gate
  logic (evidence verifier / confidence gate / policy verifier)
- ⚠️ **Not yet updated to match the above:** `backend/app/agents/supervisor.py`
  still sequences specialists manually instead of using
  `deepagents.create_deep_agent(...)`; `backend/app/agents/openshell_sandbox.py`
  still has the placeholder lifecycle methods instead of the real
  `openshell.SandboxClient`; `backend/app/main.py`'s startup does not yet
  call `init_db()`. **The backend will likely not boot cleanly from this
  commit** until those are finished — tracked in `docs/plan.md`.
- ❌ Not runnable end-to-end against real NVIDIA endpoints from any
  environment with build.nvidia.com network access blocked (this includes
  the sandbox this was authored in) — needs a real `NVIDIA_API_KEY` and,
  for OpenShell, a reachable OpenShell sandbox cluster.

See `docs/plan.md` for the full phase-by-phase breakdown, open risks, and
exactly what credentials/access are needed from the team to take this further.
