import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InsurerExposureCard } from "../InsurerExposureCard";
import type { InsurerExposureReport } from "../../../types/decision";

describe("InsurerExposureCard", () => {
  it("shows a placeholder when no report exists yet", () => {
    render(<InsurerExposureCard report={null} />);
    expect(screen.getByText(/no exposure computed yet/i)).toBeInTheDocument();
  });

  it("renders real policy rows and the correct formatted total", () => {
    const report: InsurerExposureReport = {
      event_id: "evt_test",
      policies: [
        {
          policy_id: "SYN-POL-10001",
          tiv_usd: 450000,
          limit_usd: 400000,
          deductible_usd: 5000,
          estimated_exposure_usd: 195000,
        },
      ],
      total_estimated_exposure_usd: 195000,
      evidence_ref: "evt_test",
      approved: false,
    };
    render(<InsurerExposureCard report={report} />);

    expect(screen.getByText("SYN-POL-10001")).toBeInTheDocument();
    // currency formatting via Intl.NumberFormat -- assert the real formatted value appears
    expect(screen.getByText("$195,000.00")).toBeInTheDocument();
    expect(screen.getByText(/awaiting approval/i)).toBeInTheDocument();
  });

  it("shows an approved badge when the report is approved", () => {
    const report: InsurerExposureReport = {
      event_id: "evt_test",
      policies: [],
      total_estimated_exposure_usd: 0,
      evidence_ref: "evt_test",
      approved: true,
    };
    render(<InsurerExposureCard report={report} />);
    expect(screen.getByText(/^approved$/i)).toBeInTheDocument();
  });
});
