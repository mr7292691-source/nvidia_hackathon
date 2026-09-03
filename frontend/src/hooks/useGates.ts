import { useEffect, useState } from "react";
import { agentsApi, type GateStatus } from "../api/decisions";

/**
 * Fetches real per-gate results from GET /agents/gates/{eventId} -- these
 * run the actual evidence_verifier / confidence_gate / policy_verifier
 * logic against persisted data, no live NIM call needed, so this loads
 * fast and works even before the DeepAgents graph has been invoked.
 */
export function useGates(eventId: string | null) {
  const [gates, setGates] = useState<GateStatus[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!eventId) {
      setGates(null);
      return;
    }
    setLoading(true);
    agentsApi
      .getGates(eventId)
      .then((res) => setGates(res.gates))
      .finally(() => setLoading(false));
  }, [eventId]);

  return { gates, loading };
}
