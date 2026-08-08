import { describe, it, expect } from "vitest";
import { formatRemainingTime, getGameInfoPath, getGameLandingPath, getPlayerInfoPath } from "./util";

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

describe("getGameInfoPath", () => {
  it("routes to the shell game-info tab when a phase exists", () => {
    const game = { id: "abc-1", currentPhaseId: 5 };
    expect(getGameInfoPath(game)).toBe("/game/abc-1/phase/5/game-info");
  });

  it("falls back to the game redirect route when there is no current phase", () => {
    const game = { id: "abc-2", currentPhaseId: null };
    expect(getGameInfoPath(game)).toBe("/game/abc-2");
  });
});

describe("getPlayerInfoPath", () => {
  it("routes to the shell player-info tab when a phase exists", () => {
    const game = { id: "abc-1", currentPhaseId: 5 };
    expect(getPlayerInfoPath(game)).toBe("/game/abc-1/phase/5/player-info");
  });

  it("falls back to the game redirect route when there is no current phase", () => {
    const game = { id: "abc-2", currentPhaseId: null };
    expect(getPlayerInfoPath(game)).toBe("/game/abc-2");
  });
});

describe("getGameLandingPath", () => {
  it("routes pending games to the shell game-info tab regardless of viewport", () => {
    const game = { id: "abc-1", status: "pending", currentPhaseId: 5 };
    expect(getGameLandingPath(game, true)).toBe("/game/abc-1/phase/5/game-info");
    expect(getGameLandingPath(game, false)).toBe("/game/abc-1/phase/5/game-info");
  });

  it("routes pending games with no currentPhaseId back to home", () => {
    const game = { id: "abc-2", status: "pending", currentPhaseId: null };
    expect(getGameLandingPath(game, true)).toBe("/");
    expect(getGameLandingPath(game, false)).toBe("/");
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
