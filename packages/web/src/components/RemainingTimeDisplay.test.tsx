import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";
import { TooltipProvider } from "./ui/tooltip";

const renderWithTooltip = (ui: React.ReactElement) =>
  render(<TooltipProvider>{ui}</TooltipProvider>);

describe("RemainingTimeDisplay", () => {
  describe("Formatted remaining time", () => {
    it("renders minutes remaining for short durations", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={1800}
          scheduledResolution="2026-02-07T21:00:00Z"
        />
      );
      expect(screen.getByText("30m remaining")).toBeInTheDocument();
    });

    it("renders hours and minutes for medium durations", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={19800}
          scheduledResolution="2026-02-07T21:00:00Z"
        />
      );
      expect(screen.getByText("5h 30m remaining")).toBeInTheDocument();
    });

    it("renders days and hours for long durations", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={180000}
          scheduledResolution="2026-02-07T21:00:00Z"
        />
      );
      expect(screen.getByText("2d 2h remaining")).toBeInTheDocument();
    });

    it("renders less than 1 minute for very short durations", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={30}
          scheduledResolution="2026-02-07T21:00:00Z"
        />
      );
      expect(screen.getByText("< 1m remaining")).toBeInTheDocument();
    });

    it("renders 'Deadline passed' when remaining time is 0", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={0}
          scheduledResolution="2026-02-07T21:00:00Z"
        />
      );
      expect(screen.getByText("Deadline passed")).toBeInTheDocument();
    });
  });

  describe("Paused state", () => {
    it("renders 'Paused' with pause styling when isPaused is true", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={3600}
          scheduledResolution="2026-02-07T21:00:00Z"
          isPaused={true}
        />
      );
      expect(screen.getByText("Paused")).toBeInTheDocument();
    });

    it("does not render remaining time when paused", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={3600}
          scheduledResolution="2026-02-07T21:00:00Z"
          isPaused={true}
        />
      );
      expect(screen.queryByText(/remaining/)).not.toBeInTheDocument();
    });

    it("renders remaining time when not paused", () => {
      renderWithTooltip(
        <RemainingTimeDisplay
          remainingTime={3600}
          scheduledResolution="2026-02-07T21:00:00Z"
          isPaused={false}
        />
      );
      expect(screen.getByText("1h 0m remaining")).toBeInTheDocument();
      expect(screen.queryByText("Paused")).not.toBeInTheDocument();
    });
  });
});
