import { useActiveEventStore } from "../store/activeEventStore";
import { LineagePanel } from "../components/evidence/LineagePanel";
import { FieldImageUpload } from "../components/evidence/FieldImageUpload";
import { GatesPanel } from "../components/gates/GatesPanel";
import { EventMap } from "../components/map/EventMap";
import { LifeSafetyCard } from "../components/outputs/LifeSafetyCard";
import { InsurerExposureCard } from "../components/outputs/InsurerExposureCard";
import { Card } from "../components/common/Card";

export function EventDetail() {
  const { eventId, lineage, findings, lifesafetyGuidance, insurerExposure } = useActiveEventStore();

  if (!eventId) {
    return (
      <div>
        <h1>Event Detail</h1>
        <p>No active event. Run the replay demo from the Dashboard first.</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Event {eventId}</h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        <div>
          <LineagePanel lineage={lineage} />
          <EventMap />
          <FieldImageUpload eventId={eventId} />
          {findings?.evidence && (
            <Card title="Evidence Specialist Summary">
              <p>{findings.evidence.summary}</p>
            </Card>
          )}
          {findings?.vision && (
            <Card title="Vision Specialist">
              <p>{findings.vision.damage_assessment ?? findings.vision.note}</p>
            </Card>
          )}
        </div>
        <div>
          {/*
            TODO: the backend doesn't yet return structured per-gate results
            from /agents/run — GatesPanel renders defaults until
            app/nvidia_runtime/relay/guardrails.py's ToolExecutionInterceptOutcome
            reasons are surfaced through the API response.
          */}
          <GatesPanel />
          <LifeSafetyCard guidance={lifesafetyGuidance} />
          <InsurerExposureCard report={insurerExposure} />
        </div>
      </div>
    </div>
  );
}
