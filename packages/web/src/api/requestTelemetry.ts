import axios from "axios";
import type { AxiosAdapter, InternalAxiosRequestConfig } from "axios";
import { focusManager } from "@tanstack/react-query";
import type { Query, QueryClient } from "@tanstack/react-query";

export type RequestReason =
  | "mount"
  | "poll"
  | "focus"
  | "invalidation"
  | "prefetch"
  | "mutation"
  | "other";

export interface RequestTag {
  blocking: boolean;
  reason: RequestReason;
}

const FOCUS_WINDOW_MS = 1000;
const MOUNT_WINDOW_MS = 1000;

let registeredClient: QueryClient | null = null;
let lastFocusAt = 0;
let tagInFlight: RequestTag | undefined;
const xhrTags = new WeakMap<XMLHttpRequest, RequestTag>();
const lastObserverAddedAt = new Map<string, number>();
let unsubscribeCache: (() => void) | null = null;

focusManager.subscribe(focused => {
  if (focused) lastFocusAt = Date.now();
});

export const registerQueryClient = (client: QueryClient) => {
  unsubscribeCache?.();
  lastObserverAddedAt.clear();
  registeredClient = client;
  unsubscribeCache = client.getQueryCache().subscribe(event => {
    if (event.type === "observerAdded") {
      lastObserverAddedAt.set(event.query.queryHash, Date.now());
    }
  });
};

const classifyQuery = (query: Query): RequestTag => {
  const blocking = query.state.data === undefined;
  if (query.meta?.prefetch === true) return { blocking, reason: "prefetch" };
  if (blocking) return { blocking, reason: "mount" };
  if (query.state.isInvalidated) return { blocking, reason: "invalidation" };
  if (Date.now() - lastFocusAt < FOCUS_WINDOW_MS) {
    return { blocking, reason: "focus" };
  }
  const mountedAt = lastObserverAddedAt.get(query.queryHash);
  if (mountedAt !== undefined && Date.now() - mountedAt < MOUNT_WINDOW_MS) {
    return { blocking, reason: "mount" };
  }
  const polling = query.observers.some(observer => {
    const interval = observer.options.refetchInterval;
    return typeof interval === "function"
      ? Boolean(interval(query))
      : Boolean(interval);
  });
  return { blocking, reason: polling ? "poll" : "mount" };
};

export const classifyRequest = (
  config: InternalAxiosRequestConfig
): RequestTag => {
  if ((config.method ?? "get").toLowerCase() !== "get") {
    return { blocking: true, reason: "mutation" };
  }
  const query = registeredClient
    ?.getQueryCache()
    .findAll({ fetchStatus: "fetching" })
    .find(candidate => candidate.queryKey[0] === config.url);
  return query ? classifyQuery(query) : { blocking: true, reason: "other" };
};

export const taggedXhrAdapter: AxiosAdapter = config => {
  tagInFlight = classifyRequest(config);
  try {
    return axios.getAdapter("xhr")(config);
  } finally {
    tagInFlight = undefined;
  }
};

export const trackXhrRequestTags = () => {
  const originalOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (
    this: XMLHttpRequest,
    ...args: Parameters<XMLHttpRequest["open"]>
  ) {
    if (tagInFlight) xhrTags.set(this, tagInFlight);
    return originalOpen.apply(this, args);
  } as XMLHttpRequest["open"];
};

export const requestTagFor = (xhr: XMLHttpRequest): RequestTag | undefined =>
  xhrTags.get(xhr);
