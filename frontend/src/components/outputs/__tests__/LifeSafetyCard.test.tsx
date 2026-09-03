import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LifeSafetyCard } from "../LifeSafetyCard";
import type { LifeSafetyGuidance } from "../../../types/decision";

describe("LifeSafetyCard", () => {
  it("shows a placeholder when no guidance exists yet", () => {
    render(<LifeSafetyCard guidance={null} />);
    expect(screen.getByText(/no guidance generated yet/i)).toBeInTheDocument();
  });

  it("renders the guidance text and evidence reference", () => {
    const guidance: LifeSafetyGuidance = {
      event_id: "evt_test",
      guidance_text: "Evacuate low-lying areas near Buffalo Bayou.",
      evidence_ref: "evt_test",
      approved: false,
    };
    render(<LifeSafetyCard guidance={guidance} />);
    expect(screen.getByText(/evacuate low-lying areas/i)).toBeInTheDocument();
    expect(screen.getByText(/evt_test/)).toBeInTheDocument();
  });

  it("shows the approve button only when not yet approved and a handler is given", () => {
    const guidance: LifeSafetyGuidance = {
      event_id: "evt_test",
      guidance_text: "Draft guidance.",
      evidence_ref: "evt_test",
      approved: false,
    };
    const onApprove = vi.fn();
    render(<LifeSafetyCard guidance={guidance} onApprove={onApprove} />);
    expect(screen.getByRole("button", { name: /send for human approval/i })).toBeInTheDocument();
  });

  it("hides the approve button once already approved", () => {
    const guidance: LifeSafetyGuidance = {
      event_id: "evt_test",
      guidance_text: "Approved guidance.",
      evidence_ref: "evt_test",
      approved: true,
    };
    render(<LifeSafetyCard guidance={guidance} onApprove={vi.fn()} />);
    expect(screen.queryByRole("button", { name: /send for human approval/i })).not.toBeInTheDocument();
    expect(screen.getByText(/^approved$/i)).toBeInTheDocument();
  });
});
