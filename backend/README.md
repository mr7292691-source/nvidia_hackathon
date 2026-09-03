# LifeShield AI — Backend

Multi-agent disaster response backend for the NVIDIA GSI Open Hackathon.
Evidence in → governed reasoning → deterministic gates → two decision outputs.

## Architecture (maps 1:1 to the deck's 4-layer diagram)

```
app/
├── evidence/          # LAYER 1 — Evidence Layer
│   └── adapters/      #   NWS, USGS, HCFCD, TranStar, FEMA source adapters.
│       └── replay/    #   Replayable JSON fixtures for the Houston demo event
│                       #   (today's build stays replay-first per the deck;
│                       #    adapters are written so a live feed is a config
│                       #    swap, not a rewrite).
│
├── nvidia_runtime/    # LAYER 2 — NVIDIA Runtime
│   ├── switchyard_client.py   # Talks OpenAI-compatible API to whatever
│   │                           # NeMo Switchyard route is active:
│   │                           #   dev  -> build.nvidia.com NIM endpoints
│   │                           #   prod -> self-hosted NIM on Curiosity B300
│   ├── nim_vision.py           # Vision NIM call (flood imagery -> damage evidence)
│   ├── nim_reasoning.py        # Reasoning NIM call (Nemotron, via Switchyard)
│   └── relay/                  # NeMo Relay integration: every LLM + tool call
│       ├── relay_runtime.py    # is wrapped in a Relay scope; ATOF trajectory
│       └── guardrails.py       # export IS the auditable evidence/lineage record.
│
├── agents/            # LAYER 3 — Decision Gates
│   ├── openshell_sandbox.py    # OpenShell sandbox session: agents get network-
│   │                           # locked, policy-governed exec envs. No agent
│   │                           # ever gets raw internet or DB access here.
│   ├── supervisor.py           # DeepAgents supervisor ("OpenShell supervisor")
│   ├── specialists/             # DeepAgents sub-agents, each scoped to one job
│   ├── tools/                   # The ONLY things specialists can call — thin,
│   │                           # validated wrappers over evidence/portfolio data.
│   │                           # This is the guardrail: no raw web/db tools exist.
│   └── gates/                   # evidence_verifier / confidence_gate /
│                                 # policy_verifier — implemented as NeMo Relay
│                                 # conditional-execution guardrails, not prompts.
│
├── decisions/         # LAYER 4 — Decision Outputs
│   ├── lifesafety_guidance.py  # Life-safety response guidance
│   └── insurer_exposure.py     # Deterministic TIV / limit / deductible math.
│                                 # Intentionally NOT LLM-generated — it's plain
│                                 # arithmetic over the evidence + policy overlay.
│
└── approvals/          # Human approval gate — nothing in decisions/ is allowed
                         # to leave the system as an "action" without a passed
                         # approvals/human_approval.py check.
```

## NVIDIA / LangChain stack (all required, non-negotiable per project brief)

| Component | Used for |
|---|---|
| [build.nvidia.com](https://build.nvidia.com/) | Hosted NIM endpoints for dev (vision + reasoning models) |
| [NVIDIA-NeMo/Switchyard](https://github.com/NVIDIA-NeMo/Switchyard) | OpenAI-compatible routing proxy between dev (build.nvidia.com) and prod (self-hosted NIM on Curiosity B300) |
| [NVIDIA/NeMo-Relay](https://github.com/NVIDIA/NeMo-Relay) | Governance/observability runtime — guardrail middleware + ATOF trajectory export for every LLM/tool call |
| [langchain-ai/openshell-deepagent](https://github.com/langchain-ai/openshell-deepagent) | Reference pattern for running DeepAgents specialists inside an OpenShell sandbox |
| LangChain DeepAgents | Supervisor + specialist multi-agent harness (LangGraph runtime underneath) |

## Environments

Two deploy targets, selected by `LIFESHIELD_ENV`:

- `dev` — Switchyard routes to `https://integrate.api.nvidia.com/v1` using `NVIDIA_API_KEY` (an `nvapi-...` key from build.nvidia.com).
- `prod` — Switchyard routes to the self-hosted NIM containers running as Slurm/Kubernetes workloads on the Curiosity v2 (B300) cluster. No code change — only `infra/switchyard/routes.<env>.toml` differs.

See `.env.example` and `infra/switchyard/`.

## Status

This is a scaffold: folder structure, interfaces, and stubs wired end-to-end so
the team can fill in each box in parallel. Nothing here has been pushed to
GitHub — that happens only with explicit sign-off.
