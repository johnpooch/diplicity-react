import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  CHANNEL_POLL_SCHEDULE,
  createAdaptiveRefetchInterval,
  GAME_POLL_SCHEDULE,
} from "./adaptiveRefetchInterval";

describe("adaptive refetch interval", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("backs off unchanged game data without using fetch timestamps", () => {
    const { refetchInterval } =
      createAdaptiveRefetchInterval(GAME_POLL_SCHEDULE);
    const query = {
      queryHash: "game",
      state: { data: {}, isInvalidated: false, dataUpdatedAt: Date.now() },
    };

    expect(refetchInterval(query)).toBe(5_000);
    vi.advanceTimersByTime(59_999);
    query.state.dataUpdatedAt = Date.now();
    expect(refetchInterval(query)).toBe(5_000);
    vi.advanceTimersByTime(1);
    expect(refetchInterval(query)).toBe(15_000);
    vi.advanceTimersByTime(239_999);
    query.state.dataUpdatedAt = Date.now();
    expect(refetchInterval(query)).toBe(15_000);
    vi.advanceTimersByTime(1);
    expect(refetchInterval(query)).toBe(60_000);
  });

  it("keeps channel polling at fifteen seconds after two idle minutes", () => {
    const { refetchInterval } = createAdaptiveRefetchInterval(
      CHANNEL_POLL_SCHEDULE
    );
    const query = {
      queryHash: "channel",
      state: { data: {}, isInvalidated: false },
    };

    expect(refetchInterval(query)).toBe(5_000);
    vi.advanceTimersByTime(119_999);
    expect(refetchInterval(query)).toBe(5_000);
    vi.advanceTimersByTime(1);
    expect(refetchInterval(query)).toBe(15_000);
    vi.advanceTimersByTime(600_000);
    expect(refetchInterval(query)).toBe(15_000);
  });

  it.each(["data", "invalidation", "query", "resume"])(
    "resets on %s",
    change => {
      const { refetchInterval, reset } =
        createAdaptiveRefetchInterval(GAME_POLL_SCHEDULE);
      const query = {
        queryHash: "game",
        state: { data: {}, isInvalidated: false },
      };
      expect(refetchInterval(query)).toBe(5_000);
      vi.advanceTimersByTime(300_000);
      expect(refetchInterval(query)).toBe(60_000);

      if (change === "data") query.state.data = {};
      if (change === "invalidation") query.state.isInvalidated = true;
      if (change === "query") query.queryHash = "other-game";
      if (change === "resume") reset();

      expect(refetchInterval(query)).toBe(5_000);
      query.state.isInvalidated = false;
      vi.advanceTimersByTime(60_000);
      expect(refetchInterval(query)).toBe(15_000);
    }
  );

  it.each([undefined, "pending", "mustering", "completed", "abandoned"])(
    "does not poll games with status %s",
    status => {
      const { refetchInterval } = createAdaptiveRefetchInterval<{
        status: string;
      }>(GAME_POLL_SCHEDULE, data => data?.status === "active");
      expect(
        refetchInterval({
          queryHash: "game",
          state: {
            data: status ? { status } : undefined,
            isInvalidated: false,
          },
        })
      ).toBe(false);
    }
  );
});
