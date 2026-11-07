import { act, renderHook } from "@testing-library/react";
import { focusManager } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GAME_POLL_SCHEDULE } from "./adaptiveRefetchInterval";
import { useAdaptiveRefetchInterval } from "./useAdaptiveRefetchInterval";

describe("useAdaptiveRefetchInterval", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    focusManager.setFocused(undefined);
    vi.useRealTimers();
  });

  it("keeps its idle history across renders and resets on foregrounding", () => {
    const { result, rerender } = renderHook(() =>
      useAdaptiveRefetchInterval(GAME_POLL_SCHEDULE)
    );
    const query = {
      queryHash: "game",
      state: { data: {}, isInvalidated: false },
    };
    expect(result.current(query)).toBe(5_000);
    vi.advanceTimersByTime(300_000);
    rerender();
    expect(result.current(query)).toBe(60_000);

    act(() => {
      focusManager.setFocused(false);
    });
    vi.advanceTimersByTime(300_000);
    act(() => {
      focusManager.setFocused(true);
    });

    expect(result.current(query)).toBe(5_000);
  });
});
