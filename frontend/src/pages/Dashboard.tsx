import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRunHoustonReplay } from "../hooks/useRunHoustonReplay";
import { useActiveEventStore } from "../store/activeEventStore";
import { Card } from "../components/common/Card";

export function Dashboard() {
  const { run } = useRunHoustonReplay();
  const { eventId, isRunning, error } = useActiveEventStore();
  const navigate = useNavigate();

  // Real state (not a ref) for anything that affects what's rendered --
  // ESLint's react-hooks rules correctly flagged an earlier draft that
  // read a ref's `.current` directly in JSX ("Cannot access ref value
  // during render": refs don't trigger re-renders, so the UI could go
  // stale). The ref below is only used inside the effect, never read
  // during render, which is the legitimate use case for it.
  const [justFinished, setJustFinished] = useState(false);
  const pendingNavigation = useRef(false);

  async function handleRun() {
    pendingNavigation.current = true;
    setJustFinished(false);
    await run();
  }

  useEffect(() => {
    if (pendingNavigation.current && eventId && !isRunning) {
      pendingNavigation.current = false;
      navigate("/event");
    }
  }, [eventId, isRunning, navigate]);

  useEffect(() => {
    if (eventId && !isRunning && !pendingNavigation.current) {
      setJustFinished(true);
    }
  }, [eventId, isRunning]);

  return (
    <div>
      <h1>LifeShield AI</h1>
      <p style={{ color: "#666", maxWidth: 640 }}>
        Multi-agent disaster response, accelerated by NVIDIA. Evidence in,
        governed reasoning, deterministic gates, two decision outputs.
      </p>

      <Card title="Today's Demo: One Replayed Houston Event">
        <p style={{ fontSize: "0.9rem", color: "#666" }}>
          Illustrative synthetic scenario — the values prove the flow, not a
          prediction about a real insurer or incident.
        </p>
        <button onClick={handleRun} disabled={isRunning}>
          {isRunning ? "Running..." : "Run Houston replay"}
        </button>
        {error && <p style={{ color: "#c5221f" }}>{error}</p>}
        {eventId && justFinished && (
          <p style={{ fontSize: "0.85rem", color: "#1e8e3e" }}>
            Last event: {eventId} — <a href="/event">view details</a>
          </p>
        )}
      </Card>
    </div>
  );
}
