import { describe, it, expect } from "vitest";
import { AxiosError } from "axios";
import { isNetworkError } from "./network";

describe("isNetworkError", () => {
  it("returns true for an axios network error", () => {
    expect(
      isNetworkError(new AxiosError("Network Error", AxiosError.ERR_NETWORK))
    ).toBe(true);
  });

  it("returns false for an axios error with a response code", () => {
    expect(
      isNetworkError(new AxiosError("Not Found", AxiosError.ERR_BAD_REQUEST))
    ).toBe(false);
  });

  it("returns false for a non-axios error", () => {
    expect(isNetworkError(new Error("Network Error"))).toBe(false);
  });

  it("returns false for a non-error value", () => {
    expect(isNetworkError("offline")).toBe(false);
  });
});
