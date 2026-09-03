import { apiClient } from "./client";

export interface CreateEventRequest {
  window_start: string;
  window_end: string;
  bbox: Record<string, unknown>;
}

export interface CreateEventResponse {
  event_id: string;
  lineage: unknown[];
}

export const eventsApi = {
  create: (body: CreateEventRequest) =>
    apiClient.post<CreateEventResponse>("/events", body),
  replayHoustonDemo: () =>
    apiClient.post<CreateEventResponse>("/events/replay/houston-demo"),
};
