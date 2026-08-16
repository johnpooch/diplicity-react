import { describe, it, expect } from "vitest";
import { AxiosError, AxiosHeaders } from "axios";
import type { AxiosResponse } from "axios";
import { isNetworkError, isNotFoundError } from "./network";

const responseError = (status: number) => {
  const config = { headers: new AxiosHeaders() };
  return new AxiosError(
    `Request failed with status code ${status}`,
    AxiosError.ERR_BAD_REQUEST,
    config,
    undefined,
    { status, statusText: "", data: null, headers: {}, config } as AxiosResponse
  );
};

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

describe("isNotFoundError", () => {
  it("returns true for an axios error with a 404 response", () => {
    expect(isNotFoundError(responseError(404))).toBe(true);
  });

  it("returns false for an axios error with a 500 response", () => {
    expect(isNotFoundError(responseError(500))).toBe(false);
  });

  it("returns false for an axios network error", () => {
    expect(
      isNotFoundError(new AxiosError("Network Error", AxiosError.ERR_NETWORK))
    ).toBe(false);
  });

  it("returns false for a non-axios error", () => {
    expect(isNotFoundError(new Error("Not Found"))).toBe(false);
  });
});
