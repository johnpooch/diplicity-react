import { trace, type Span } from "@opentelemetry/api";
import type { DataRouter } from "react-router";
import { currentRouteTemplate } from "../observability";

const tracer = trace.getTracer("navigation");

const GAME_ROUTE_PREFIX = "/game/:gameId";

interface PendingNavigation {
  navigation: Span;
  gameOpen?: Span;
  fallbackCount: number;
  fallbackMs: number;
  requestCount: number;
  requestDepth: number;
  endedDepth: number;
}

let pending: PendingNavigation | null = null;
let activeFallbacks = 0;
let lastKey: string | undefined;
let lastRoute: string | undefined;
let unsubscribe: (() => void) | null = null;

const isGameRoute = (route: string | undefined) =>
  route?.startsWith(GAME_ROUTE_PREFIX) ?? false;

const endPending = () => {
  if (!pending) return;
  pending.navigation.setAttribute(
    "navigation.fallback_count",
    pending.fallbackCount
  );
  pending.navigation.setAttribute("navigation.fallback_ms", pending.fallbackMs);
  pending.navigation.end();
  if (pending.gameOpen) {
    pending.gameOpen.setAttribute(
      "game.open.request_count",
      pending.requestCount
    );
    pending.gameOpen.setAttribute(
      "game.open.request_depth",
      pending.requestDepth
    );
    pending.gameOpen.end();
  }
  pending = null;
};

const settle = () => {
  if (activeFallbacks > 0) return;
  endPending();
};

const settleSoon = () => {
  setTimeout(settle, 0);
};

export const trackNavigations = (
  router: Pick<DataRouter, "state" | "subscribe">
): void => {
  unsubscribe?.();
  endPending();
  lastKey = router.state.location.key;
  lastRoute = currentRouteTemplate();
  unsubscribe = router.subscribe(state => {
    if (state.navigation.state !== "idle") return;
    if (state.location.key === lastKey) return;
    lastKey = state.location.key;
    const from = lastRoute;
    const to = currentRouteTemplate();
    lastRoute = to;
    if (pending) {
      pending.navigation.setAttribute("navigation.to", to ?? "");
      return;
    }
    pending = {
      navigation: tracer.startSpan("navigation", {
        attributes: {
          "navigation.from": from ?? "",
          "navigation.to": to ?? "",
        },
      }),
      gameOpen:
        isGameRoute(to) && !isGameRoute(from)
          ? tracer.startSpan("game.open", {
              attributes: { "game.route": to ?? "" },
            })
          : undefined,
      fallbackCount: 0,
      fallbackMs: 0,
      requestCount: 0,
      requestDepth: 0,
      endedDepth: 0,
    };
  });
};

export const markNavigationCommitted = settleSoon;

export const startFallbackSpan = (): (() => void) => {
  activeFallbacks += 1;
  const startedAt = Date.now();
  const span = tracer.startSpan("suspense.fallback", {
    attributes: { "fallback.route": currentRouteTemplate() ?? "" },
  });
  return () => {
    span.end();
    if (pending) {
      pending.fallbackCount += 1;
      pending.fallbackMs += Date.now() - startedAt;
    }
    activeFallbacks -= 1;
    settleSoon();
  };
};

export const startRequestTracking = (): (() => void) => {
  const owner = pending;
  if (!owner?.gameOpen) return () => {};
  const depth = owner.endedDepth + 1;
  owner.requestCount += 1;
  owner.requestDepth = Math.max(owner.requestDepth, depth);
  return () => {
    owner.endedDepth = Math.max(owner.endedDepth, depth);
  };
};
