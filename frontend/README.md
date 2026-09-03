# LifeShield AI — Frontend

React + TypeScript UI for the disaster-response demo. Talks only to the
`lifeshield-backend` FastAPI service — never directly to any NVIDIA service,
evidence source, or agent. All governance (NeMo Relay), routing (Switchyard),
and agent orchestration (OpenShell/DeepAgents) live server-side; this app is
a thin client over `/events`, `/evidence`, `/agents`, `/decisions`,
`/approvals`, `/replay`.

## Pages (mirrors the deck's demo flow, slide 5)

- **Dashboard** — event list + "Run Houston replay" one-click demo trigger
- **EventDetail** — evidence record, source lineage, gate status, both decision outputs
- **ApprovalQueue** — human-in-the-loop approve/reject for pending actions
- **ReplayConsole** — raw view into the replay fixtures for debugging the demo

## Structure

```
src/
├── api/            # fetch wrappers, one file per backend route group
├── components/
│   ├── evidence/    # evidence record viewer, source lineage panel
│   ├── gates/       # evidence_verifier / confidence_gate / policy_verifier status
│   ├── map/         # event polygon + gauge/roadway overlay
│   ├── outputs/     # life-safety guidance card, insurer exposure card
│   └── common/
├── pages/
├── hooks/
├── store/           # lightweight zustand store for the active event
└── types/           # TS types mirroring backend/app/models/*.py — keep in sync
```

## Running

```bash
npm install
cp .env.example .env   # set VITE_API_BASE_URL to the backend's URL
npm run dev
```

## Status

Scaffold + working demo flow (trigger replay → poll event → show gates,
outputs, approval queue) wired against the backend's stub endpoints. Visual
design, map integration, and auth are still open. Nothing here has been
pushed to GitHub.
