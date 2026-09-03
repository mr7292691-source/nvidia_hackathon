import { useActiveEventStore } from "../store/activeEventStore";
import { Card } from "../components/common/Card";

/**
 * Raw debug view of whatever the last replay run produced — useful when
 * iterating on the backend's fixtures/specialists without redesigning the
 * polished EventDetail view each time the response shape changes.
 */
export function ReplayConsole() {
  const state = useActiveEventStore();

  return (
    <div>
      <h1>Replay Console</h1>
      <Card title="Raw Active Event State">
        <pre style={{ fontSize: "0.8rem", background: "#f7f7f7", padding: "0.75rem", overflowX: "auto" }}>
          {JSON.stringify(state, null, 2)}
        </pre>
      </Card>
    </div>
  );
}
