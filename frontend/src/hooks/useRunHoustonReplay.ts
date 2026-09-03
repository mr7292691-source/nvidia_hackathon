import { useCallback } from "react";
import { replayApi } from "../api/replay";
import { ApiError } from "../api/client";
import { useActiveEventStore } from "../store/activeEventStore";

/**
 * Drives the single-button demo flow (deck slide 5): calls
 * POST /replay/houston-event, which itself runs evidence bundling, the
 * OpenShell-sandboxed DeepAgents supervisor, and decision finalization
 * server-side, then stores the whole result for the UI to render.
 */
export function useRunHoustonReplay() {
  const { setEvent, setFindings, setDecisions, setRunning, setError, reset } =
    useActiveEventStore();

  const run = useCallback(async () => {
    reset();
    setRunning(true);
    try {
      const result = await replayApi.runHoustonEvent();
      setEvent(result.event_id, result.lineage);
      setFindings(result.findings);
      setDecisions(result.lifesafety_guidance, result.insurer_exposure);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : String(err);
      setError(message);
    } finally {
      setRunning(false);
    }
  }, [reset, setEvent, setFindings, setDecisions, setRunning, setError]);

  return { run };
}
