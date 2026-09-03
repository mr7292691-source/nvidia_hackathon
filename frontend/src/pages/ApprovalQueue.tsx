import { useState } from "react";
import { approvalsApi } from "../api/approvals";
import { useApprovalQueue } from "../hooks/useApprovalQueue";
import { Card } from "../components/common/Card";

const CURRENT_APPROVER = "demo-operator"; // TODO: replace with real auth identity

export function ApprovalQueue() {
  const { pending, loading, refresh } = useApprovalQueue();
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});

  async function handleApprove(id: string) {
    await approvalsApi.approve(id, CURRENT_APPROVER);
    refresh();
  }

  async function handleReject(id: string) {
    await approvalsApi.reject(id, CURRENT_APPROVER, rejectReason[id] ?? "");
    refresh();
  }

  return (
    <div>
      <h1>Approval Queue</h1>
      <p style={{ color: "#666" }}>
        Nothing here becomes an action until a human explicitly approves it —
        this is the last of the deck's decision gates.
      </p>

      {loading && pending.length === 0 && <p>Loading...</p>}
      {!loading && pending.length === 0 && <p>No pending approvals.</p>}

      {pending.map((approval) => (
        <Card key={approval.approval_id} title={`Approval ${approval.approval_id}`}>
          <p style={{ fontSize: "0.85rem", color: "#666" }}>Event: {approval.event_id}</p>
          <pre style={{ fontSize: "0.8rem", background: "#f7f7f7", padding: "0.75rem" }}>
            {JSON.stringify(approval.proposed_action, null, 2)}
          </pre>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <button onClick={() => handleApprove(approval.approval_id)}>Approve</button>
            <input
              placeholder="Rejection reason"
              value={rejectReason[approval.approval_id] ?? ""}
              onChange={(e) =>
                setRejectReason((prev) => ({ ...prev, [approval.approval_id]: e.target.value }))
              }
            />
            <button onClick={() => handleReject(approval.approval_id)}>Reject</button>
          </div>
        </Card>
      ))}
    </div>
  );
}
