import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useDraft } from "./useDraft";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

describe("useDraft", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("has no draft id while the draft is empty", () => {
    const { result } = renderHook(() => useDraft("game-1", "7"));

    expect(result.current[0]).toBe("");
    expect(result.current[2]).toBeNull();
  });

  it("gives a non-empty draft a uuid that is stable across renders", () => {
    const { result, rerender } = renderHook(() => useDraft("game-1", "7"));

    act(() => result.current[1]("Hello"));
    const draftId = result.current[2];
    rerender();

    expect(draftId).toMatch(UUID_PATTERN);
    expect(result.current[2]).toBe(draftId);
  });

  it("changes the draft id when the text changes", () => {
    const { result } = renderHook(() => useDraft("game-1", "7"));

    act(() => result.current[1]("Hello"));
    const first = result.current[2];
    act(() => result.current[1]("Hello!"));

    expect(result.current[2]).not.toBe(first);
  });

  it("clears the draft id when the draft is emptied", () => {
    const { result } = renderHook(() => useDraft("game-1", "7"));

    act(() => result.current[1]("Hello"));
    act(() => result.current[1](""));

    expect(result.current[2]).toBeNull();
    expect(sessionStorage.getItem("draft-id:game-1:7")).toBeNull();
  });

  it("keeps the draft id across remounts", () => {
    const first = renderHook(() => useDraft("game-1", "7"));
    act(() => first.result.current[1]("Hello"));
    const draftId = first.result.current[2];
    first.unmount();

    const second = renderHook(() => useDraft("game-1", "7"));

    expect(second.result.current[0]).toBe("Hello");
    expect(second.result.current[2]).toBe(draftId);
  });

  it("keeps one draft id for a restored draft that was saved without one", () => {
    sessionStorage.setItem("draft:game-1:7", "Hello");

    const first = renderHook(() => useDraft("game-1", "7"));
    const draftId = first.result.current[2];
    first.unmount();
    const second = renderHook(() => useDraft("game-1", "7"));

    expect(draftId).toMatch(UUID_PATTERN);
    expect(second.result.current[2]).toBe(draftId);
  });
});
