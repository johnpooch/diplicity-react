import { describe, it, expect, afterEach } from "vitest";
import axios, { AxiosError, AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import axiosInstance, { customInstance } from "./axiosInstance";
import { tokenStorage } from "@/auth/tokenStorage";
import { isNetworkError } from "@/utils/network";
import packageJson from "../../package.json";

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

  it("gives up on a request after 30 seconds with a timeout error", async () => {
    let request: InternalAxiosRequestConfig | undefined;
    axiosInstance.defaults.adapter = async config => {
      request = config;
      return {
        status: 200,
        statusText: "",
        data: [],
        headers: new AxiosHeaders(),
        config,
      } as AxiosResponse;
    };

    await customInstance({ url: "/variants/" });

    expect(request?.timeout).toBe(30_000);
    expect(request?.transitional?.clarifyTimeoutError).toBe(true);
  });
});

describe("client version header", () => {
  const defaultAdapter = axios.defaults.adapter;

  afterEach(() => {
    axios.defaults.adapter = defaultAdapter;
    tokenStorage.clearTokens();
  });

  it("sends the web bundle version on API requests", async () => {
    let request: InternalAxiosRequestConfig | undefined;
    axiosInstance.defaults.adapter = async config => {
      request = config;
      return {
        status: 200,
        statusText: "",
        data: [],
        headers: new AxiosHeaders(),
        config,
      } as AxiosResponse;
    };

    await customInstance({ url: "/variants/" });

    expect(request?.headers["X-Client-Version"]).toBe(packageJson.version);
  });

  it("sends the web bundle version when refreshing the access token", async () => {
    tokenStorage.setTokens({
      accessToken: "expired",
      refreshToken: "refresh",
      email: "player@example.com",
      name: "Player",
    });
    let rejected = false;
    axiosInstance.defaults.adapter = async config => {
      const response = {
        status: rejected ? 200 : 401,
        statusText: "",
        data: [],
        headers: new AxiosHeaders(),
        config,
      } as AxiosResponse;
      if (rejected) return response;
      rejected = true;
      throw new AxiosError("Unauthorized", "401", config, null, response);
    };
    let refreshRequest: InternalAxiosRequestConfig | undefined;
    axios.defaults.adapter = async config => {
      refreshRequest = config;
      return {
        status: 200,
        statusText: "",
        data: { access: "fresh" },
        headers: new AxiosHeaders(),
        config,
      } as AxiosResponse;
    };

    await customInstance({ url: "/variants/" });

    expect(refreshRequest?.url).toContain("/api/token/refresh/");
    expect(refreshRequest?.headers["X-Client-Version"]).toBe(
      packageJson.version
    );
  });
});
