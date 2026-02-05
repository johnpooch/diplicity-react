import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DeadlineSummary } from "./DeadlineSummary";

describe("DeadlineSummary", () => {
  describe("Duration Mode", () => {
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

    it("renders simple message when retreatPhaseDuration is null", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration="24 hours"
          retreatPhaseDuration={null}
        />
      );
      expect(
        screen.getByText("Phases resolve every 24 hours")
      ).toBeInTheDocument();
    });

    it("renders simple message when retreatPhaseDuration is undefined", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration="24 hours"
          retreatPhaseDuration={undefined}
        />
      );
      expect(
        screen.getByText("Phases resolve every 24 hours")
      ).toBeInTheDocument();
    });
  });

  describe("Fixed-Time Mode", () => {
    it("renders fixed-time summary with daily frequency", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="21:00"
          fixedDeadlineTimezone="America/New_York"
          movementFrequency="daily"
        />
      );
      expect(screen.getByText(/daily at 9:00 PM ET/i)).toBeInTheDocument();
    });

    it("renders fixed-time summary with hourly frequency", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="14:30"
          fixedDeadlineTimezone="America/Chicago"
          movementFrequency="hourly"
        />
      );
      expect(screen.getByText(/hourly at 2:30 PM CT/i)).toBeInTheDocument();
    });

    it("renders fixed-time summary with weekly frequency", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="15:00"
          fixedDeadlineTimezone="America/Los_Angeles"
          movementFrequency="weekly"
        />
      );
      expect(screen.getByText(/weekly at 3:00 PM PT/i)).toBeInTheDocument();
    });

    it("renders fixed-time summary with every_2_days frequency", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="09:00"
          fixedDeadlineTimezone="Europe/London"
          movementFrequency="every_2_days"
        />
      );
      expect(screen.getByText(/every 2 days at 9:00 AM GMT/i)).toBeInTheDocument();
    });

    it("shows prompt when fixed-time fields are incomplete (missing time)", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime={null}
          fixedDeadlineTimezone="America/New_York"
          movementFrequency="daily"
        />
      );
      expect(
        screen.getByText("Select time, timezone, and frequency")
      ).toBeInTheDocument();
    });

    it("shows prompt when fixed-time fields are incomplete (missing timezone)", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="21:00"
          fixedDeadlineTimezone={null}
          movementFrequency="daily"
        />
      );
      expect(
        screen.getByText("Select time, timezone, and frequency")
      ).toBeInTheDocument();
    });

    it("shows prompt when fixed-time fields are incomplete (missing frequency)", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="21:00"
          fixedDeadlineTimezone="America/New_York"
          movementFrequency={null}
        />
      );
      expect(
        screen.getByText("Select time, timezone, and frequency")
      ).toBeInTheDocument();
    });

    it("shows different retreat frequency when specified", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="15:00"
          fixedDeadlineTimezone="America/Los_Angeles"
          movementFrequency="weekly"
          retreatFrequency="daily"
        />
      );
      expect(
        screen.getByText(/Movement: weekly at 3:00 PM PT, Retreat: daily/i)
      ).toBeInTheDocument();
    });

    it("shows single summary when retreat frequency matches movement frequency", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="21:00"
          fixedDeadlineTimezone="America/New_York"
          movementFrequency="daily"
          retreatFrequency="daily"
        />
      );
      expect(screen.getByText(/daily at 9:00 PM ET/i)).toBeInTheDocument();
      expect(screen.queryByText(/Movement:/)).not.toBeInTheDocument();
    });

    it("formats 12:00 as 12:00 PM", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="12:00"
          fixedDeadlineTimezone="UTC"
          movementFrequency="daily"
        />
      );
      expect(screen.getByText(/daily at 12:00 PM UTC/i)).toBeInTheDocument();
    });

    it("formats 00:00 as 12:00 AM", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="00:00"
          fixedDeadlineTimezone="UTC"
          movementFrequency="daily"
        />
      );
      expect(screen.getByText(/daily at 12:00 AM UTC/i)).toBeInTheDocument();
    });

    it("handles unknown timezone by showing full timezone name", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="21:00"
          fixedDeadlineTimezone="Africa/Cairo"
          movementFrequency="daily"
        />
      );
      expect(screen.getByText(/daily at 9:00 PM Africa\/Cairo/i)).toBeInTheDocument();
    });

    it("handles hourly retreat frequency display", () => {
      render(
        <DeadlineSummary
          movementPhaseDuration={null}
          deadlineMode="fixed_time"
          fixedDeadlineTime="21:00"
          fixedDeadlineTimezone="Europe/London"
          movementFrequency="daily"
          retreatFrequency="hourly"
        />
      );
      expect(
        screen.getByText(/Movement: daily at 9:00 PM GMT, Retreat: hourly/i)
      ).toBeInTheDocument();
    });
  });
});
