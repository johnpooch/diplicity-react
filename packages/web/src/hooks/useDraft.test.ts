import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useDraft } from "./useDraft";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const ID_KEY = "draft-id:game-1:7";

describe("useDraft", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("has no draft id until one is requested", () => {
    const { result } = renderHook(() => useDraft("game-1", "7"));

    act(() => result.current[1]("Hello"));

    expect(sessionStorage.getItem(ID_KEY)).toBeNull();
    expect(result.current[2]()).toMatch(UUID_PATTERN);
  });

  it("returns the same draft id while the text is unchanged", () => {
    const { result, rerender } = renderHook(() => useDraft("game-1", "7"));

    act(() => result.current[1]("Hello"));
    const first = result.current[2]();
    rerender();

    expect(result.current[2]()).toBe(first);
  });

  it("returns a new draft id after the text changes", () => {
    const { result } = renderHook(() => useDraft("game-1", "7"));

    act(() => result.current[1]("Hello"));
    const first = result.current[2]();
    act(() => result.current[1]("Hello!"));

    expect(result.current[2]()).not.toBe(first);
  });

  it("clears the draft id when the draft is cleared", () => {
    const { result } = renderHook(() => useDraft("game-1", "7"));

    act(() => result.current[1]("Hello"));
    result.current[2]();
    act(() => result.current[1](""));

    expect(sessionStorage.getItem(ID_KEY)).toBeNull();
  });

  it("keeps the draft id across remounts", () => {
    const first = renderHook(() => useDraft("game-1", "7"));
    act(() => first.result.current[1]("Hello"));
    const draftId = first.result.current[2]();
    first.unmount();

    const second = renderHook(() => useDraft("game-1", "7"));

    expect(second.result.current[0]).toBe("Hello");
    expect(second.result.current[2]()).toBe(draftId);
  });
});
