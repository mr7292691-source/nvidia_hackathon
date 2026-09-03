import type { InsurerExposureReport, LifeSafetyGuidance } from "../types/decision";
import type { SpecialistFindings } from "../types/replay";
import { apiClient } from "./client";

export const agentsApi = {
  run: (eventId: string) => apiClient.post<SpecialistFindings>(`/agents/run/${eventId}`),
  getGates: (eventId: string) => apiClient.get<GatesResponse>(`/agents/gates/${eventId}`),
};

export interface GateStatus {
  name: string;
  passed: boolean;
  reason: string;
}

export interface GatesResponse {
  event_id: string;
  gates: GateStatus[];
}

export interface FinalizeDecisionsResponse {
  lifesafety_guidance: LifeSafetyGuidance;
  insurer_exposure: InsurerExposureReport;
}

export const decisionsApi = {
  finalize: (eventId: string, findings: SpecialistFindings) =>
    apiClient.post<FinalizeDecisionsResponse>(`/decisions/${eventId}/finalize`, findings),
};
