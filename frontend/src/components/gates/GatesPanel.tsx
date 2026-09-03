import { StatusBadge } from "../common/StatusBadge";
import { Card } from "../common/Card";

interface GateStatus {
  name: string;
  description: string;
  status: "pass" | "fail" | "pending" | "unknown";
  reason?: string;
}

interface GatesPanelProps {
  /**
   * The backend doesn't yet expose a dedicated gate-status endpoint — gate
   * pass/fail currently only surfaces implicitly (a blocked NeMo Relay
   * guardrail short-circuits /agents/run). Until app/nvidia_runtime/relay/
   * guardrails.py returns structured results back through the API, this
   * component accepts them as a prop so it can be wired in incrementally;
   * see TODO in EventDetail.tsx.
   */
  gates?: GateStatus[];
}

const DEFAULT_GATES: GateStatus[] = [
  {
    name: "Evidence Verifier",
    description: "Scores freshness, location, and source agreement.",
    status: "unknown",
  },
  {
    name: "Confidence Gate",
    description: "Blocks weak evidence before it reaches the specialists.",
    status: "unknown",
  },
  {
    name: "Policy Verifier",
    description: "Checks proposed actions against deterministic policy bounds.",
    status: "unknown",
  },
  {
    name: "Human Approval",
    description: "Final sign-off — no action leaves the system without it.",
    status: "pending",
  },
];

export function GatesPanel({ gates = DEFAULT_GATES }: GatesPanelProps) {
  return (
    <Card title="Decision Gates">
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {gates.map((gate) => (
          <div key={gate.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 600 }}>{gate.name}</div>
              <div style={{ fontSize: "0.85rem", color: "#666" }}>{gate.description}</div>
              {gate.reason && (
                <div style={{ fontSize: "0.8rem", color: "#c5221f", marginTop: "0.25rem" }}>{gate.reason}</div>
              )}
            </div>
            <StatusBadge status={gate.status} label={gate.status} />
          </div>
        ))}
      </div>
    </Card>
  );
}
