import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useRunHoustonReplay } from "../hooks/useRunHoustonReplay";
import { useActiveEventStore } from "../store/activeEventStore";
import { Card } from "../components/common/Card";

export function Dashboard() {
  const { run } = useRunHoustonReplay();
  const { eventId, isRunning, error } = useActiveEventStore();
  const navigate = useNavigate();
  // Tracks whether the user just triggered a run in THIS page visit, so we
  // only auto-navigate once, right after a fresh run finishes -- not on
  // every render where eventId happens to already be set (e.g. coming back
  // to the Dashboard from EventDetail shouldn't bounce you right back).
  const justTriggered = useRef(false);

  async function handleRun() {
    justTriggered.current = true;
    await run();
  }

  useEffect(() => {
    if (justTriggered.current && eventId && !isRunning) {
      justTriggered.current = false;
      navigate("/event");
    }
  }, [eventId, isRunning, navigate]);

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
        {eventId && !isRunning && !justTriggered.current && (
          <p style={{ fontSize: "0.85rem", color: "#1e8e3e" }}>
            Last event: {eventId} — <a href="/event">view details</a>
          </p>
        )}
      </Card>
    </div>
  );
}
