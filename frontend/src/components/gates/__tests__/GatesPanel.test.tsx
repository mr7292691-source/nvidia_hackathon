import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GatesPanel } from "../GatesPanel";
import type { GateStatus } from "../../../api/decisions";

describe("GatesPanel", () => {
  it("shows a loading state when loading and no gates yet", () => {
    render(<GatesPanel gates={null} loading />);
    expect(screen.getByText(/checking gates/i)).toBeInTheDocument();
  });

  it("shows 'no event loaded' when not loading and no gates", () => {
    render(<GatesPanel gates={null} loading={false} />);
    expect(screen.getByText(/no event loaded/i)).toBeInTheDocument();
  });

  it("renders each real gate result with correct pass/fail state", () => {
    const gates: GateStatus[] = [
      { name: "Evidence Verifier", passed: true, reason: "" },
      {
        name: "Confidence Gate",
        passed: false,
        reason: "No vision confidence recorded yet -- evidence gap.",
      },
    ];
    render(<GatesPanel gates={gates} />);

    expect(screen.getByText("Evidence Verifier")).toBeInTheDocument();
    expect(screen.getByText("Confidence Gate")).toBeInTheDocument();
    expect(screen.getByText(/evidence gap/i)).toBeInTheDocument();

    // One badge per real gate (pass/fail), rendered as lowercase status text
    expect(screen.getByText("pass")).toBeInTheDocument();
    expect(screen.getByText("fail")).toBeInTheDocument();
  });

  it("always shows the static Human Approval row once gates have loaded", () => {
    render(<GatesPanel gates={[{ name: "Evidence Verifier", passed: true, reason: "" }]} />);
    expect(screen.getByText("Human Approval")).toBeInTheDocument();
    expect(screen.getByText("pending")).toBeInTheDocument();
  });

  it("does not show Human Approval before any event/gates exist", () => {
    render(<GatesPanel gates={null} />);
    expect(screen.queryByText("Human Approval")).not.toBeInTheDocument();
  });
});
