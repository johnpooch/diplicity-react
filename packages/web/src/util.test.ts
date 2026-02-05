import { describe, it, expect } from "vitest";
import { formatRemainingTime } from "./util";

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
