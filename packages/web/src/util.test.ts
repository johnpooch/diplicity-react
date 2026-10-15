import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import {
  formatDateTime,
  formatRemainingTime,
  formatTimeLeft,
  getGameLandingPath,
  isFinishedGameStatus,
} from "./util";

describe("isFinishedGameStatus", () => {
  it("treats completed and abandoned games as finished", () => {
    expect(isFinishedGameStatus("completed")).toBe(true);
    expect(isFinishedGameStatus("abandoned")).toBe(true);
    expect(isFinishedGameStatus("active")).toBe(false);
    expect(isFinishedGameStatus("pending")).toBe(false);
  });
});

describe("formatRemainingTime", () => {
  it("returns 'Deadline passed' for 0 seconds", () => {
    expect(formatRemainingTime(0)).toBe("Deadline passed");
  });

  it("returns 'Deadline passed' for negative seconds", () => {
    expect(formatRemainingTime(-100)).toBe("Deadline passed");
  });

  it("returns '< 1m remaining' for less than 60 seconds", () => {
    expect(formatRemainingTime(30)).toBe("< 1m remaining");
    expect(formatRemainingTime(59)).toBe("< 1m remaining");
  });

  it("returns minutes only for 60-3599 seconds", () => {
    expect(formatRemainingTime(60)).toBe("1m remaining");
    expect(formatRemainingTime(300)).toBe("5m remaining");
    expect(formatRemainingTime(1800)).toBe("30m remaining");
    expect(formatRemainingTime(3540)).toBe("59m remaining");
  });

  it("returns hours and minutes for 3600-86399 seconds", () => {
    expect(formatRemainingTime(3600)).toBe("1h 0m remaining");
    expect(formatRemainingTime(5400)).toBe("1h 30m remaining");
    expect(formatRemainingTime(19800)).toBe("5h 30m remaining");
    expect(formatRemainingTime(82800)).toBe("23h 0m remaining");
  });

  it("returns days and hours for 86400+ seconds", () => {
    expect(formatRemainingTime(86400)).toBe("1d 0h remaining");
    expect(formatRemainingTime(90000)).toBe("1d 1h remaining");
    expect(formatRemainingTime(172800)).toBe("2d 0h remaining");
    expect(formatRemainingTime(259200)).toBe("3d 0h remaining");
  });
});

describe("formatDateTime", () => {
  it("appends a timezone label to the formatted time", () => {
    const result = formatDateTime("2026-02-07T21:00:00Z");
    expect(result).toMatch(
      /^(Today|Tomorrow|\d{2}\/\d{2}\/\d{2}) \d{2}:\d{2} .+$/
    );
  });
});

describe("formatTimeLeft", () => {
  const now = new Date("2026-05-01T12:00:00Z");
  const inMinutes = (minutes: number) =>
    new Date(now.getTime() + minutes * 60 * 1000).toISOString();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(now);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows minutes under an hour", () => {
    expect(formatTimeLeft(inMinutes(0))).toBe("0 min");
    expect(formatTimeLeft(inMinutes(59))).toBe("59 min");
  });

  it("does not go below zero minutes once the deadline has passed", () => {
    expect(formatTimeLeft(inMinutes(-30))).toBe("0 min");
  });

  it("shows hours from one hour to under a day, rounded down", () => {
    expect(formatTimeLeft(inMinutes(60))).toBe("1 hour");
    expect(formatTimeLeft(inMinutes(119))).toBe("1 hour");
    expect(formatTimeLeft(inMinutes(120))).toBe("2 hours");
    expect(formatTimeLeft(inMinutes(24 * 60 - 1))).toBe("23 hours");
  });

  it("shows days from one day, rounded down", () => {
    expect(formatTimeLeft(inMinutes(24 * 60))).toBe("1 day");
    expect(formatTimeLeft(inMinutes(48 * 60 - 1))).toBe("1 day");
    expect(formatTimeLeft(inMinutes(48 * 60))).toBe("2 days");
  });
});

describe("getGameLandingPath", () => {
  it("routes pending games to game-info in the game layout regardless of viewport", () => {
    const game = { id: "abc-1", status: "pending", currentPhaseId: 5 };
    expect(getGameLandingPath(game, true)).toBe("/game/abc-1/phase/5/game-info");
    expect(getGameLandingPath(game, false)).toBe("/game/abc-1/phase/5/game-info");
  });

  it("routes mustering games to game-info in the game layout regardless of viewport", () => {
    const game = { id: "abc-6", status: "mustering", currentPhaseId: 8 };
    expect(getGameLandingPath(game, true)).toBe("/game/abc-6/phase/8/game-info");
    expect(getGameLandingPath(game, false)).toBe("/game/abc-6/phase/8/game-info");
  });

  it("routes pending games to the home game-info when currentPhaseId is null", () => {
    const game = { id: "abc-2", status: "pending", currentPhaseId: null };
    expect(getGameLandingPath(game, true)).toBe("/game-info/abc-2");
    expect(getGameLandingPath(game, false)).toBe("/game-info/abc-2");
  });

  it("routes active games on mobile to the phase index", () => {
    const game = { id: "abc-3", status: "active", currentPhaseId: 7 };
    expect(getGameLandingPath(game, true)).toBe("/game/abc-3/phase/7");
  });

  it("routes active games on desktop to the orders sub-route", () => {
    const game = { id: "abc-3", status: "active", currentPhaseId: 7 };
    expect(getGameLandingPath(game, false)).toBe("/game/abc-3/phase/7/orders");
  });

  it("routes active games with no currentPhaseId back to home", () => {
    const game = { id: "abc-4", status: "active", currentPhaseId: null };
    expect(getGameLandingPath(game, true)).toBe("/");
    expect(getGameLandingPath(game, false)).toBe("/");
  });

  it("routes completed games like active ones", () => {
    const game = { id: "abc-5", status: "completed", currentPhaseId: 12 };
    expect(getGameLandingPath(game, true)).toBe("/game/abc-5/phase/12");
    expect(getGameLandingPath(game, false)).toBe("/game/abc-5/phase/12/orders");
  });
});
