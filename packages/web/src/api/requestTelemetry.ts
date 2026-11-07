import axios from "axios";
import type { InternalAxiosRequestConfig } from "axios";
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

let registeredClient: QueryClient | null = null;
let lastFocusAt = 0;
let pendingTags = new Map<string, RequestTag[]>();

focusManager.subscribe(focused => {
  if (focused) lastFocusAt = Date.now();
});

export const registerQueryClient = (client: QueryClient) => {
  registeredClient = client;
};

export const resetRequestTags = () => {
  pendingTags = new Map();
  lastFocusAt = 0;
};

const tagKey = (method: string, url: string) =>
  `${method.toUpperCase()} ${url}`;

const classifyQuery = (query: Query): RequestTag => {
  const blocking = query.state.data === undefined;
  if (query.getObserversCount() === 0) return { blocking, reason: "prefetch" };
  if (blocking) return { blocking, reason: "mount" };
  if (query.state.isInvalidated) return { blocking, reason: "invalidation" };
  if (Date.now() - lastFocusAt < FOCUS_WINDOW_MS) {
    return { blocking, reason: "focus" };
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

export const recordRequestTag = (config: InternalAxiosRequestConfig) => {
  const key = tagKey(config.method ?? "get", axios.getUri(config));
  const queue = pendingTags.get(key) ?? [];
  queue.push(classifyRequest(config));
  pendingTags.set(key, queue);
};

export const consumeRequestTag = (
  method: unknown,
  url: unknown
): RequestTag | undefined => {
  if (typeof method !== "string" || typeof url !== "string") return undefined;
  const key = tagKey(method, url);
  const queue = pendingTags.get(key);
  const tag = queue?.shift();
  if (queue && queue.length === 0) pendingTags.delete(key);
  return tag;
};
