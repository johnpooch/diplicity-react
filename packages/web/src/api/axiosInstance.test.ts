import { describe, it, expect } from "vitest";
import { AxiosError, AxiosHeaders } from "axios";
import type { AxiosResponse } from "axios";
import axiosInstance, { customInstance } from "./axiosInstance";
import { isNetworkError } from "@/utils/network";

const respondWith = (status: number, data: unknown) => {
  axiosInstance.defaults.adapter = async config =>
    ({
      status,
      statusText: "",
      data,
      headers: new AxiosHeaders(),
      config,
    }) as AxiosResponse;
};

describe("customInstance", () => {
  it("resolves with the response body", async () => {
    respondWith(200, [{ id: "classical" }]);

    await expect(customInstance({ url: "/variants/" })).resolves.toEqual([
      { id: "classical" },
    ]);
  });

  it("rejects a response with no status rather than returning its empty body", async () => {
    respondWith(0, "");

    await expect(customInstance({ url: "/variants/" })).rejects.toMatchObject({
      code: AxiosError.ERR_NETWORK,
    });
  });

  it("rejects a response with no status as a network error", async () => {
    respondWith(0, "");

    const error = await customInstance({ url: "/variants/" }).catch(e => e);

    expect(isNetworkError(error)).toBe(true);
  });
});
