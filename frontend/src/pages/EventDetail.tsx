import { useActiveEventStore } from "../store/activeEventStore";
import { useGates } from "../hooks/useGates";
import { LineagePanel } from "../components/evidence/LineagePanel";
import { FieldImageUpload } from "../components/evidence/FieldImageUpload";
import { GatesPanel } from "../components/gates/GatesPanel";
import { EventMap } from "../components/map/EventMap";
import { LifeSafetyCard } from "../components/outputs/LifeSafetyCard";
import { InsurerExposureCard } from "../components/outputs/InsurerExposureCard";
import { Card } from "../components/common/Card";

export function EventDetail() {
  const { eventId, lineage, findings, lifesafetyGuidance, insurerExposure } = useActiveEventStore();
  const { gates, loading: gatesLoading } = useGates(eventId);

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
          <GatesPanel gates={gates} loading={gatesLoading} />
          <LifeSafetyCard guidance={lifesafetyGuidance} />
          <InsurerExposureCard report={insurerExposure} />
        </div>
      </div>
    </div>
  );
}
