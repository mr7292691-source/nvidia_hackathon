import type { ApprovalRecord } from "../types/approval";
import { apiClient } from "./client";

export const approvalsApi = {
  listPending: () => apiClient.get<ApprovalRecord[]>("/approvals"),
  approve: (approvalId: string, approver: string) =>
    apiClient.post<ApprovalRecord>(`/approvals/${approvalId}/approve`, { approver }),
  reject: (approvalId: string, approver: string, reason: string) =>
    apiClient.post<ApprovalRecord>(`/approvals/${approvalId}/reject`, { approver, reason }),
};
