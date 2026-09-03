// Mirrors backend/app/evidence/lineage.py:LineageEntry and
// backend/app/evidence/evidence_record.py:EvidenceRecord

export interface LineageEntry {
  source: string;
  record_count: number;
  earliest_observed_at: string | null;
  latest_observed_at: string | null;
  mode: "replay" | "live";
}

export interface GeoJSONGeometry {
  type: string;
  coordinates: unknown;
}

export interface EvidenceRecord {
  event_id: string;
  created_at: string;
  event_window: [string, string];
  bbox: GeoJSONGeometry;
  sources: Record<string, unknown[]>;
  lineage: LineageEntry[];
  vision_confidence: number | null;
  vision_lineage_ref: string | null;
}
