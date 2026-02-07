import React from "react";

interface DeadlineSummaryGame {
  movementPhaseDuration: string | null;
  retreatPhaseDuration?: string | null;
  deadlineMode?: string;
  fixedDeadlineTime?: string | null;
  fixedDeadlineTimezone?: string | null;
  movementFrequency?: string | null;
  retreatFrequency?: string | null;
}

interface DeadlineSummaryProps {
  game: DeadlineSummaryGame;
}

const FREQUENCY_LABELS: Record<string, string> = {
  hourly: "Hourly",
  daily: "Daily",
  every_2_days: "Every 2 days",
  weekly: "Weekly",
};

const TIMEZONE_ABBREVS: Record<string, string> = {
  "America/New_York": "ET",
  "America/Chicago": "CT",
  "America/Denver": "MT",
  "America/Los_Angeles": "PT",
  "America/Anchorage": "AKT",
  "Pacific/Honolulu": "HT",
  "Europe/London": "GMT",
  "Europe/Dublin": "GMT",
  "Europe/Paris": "CET",
  "Europe/Berlin": "CET",
  "Europe/Moscow": "MSK",
  "Asia/Tokyo": "JST",
  "Asia/Shanghai": "CST",
  "Asia/Kolkata": "IST",
  "Australia/Sydney": "AEST",
  UTC: "UTC",
};

function formatTime12Hour(time: string): string {
  const [hoursStr, minutesStr] = time.split(":");
  const hours = parseInt(hoursStr, 10);
  const minutes = parseInt(minutesStr, 10);
  const ampm = hours >= 12 ? "PM" : "AM";
  const hour12 = hours % 12 || 12;
  return `${hour12}:${minutes.toString().padStart(2, "0")} ${ampm}`;
}

export const DeadlineSummary: React.FC<DeadlineSummaryProps> = ({ game }) => {
  const {
    movementPhaseDuration,
    retreatPhaseDuration,
    deadlineMode = "duration",
    fixedDeadlineTime,
    fixedDeadlineTimezone,
    movementFrequency,
    retreatFrequency,
  } = game;

  if (deadlineMode === "fixed_time") {
    if (!fixedDeadlineTime || !fixedDeadlineTimezone || !movementFrequency) {
      return <span>Select time, timezone, and frequency</span>;
    }

    const freq = FREQUENCY_LABELS[movementFrequency] ?? movementFrequency;
    const tz = TIMEZONE_ABBREVS[fixedDeadlineTimezone] ?? fixedDeadlineTimezone;
    const time = formatTime12Hour(fixedDeadlineTime);

    if (!retreatFrequency || retreatFrequency === movementFrequency) {
      return (
        <span>
          Phases resolve {freq.toLowerCase()} at {time} {tz}
        </span>
      );
    }

    const retreatFreq = FREQUENCY_LABELS[retreatFrequency] ?? retreatFrequency;
    return (
      <span>
        Phases resolve Movement: {freq.toLowerCase()} at {time} {tz}, Retreat: {retreatFreq.toLowerCase()}
      </span>
    );
  }

  if (!movementPhaseDuration) {
    return <span>No automatic deadlines (sandbox)</span>;
  }

  if (
    !retreatPhaseDuration ||
    retreatPhaseDuration === movementPhaseDuration
  ) {
    return <span>Phases resolve every {movementPhaseDuration}</span>;
  }

  return (
    <span>
      Movement: {movementPhaseDuration}, Retreat/Adjustment:{" "}
      {retreatPhaseDuration}
    </span>
  );
};
