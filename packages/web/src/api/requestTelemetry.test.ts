import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import axios from "axios";
import { QueryClient } from "@tanstack/react-query";
import type { InternalAxiosRequestConfig } from "axios";
import {
  classifyRequest,
  registerQueryClient,
  requestTagFor,
  taggedXhrAdapter,
  trackXhrRequestTags,
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
    trackXhrRequestTags();
  });

  it("attaches the tag to the XHR opened for the request and to no other", async () => {
    const opened: XMLHttpRequest[] = [];
    vi.spyOn(axios, "getAdapter").mockReturnValue((() => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "http://api.test/user/");
      opened.push(xhr);
      return Promise.resolve({});
    }) as never);

    await taggedXhrAdapter(config("/user/", "post"));
    const untagged = new XMLHttpRequest();
    untagged.open("GET", "http://api.test/other/");

    expect(requestTagFor(opened[0])).toEqual({
      blocking: true,
      reason: "mutation",
      duplicate: false,
    });
    expect(requestTagFor(untagged)).toBeUndefined();
  });

  describe("duplicate detection", () => {
    const tagsFor = async (...requests: InternalAxiosRequestConfig[]) => {
      const opened: XMLHttpRequest[] = [];
      vi.spyOn(axios, "getAdapter").mockReturnValue((() => {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", "http://api.test/x/");
        opened.push(xhr);
        return Promise.resolve({});
      }) as never);
      for (const request of requests) await taggedXhrAdapter(request);
      return opened.map(xhr => requestTagFor(xhr)?.duplicate);
    };

    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it("flags the same method and URL requested within 5 seconds", async () => {
      expect(await tagsFor(config("/a/"), config("/a/"))).toEqual([
        false,
        true,
      ]);
    });

    it("does not flag a different URL or method", async () => {
      expect(
        await tagsFor(config("/a/"), config("/b/"), config("/a/", "post"))
      ).toEqual([false, false, false]);
    });

    it("does not flag a request made 5 seconds or more later", async () => {
      const first = await tagsFor(config("/a/"));
      vi.advanceTimersByTime(5000);
      const second = await tagsFor(config("/a/"));

      expect([...first, ...second]).toEqual([false, false]);
    });
  });
});
