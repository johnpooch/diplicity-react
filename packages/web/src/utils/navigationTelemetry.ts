import { trace, type Span } from "@opentelemetry/api";
import type { DataRouter } from "react-router";
import { currentRouteTemplate } from "../observability";

const tracer = trace.getTracer("navigation");

const GAME_ROUTE_PREFIX = "/game/:gameId";

interface PendingNavigation {
  navigation: Span;
  gameOpen?: Span;
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
  pending.navigation.end();
  pending.gameOpen?.end();
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
  unsubscribe = router.subscribe((state) => {
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
        attributes: { "navigation.from": from ?? "", "navigation.to": to ?? "" },
      }),
      gameOpen:
        isGameRoute(to) && !isGameRoute(from)
          ? tracer.startSpan("game.open", {
              attributes: { "game.route": to ?? "" },
            })
          : undefined,
    };
  });
};

export const markNavigationCommitted = settleSoon;

export const startFallbackSpan = (): (() => void) => {
  activeFallbacks += 1;
  const span = tracer.startSpan("suspense.fallback", {
    attributes: { "fallback.route": currentRouteTemplate() ?? "" },
  });
  return () => {
    span.end();
    activeFallbacks -= 1;
    settleSoon();
  };
};
