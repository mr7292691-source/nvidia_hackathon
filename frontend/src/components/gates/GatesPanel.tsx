import type { GateStatus as ApiGateStatus } from "../../api/decisions";
import { StatusBadge } from "../common/StatusBadge";
import { Card } from "../common/Card";

interface GatesPanelProps {
  /** Real per-gate results from GET /agents/gates/{eventId}, or null while
   * loading / before an event exists. Human approval isn't included in
   * that endpoint (it's not a NeMo Relay guardrail, it's the separate
   * /approvals flow) so it's always shown as a static "pending" row here. */
  gates: ApiGateStatus[] | null;
  loading?: boolean;
}

export function GatesPanel({ gates, loading }: GatesPanelProps) {
  return (
    <Card title="Decision Gates">
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {loading && <p style={{ color: "#666", fontSize: "0.85rem" }}>Checking gates...</p>}
        {!loading && !gates && <p style={{ color: "#666", fontSize: "0.85rem" }}>No event loaded.</p>}
        {gates?.map((gate) => (
          <div key={gate.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 600 }}>{gate.name}</div>
              {gate.reason && (
                <div style={{ fontSize: "0.8rem", color: gate.passed ? "#666" : "#c5221f", marginTop: "0.25rem" }}>
                  {gate.reason}
                </div>
              )}
            </div>
            <StatusBadge status={gate.passed ? "pass" : "fail"} label={gate.passed ? "pass" : "fail"} />
          </div>
        ))}
        {gates && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 600 }}>Human Approval</div>
              <div style={{ fontSize: "0.8rem", color: "#666" }}>
                Final sign-off -- no action leaves the system without it.
              </div>
            </div>
            <StatusBadge status="pending" label="pending" />
          </div>
        )}
      </div>
    </Card>
  );
}
