import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { formatMessageTime } from "./formatMessageTime";

describe("formatMessageTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-05-01T18:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns just the time for a message sent today", () => {
    const result = formatMessageTime("2026-05-01T12:00:00Z");
    expect(result).not.toMatch(/May/);
  });

  it("includes the date for a message sent on a previous day", () => {
    const result = formatMessageTime("2026-04-29T12:00:00Z");
    expect(result).toMatch(/Apr/);
  });
});
