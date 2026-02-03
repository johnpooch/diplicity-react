import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DeadlineSummary } from "./DeadlineSummary";

describe("DeadlineSummary", () => {
  it("renders sandbox message when movementPhaseDuration is null", () => {
    render(<DeadlineSummary movementPhaseDuration={null} />);
    expect(
      screen.getByText("No automatic deadlines (sandbox)")
    ).toBeInTheDocument();
  });

  it("renders simple message when only movementPhaseDuration is set", () => {
    render(<DeadlineSummary movementPhaseDuration="24 hours" />);
    expect(
      screen.getByText("Phases resolve every 24 hours")
    ).toBeInTheDocument();
  });

  it("renders simple message when retreatPhaseDuration equals movementPhaseDuration", () => {
    render(
      <DeadlineSummary
        movementPhaseDuration="48 hours"
        retreatPhaseDuration="48 hours"
      />
    );
    expect(
      screen.getByText("Phases resolve every 48 hours")
    ).toBeInTheDocument();
  });

  it("renders both durations when they differ", () => {
    render(
      <DeadlineSummary
        movementPhaseDuration="48 hours"
        retreatPhaseDuration="12 hours"
      />
    );
    expect(
      screen.getByText(/Movement: 48 hours, Retreat\/Adjustment: 12 hours/)
    ).toBeInTheDocument();
  });

  it.each([
    "1 hour",
    "12 hours",
    "24 hours",
    "48 hours",
    "3 days",
    "4 days",
    "1 week",
    "2 weeks",
  ])("renders correctly for %s duration", duration => {
    render(<DeadlineSummary movementPhaseDuration={duration} />);
    expect(
      screen.getByText(`Phases resolve every ${duration}`)
    ).toBeInTheDocument();
  });
});
