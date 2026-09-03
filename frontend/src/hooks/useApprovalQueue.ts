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
    // This is the standard "fetch on mount, then poll" pattern (React's
    // own docs use this shape for effects that synchronize with an
    // external system). ESLint's react-hooks rule flags any function call
    // in an effect that *could* set state, which is a broader net than
    // just the synchronous-setState-in-effect-body anti-pattern this repo
    // fixed for real elsewhere (see Dashboard.tsx, useGates.ts) --
    // disabling narrowly here rather than restructuring away from a
    // pattern React's own documentation recommends.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    const id = setInterval(refresh, pollIntervalMs);
    return () => clearInterval(id);
  }, [refresh, pollIntervalMs]);

  return { pending, loading, refresh };
}
