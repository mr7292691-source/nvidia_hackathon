import { useEffect, useState } from "react";
import { agentsApi, type GateStatus } from "../api/decisions";

/**
 * Fetches real per-gate results from GET /agents/gates/{eventId} -- these
 * run the actual evidence_verifier / confidence_gate / policy_verifier
 * logic against persisted data, no live NIM call needed, so this loads
 * fast and works even before the DeepAgents graph has been invoked.
 *
 * Restructured after ESLint's react-hooks rules flagged an earlier draft
 * that called setGates(null) synchronously inside the effect as a
 * "no event yet" reset -- the null case is now derived directly at the
 * return site instead, so the effect only ever sets state for the case it
 * actually owns (a real fetch in flight).
 */
export function useGates(eventId: string | null) {
  const [gates, setGates] = useState<GateStatus[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadedForEventId, setLoadedForEventId] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) {
      return;
    }
    // Standard fetch-on-dependency-change pattern -- see the identical,
    // more detailed justification in useApprovalQueue.ts.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    agentsApi
      .getGates(eventId)
      .then((res) => {
        setGates(res.gates);
        setLoadedForEventId(eventId);
      })
      .finally(() => setLoading(false));
  }, [eventId]);

  const isCurrent = eventId !== null && loadedForEventId === eventId;
  return { gates: isCurrent ? gates : null, loading };
}
