import { useCallback, useEffect, useState } from "react";
import { approvalsApi } from "../api/approvals";
import type { ApprovalRecord } from "../types/approval";

export function useApprovalQueue(pollIntervalMs = 4000) {
  const [pending, setPending] = useState<ApprovalRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const records = await approvalsApi.listPending();
      setPending(records);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollIntervalMs);
    return () => clearInterval(id);
  }, [refresh, pollIntervalMs]);

  return { pending, loading, refresh };
}
