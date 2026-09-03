import type { ReplayResult } from "../types/replay";
import { apiClient } from "./client";

export const replayApi = {
  runHoustonEvent: () => apiClient.post<ReplayResult>("/replay/houston-event"),
};
