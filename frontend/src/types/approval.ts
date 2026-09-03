// Mirrors backend/app/models/approval.py

export type ApprovalStatus = "pending" | "approved" | "rejected";

export interface ApprovalRecord {
  approval_id: string;
  event_id: string;
  proposed_action: Record<string, unknown>;
  status: ApprovalStatus;
  approver?: string | null;
  reason?: string | null;
}
