import { create } from "zustand";
import type { InsurerExposureReport, LifeSafetyGuidance } from "../types/decision";
import type { LineageEntry } from "../types/evidence";
import type { SpecialistFindings } from "../types/replay";

interface ActiveEventState {
  eventId: string | null;
  lineage: LineageEntry[];
  findings: SpecialistFindings | null;
  lifesafetyGuidance: LifeSafetyGuidance | null;
  insurerExposure: InsurerExposureReport | null;
  isRunning: boolean;
  error: string | null;

  setEvent: (eventId: string, lineage: LineageEntry[]) => void;
  setFindings: (findings: SpecialistFindings) => void;
  setDecisions: (guidance: LifeSafetyGuidance, exposure: InsurerExposureReport) => void;
  setRunning: (running: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useActiveEventStore = create<ActiveEventState>((set) => ({
  eventId: null,
  lineage: [],
  findings: null,
  lifesafetyGuidance: null,
  insurerExposure: null,
  isRunning: false,
  error: null,

  setEvent: (eventId, lineage) => set({ eventId, lineage }),
  setFindings: (findings) => set({ findings }),
  setDecisions: (lifesafetyGuidance, insurerExposure) =>
    set({ lifesafetyGuidance, insurerExposure }),
  setRunning: (isRunning) => set({ isRunning }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      eventId: null,
      lineage: [],
      findings: null,
      lifesafetyGuidance: null,
      insurerExposure: null,
      isRunning: false,
      error: null,
    }),
}));
