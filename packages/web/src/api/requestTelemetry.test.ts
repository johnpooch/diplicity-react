import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import type { InternalAxiosRequestConfig } from "axios";
import {
  classifyRequest,
  consumeRequestTag,
  recordRequestTag,
  registerQueryClient,
  resetRequestTags,
} from "./requestTelemetry";

const config = (url: string, method = "get"): InternalAxiosRequestConfig =>
  ({
    url,
    method,
    baseURL: "http://api.test",
    headers: {},
  }) as InternalAxiosRequestConfig;

const startFetch = (
  client: QueryClient,
  url: string,
  options: {
    data?: unknown;
    observe?: boolean;
    interval?: number;
    prefetch?: boolean;
  } = {}
) => {
  const options_ = {
    queryKey: [url],
    queryFn: () => new Promise<unknown>(() => {}),
    ...(options.prefetch ? { meta: { prefetch: true } } : {}),
    ...(options.interval ? { refetchInterval: options.interval } : {}),
  };
  if (options.data !== undefined) client.setQueryData([url], options.data);
  if (options.observe) {
    client.getQueryCache().build(client, options_);
    const query = client.getQueryCache().find({ queryKey: [url] })!;
    query.addObserver({ options: options_, onQueryUpdate() {} } as never);
  }
  void client.fetchQuery({ ...options_, staleTime: 0 });
  return client.getQueryCache().find({ queryKey: [url] })!;
};

describe("classifyRequest", () => {
  let client: QueryClient;

  beforeEach(() => {
    client = new QueryClient();
    registerQueryClient(client);
    resetRequestTags();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("marks a fetch with no cached data and an observer as blocking on mount", () => {
    startFetch(client, "/game/1/", { observe: true });

    expect(classifyRequest(config("/game/1/"))).toEqual({
      blocking: true,
      reason: "mount",
    });
  });

  it("marks a suspense mount fetching before any observer subscribes as a mount", () => {
    startFetch(client, "/game/1/");

    expect(classifyRequest(config("/game/1/"))).toEqual({
      blocking: true,
      reason: "mount",
    });
  });

  it("marks a refetch right after an observer mounts as a mount even when it polls", () => {
    startFetch(client, "/game/1/", { data: { id: 1 } });
    const query = client.getQueryCache().find({ queryKey: ["/game/1/"] })!;
    query.addObserver({
      options: { queryKey: ["/game/1/"], refetchInterval: 5000 },
      onQueryUpdate() {},
    } as never);
    client
      .getQueryCache()
      .notify({ type: "observerAdded", query, observer: {} as never });

    expect(classifyRequest(config("/game/1/"))).toEqual({
      blocking: false,
      reason: "mount",
    });
  });

  it("marks a fetch flagged as a prefetch as a background prefetch", () => {
    startFetch(client, "/variants/", { prefetch: true });

    expect(classifyRequest(config("/variants/"))).toEqual({
      blocking: true,
      reason: "prefetch",
    });
  });

  it("marks a refetch with cached data and a refetch interval as a background poll", () => {
    startFetch(client, "/game/1/", {
      data: { id: 1 },
      observe: true,
      interval: 5000,
    });
    vi.advanceTimersByTime(2000);

    expect(classifyRequest(config("/game/1/"))).toEqual({
      blocking: false,
      reason: "poll",
    });
  });

  it("marks a refetch of an invalidated query as an invalidation", () => {
    const query = startFetch(client, "/game/1/", {
      data: { id: 1 },
      observe: true,
      interval: 5000,
    });
    query.setState({ isInvalidated: true });

    expect(classifyRequest(config("/game/1/"))).toEqual({
      blocking: false,
      reason: "invalidation",
    });
  });

  it("treats a non-GET request as a blocking mutation", () => {
    expect(classifyRequest(config("/game/1/join/", "post"))).toEqual({
      blocking: true,
      reason: "mutation",
    });
  });
});

describe("request tag hand-off", () => {
  beforeEach(() => {
    registerQueryClient(new QueryClient());
    resetRequestTags();
  });

  it("hands each recorded tag to the span for the same method and URL once", () => {
    recordRequestTag(config("/user/", "post"));

    expect(consumeRequestTag("POST", "http://api.test/user/")).toEqual({
      blocking: true,
      reason: "mutation",
    });
    expect(consumeRequestTag("POST", "http://api.test/user/")).toBeUndefined();
  });
});
