import type { InsurerExposureReport, LifeSafetyGuidance } from "../types/decision";
import type { SpecialistFindings } from "../types/replay";
import { apiClient } from "./client";

export const agentsApi = {
  run: (eventId: string) => apiClient.post<SpecialistFindings>(`/agents/run/${eventId}`),
};

export interface FinalizeDecisionsResponse {
  lifesafety_guidance: LifeSafetyGuidance;
  insurer_exposure: InsurerExposureReport;
}

export const decisionsApi = {
  finalize: (eventId: string, findings: SpecialistFindings) =>
    apiClient.post<FinalizeDecisionsResponse>(`/decisions/${eventId}/finalize`, findings),
};
