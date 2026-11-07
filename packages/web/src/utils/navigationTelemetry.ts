import { trace, type Span } from "@opentelemetry/api";
import type { DataRouter } from "react-router";
import { currentRouteTemplate } from "../observability";

const tracer = trace.getTracer("navigation");

const GAME_ROUTE_PREFIX = "/game/:gameId";

let navigation: Span | null = null;
let gameOpen: Span | null = null;
let activeFallbacks = 0;
let lastKey: string | undefined;
let lastRoute: string | undefined;
let unsubscribe: (() => void) | null = null;

const isGameRoute = (route: string | undefined) =>
  route?.startsWith(GAME_ROUTE_PREFIX) ?? false;

const endNavigation = () => {
  navigation?.end();
  navigation = null;
};

const endGameOpen = () => {
  gameOpen?.end();
  gameOpen = null;
};

const settle = () => {
  if (activeFallbacks > 0) return;
  endNavigation();
};

const settleSoon = () => {
  setTimeout(settle, 0);
};

const begin = (from: string | undefined, to: string | undefined) => {
  if (navigation) {
    navigation.setAttribute("navigation.superseded", true);
    endNavigation();
  }
  navigation = tracer.startSpan("navigation", {
    attributes: { "navigation.from": from ?? "", "navigation.to": to ?? "" },
  });
  if (!isGameRoute(to)) {
    if (gameOpen) gameOpen.setAttribute("game.abandoned", true);
    endGameOpen();
  } else if (!gameOpen && !isGameRoute(from)) {
    gameOpen = tracer.startSpan("game.open", {
      attributes: { "game.route": to ?? "" },
    });
  }
};

export const trackNavigations = (
  router: Pick<DataRouter, "state" | "subscribe">
): void => {
  unsubscribe?.();
  endNavigation();
  endGameOpen();
  lastKey = router.state.location.key;
  lastRoute = currentRouteTemplate();
  begin(undefined, lastRoute);
  unsubscribe = router.subscribe((state) => {
    if (state.navigation.state !== "idle") return;
    if (state.location.key === lastKey) return;
    lastKey = state.location.key;
    const from = lastRoute;
    const to = currentRouteTemplate();
    lastRoute = to;
    begin(from, to);
  });
};

export const markNavigationCommitted = settleSoon;

export const markGameUsable = endGameOpen;

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
