import type { InsurerExposureReport, LifeSafetyGuidance } from "./decision";
import type { LineageEntry } from "./evidence";

// Mirrors backend/app/api/routes/replay.py:replay_houston_event response

export interface SpecialistFindings {
  evidence?: { summary: string };
  vision?: { damage_assessment: string | null; confidence: number | null; note?: string };
  policy?: { policies_in_footprint: unknown[] };
  lifesafety?: { draft_guidance: string };
}

export interface ReplayResult {
  event_id: string;
  lineage: LineageEntry[];
  findings: SpecialistFindings;
  lifesafety_guidance: LifeSafetyGuidance;
  insurer_exposure: InsurerExposureReport;
  note: string;
}
