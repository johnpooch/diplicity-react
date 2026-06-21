import React from "react";

const FREQUENCY_SECONDS: Record<string, number> = {
  hourly: 3600,
  daily: 86400,
  every_2_days: 172800,
  weekly: 604800,
};

function formatDurationSeconds(seconds: number): string {
  if (seconds < 3600) {
    const mins = Math.round(seconds / 60);
    return `${mins} ${mins === 1 ? "minute" : "minutes"}`;
  }
  if (seconds % 86400 === 0) {
    const days = seconds / 86400;
    return `${days} ${days === 1 ? "day" : "days"}`;
  }
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);
  if (mins === 0) return `${hrs} ${hrs === 1 ? "hour" : "hours"}`;
  return `${hrs}h ${mins}m`;
}

interface DeadlineSummaryGame {
  movementPhaseDuration: string | null;
  retreatPhaseDuration?: string | null;
  deadlineMode?: string;
  fixedDeadlineTime?: string | null;
  fixedDeadlineTimezone?: string | null;
  movementFrequency?: string | null;
  retreatFrequency?: string | null;
  acceleratedPhaseWindowSeconds?: number | null;
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

const FREQUENCY_INTERVAL_MINUTES: Record<string, number> = {
  hourly: 60,
};

const FREQUENCY_INTERVAL_LABELS: Record<string, string> = {
  hourly: "1 hour",
};

function isSubDaily(frequency: string): boolean {
  return frequency in FREQUENCY_INTERVAL_MINUTES;
}

function addMinutesToTime(time: string, minutes: number): string {
  const [hoursStr, minutesStr] = time.split(":");
  const total = parseInt(hoursStr, 10) * 60 + parseInt(minutesStr, 10) + minutes;
  const h = Math.floor(total / 60) % 24;
  const m = total % 60;
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
}

function firstPhaseEndTime(time: string, frequency: string): string {
  const interval = FREQUENCY_INTERVAL_MINUTES[frequency];
  return addMinutesToTime(time, interval);
}

function formatFreqTime(frequency: string, time: string, tz: string): string {
  if (frequency === "hourly") {
    return `every hour at ${time} ${tz}`;
  }
  const label = FREQUENCY_LABELS[frequency] ?? frequency;
  return `${label.toLowerCase()} at ${time} ${tz}`;
}

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
    acceleratedPhaseWindowSeconds,
  } = game;

  if (deadlineMode === "fixed_time") {
    if (!fixedDeadlineTime || !fixedDeadlineTimezone || !movementFrequency) {
      return <span>Select time, timezone, and frequency</span>;
    }

    const tz = TIMEZONE_ABBREVS[fixedDeadlineTimezone] ?? fixedDeadlineTimezone;
    const time = formatTime12Hour(fixedDeadlineTime);
    const sameFrequency = !retreatFrequency || retreatFrequency === movementFrequency;

    if (acceleratedPhaseWindowSeconds) {
      const movementCycle = FREQUENCY_SECONDS[movementFrequency];
      const floor = movementCycle
        ? movementCycle - acceleratedPhaseWindowSeconds
        : null;
      return (
        <span>
          Movement resolves {formatFreqTime(movementFrequency, time, tz)}.
          Retreat and adjustment phases can resolve early if everyone confirms
          within {formatDurationSeconds(acceleratedPhaseWindowSeconds)}, but
          movement turns are always at least{" "}
          {floor !== null ? formatDurationSeconds(floor) : "the full cycle"}.
        </span>
      );
    }

    if (isSubDaily(movementFrequency)) {
      const firstEnd = formatTime12Hour(firstPhaseEndTime(fixedDeadlineTime, movementFrequency));
      if (sameFrequency) {
        return (
          <span>
            The first phase ends at {firstEnd} {tz}, after that every hour,
            regardless of whether players confirmed their orders.
          </span>
        );
      }
      const retreatDisplay = formatFreqTime(retreatFrequency!, time, tz);
      return (
        <span>
          The first phase ends at {firstEnd} {tz}, after that Movement: every
          hour and Retreat/Adjustment: {retreatDisplay}, regardless of whether
          players confirmed their orders.
        </span>
      );
    }

    if (retreatFrequency && isSubDaily(retreatFrequency)) {
      const intervalLabel = FREQUENCY_INTERVAL_LABELS[retreatFrequency] ?? retreatFrequency;
      return (
        <span>
          Movement resolves {formatFreqTime(movementFrequency, time, tz)}.
          Retreat/Adjustment resolves {intervalLabel} later, regardless
          of whether players confirmed their orders.
        </span>
      );
    }

    if (sameFrequency) {
      return (
        <span>
          Phases resolve {formatFreqTime(movementFrequency, time, tz)},
          regardless of whether players confirmed their orders.
        </span>
      );
    }

    return (
      <span>
        Phases resolve Movement: {formatFreqTime(movementFrequency, time, tz)},
        Retreat: {formatFreqTime(retreatFrequency!, time, tz)}, regardless of
        whether players confirmed their orders.
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
    return (
      <span>
        Phases resolve every {movementPhaseDuration}, but earlier if all players
        confirmed their orders.
      </span>
    );
  }

  return (
    <span>
      Movement: {movementPhaseDuration}, Retreat/Adjustment:{" "}
      {retreatPhaseDuration}. Both will resolve earlier if all players confirmed
      their orders.
    </span>
  );
};
