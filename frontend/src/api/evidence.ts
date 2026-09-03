import type { EvidenceRecord } from "../types/evidence";
import { apiClient } from "./client";

export const evidenceApi = {
  get: (eventId: string) => apiClient.get<EvidenceRecord>(`/evidence/${eventId}`),
  uploadFieldImage: (eventId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.postForm<{ event_id: string; bytes_received: number }>(
      `/evidence/${eventId}/field-image`,
      form
    );
  },
};
