import { Card } from "../common/Card";
import type { GeoJSONGeometry } from "../../types/evidence";

interface EventMapProps {
  bbox?: GeoJSONGeometry;
}

/**
 * Placeholder for the event-polygon / gauge / roadway overlay map referenced
 * throughout the deck. Deliberately not wired to a mapping library yet —
 * pick one (MapLibre GL + an open basemap is the natural fit given no
 * Google Maps dependency is implied anywhere in the deck) once the team
 * settles on how much of the geospatial layer is in scope for the demo.
 * Renders the bbox coordinates as text in the meantime so the rest of the
 * UI isn't blocked on this decision.
 */
export function EventMap({ bbox }: EventMapProps) {
  return (
    <Card title="Event Footprint">
      {bbox ? (
        <pre style={{ fontSize: "0.8rem", background: "#f7f7f7", padding: "0.75rem", overflowX: "auto" }}>
          {JSON.stringify(bbox, null, 2)}
        </pre>
      ) : (
        <p style={{ color: "#666" }}>No event loaded.</p>
      )}
      <p style={{ fontSize: "0.8rem", color: "#999", marginBottom: 0 }}>
        TODO: render this polygon plus gauge/roadway markers on a real map
        (MapLibre GL suggested) once the team scopes the geospatial layer.
      </p>
    </Card>
  );
}
