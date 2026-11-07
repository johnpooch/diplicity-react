import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

type StartSpan = (
  name: string,
  options: { attributes: Record<string, string> }
) => { end: () => void; setAttribute: () => void; name: string };

const { startSpanSpy, ended, routeRef } = vi.hoisted(() => {
  const ended: string[] = [];
  const startSpanSpy = vi.fn<StartSpan>((name) => ({
    name,
    end: () => ended.push(name),
    setAttribute: vi.fn(),
  }));
  return { startSpanSpy, ended, routeRef: { current: "/" as string | undefined } };
});

vi.mock("@opentelemetry/api", () => ({
  trace: { getTracer: () => ({ startSpan: startSpanSpy }) },
}));

vi.mock("../observability", () => ({
  currentRouteTemplate: () => routeRef.current,
}));

import {
  hasActiveFallbacks,
  markNavigationCommitted,
  startFallbackSpan,
  trackNavigations,
} from "./navigationTelemetry";

type Listener = (state: {
  navigation: { state: string };
  location: { key: string };
}) => void;

const makeRouter = () => {
  let listener: Listener = () => {};
  const router = {
    state: { location: { key: "a" } },
    subscribe: (fn: Listener) => {
      listener = fn;
      return () => {};
    },
  } as unknown as Parameters<typeof trackNavigations>[0];
  const navigate = (key: string, route: string) => {
    routeRef.current = route;
    listener({ navigation: { state: "idle" }, location: { key } });
  };
  return { router, navigate };
};

describe("navigationTelemetry", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    startSpanSpy.mockClear();
    ended.length = 0;
    routeRef.current = "/";
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("ends a navigation span once the destination commits", () => {
    const { router, navigate } = makeRouter();
    trackNavigations(router);

    navigate("b", "/find-games");

    expect(startSpanSpy).toHaveBeenCalledWith("navigation", {
      attributes: { "navigation.from": "/", "navigation.to": "/find-games" },
    });
    expect(ended).toEqual([]);

    markNavigationCommitted();
    vi.runAllTimers();

    expect(ended).toEqual(["navigation"]);
  });

  it("holds the navigation span open while a fallback is mounted", () => {
    const { router, navigate } = makeRouter();
    trackNavigations(router);
    navigate("b", "/find-games");

    const endFallback = startFallbackSpan();
    markNavigationCommitted();
    vi.runAllTimers();
    expect(ended).toEqual([]);

    endFallback();
    vi.runAllTimers();

    expect(ended).toEqual(["suspense.fallback", "navigation"]);
  });

  it("reports active fallbacks while one is mounted", () => {
    expect(hasActiveFallbacks()).toBe(false);

    const endFallback = startFallbackSpan();
    expect(hasActiveFallbacks()).toBe(true);

    endFallback();
    expect(hasActiveFallbacks()).toBe(false);
  });

  it("starts a game.open span when entering a game", () => {
    const { router, navigate } = makeRouter();
    trackNavigations(router);

    navigate("b", "/game/:gameId/phase/:phaseId");
    markNavigationCommitted();
    vi.runAllTimers();

    expect(startSpanSpy).toHaveBeenCalledWith("game.open", {
      attributes: { "game.route": "/game/:gameId/phase/:phaseId" },
    });
    expect(ended).toEqual(["navigation", "game.open"]);
  });

  it("does not start game.open when moving within a game", () => {
    routeRef.current = "/game/:gameId/phase/:phaseId";
    const { router, navigate } = makeRouter();
    trackNavigations(router);

    navigate("b", "/game/:gameId/phase/:phaseId/chat");

    expect(startSpanSpy).not.toHaveBeenCalledWith("game.open", expect.anything());
  });
});
