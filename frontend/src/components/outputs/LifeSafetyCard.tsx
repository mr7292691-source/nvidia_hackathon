import type { LifeSafetyGuidance } from "../../types/decision";
import { Card } from "../common/Card";
import { StatusBadge } from "../common/StatusBadge";

interface LifeSafetyCardProps {
  guidance: LifeSafetyGuidance | null;
  onApprove?: () => void;
}

export function LifeSafetyCard({ guidance, onApprove }: LifeSafetyCardProps) {
  if (!guidance) {
    return <Card title="Life-Safety Guidance">No guidance generated yet.</Card>;
  }

  return (
    <Card title="Life-Safety Guidance">
      <div style={{ marginBottom: "0.75rem" }}>
        <StatusBadge status={guidance.approved ? "pass" : "pending"} label={guidance.approved ? "Approved" : "Awaiting approval"} />
      </div>
      <p style={{ whiteSpace: "pre-wrap" }}>{guidance.guidance_text || "(empty draft)"}</p>
      <p style={{ fontSize: "0.8rem", color: "#999" }}>Evidence ref: {guidance.evidence_ref}</p>
      {!guidance.approved && onApprove && (
        <button onClick={onApprove} style={{ marginTop: "0.5rem" }}>
          Send for human approval
        </button>
      )}
    </Card>
  );
}
