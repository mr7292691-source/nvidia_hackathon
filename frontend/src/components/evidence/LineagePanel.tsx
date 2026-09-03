import type { LineageEntry } from "../../types/evidence";
import { Card } from "../common/Card";

interface LineagePanelProps {
  lineage: LineageEntry[];
}

/**
 * Renders the source lineage the deck calls out explicitly: "one auditable
 * evidence record with source lineage." Each row is one source adapter
 * (NWS/USGS/HCFCD/TranStar/FEMA) with its freshness window and record count.
 */
export function LineagePanel({ lineage }: LineagePanelProps) {
  if (lineage.length === 0) {
    return <Card title="Source Lineage">No evidence bundled yet.</Card>;
  }

  return (
    <Card title="Source Lineage">
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #eee" }}>
            <th>Source</th>
            <th>Records</th>
            <th>Earliest</th>
            <th>Latest</th>
            <th>Mode</th>
          </tr>
        </thead>
        <tbody>
          {lineage.map((entry) => (
            <tr key={entry.source} style={{ borderBottom: "1px solid #f2f2f2" }}>
              <td>{entry.source}</td>
              <td>{entry.record_count}</td>
              <td>{entry.earliest_observed_at ?? "—"}</td>
              <td>{entry.latest_observed_at ?? "—"}</td>
              <td>{entry.mode}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
