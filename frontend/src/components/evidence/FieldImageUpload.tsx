import { useState } from "react";
import { evidenceApi } from "../../api/evidence";
import { Card } from "../common/Card";

interface FieldImageUploadProps {
  eventId: string | null;
}

/**
 * Slide 5 step 2: "a field image is submitted." Lets a demo operator attach
 * an image to the active event so the vision specialist has something to
 * assess on the next /agents/run call.
 */
export function FieldImageUpload({ eventId }: FieldImageUploadProps) {
  const [status, setStatus] = useState<string | null>(null);

  async function handleFile(file: File | null) {
    if (!file || !eventId) return;
    setStatus("Uploading...");
    try {
      const result = await evidenceApi.uploadFieldImage(eventId, file);
      setStatus(`Uploaded ${result.bytes_received} bytes.`);
    } catch (err) {
      setStatus(`Upload failed: ${String(err)}`);
    }
  }

  return (
    <Card title="Submit Field Image">
      <input
        type="file"
        accept="image/*"
        disabled={!eventId}
        onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
      />
      {!eventId && <p style={{ color: "#999", fontSize: "0.85rem" }}>Start or select an event first.</p>}
      {status && <p style={{ fontSize: "0.85rem" }}>{status}</p>}
    </Card>
  );
}
