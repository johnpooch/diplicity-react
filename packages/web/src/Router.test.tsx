import React, { Suspense } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, matchRoutes } from "react-router";
import { QueryClient } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import type { LoaderFunctionArgs } from "react-router";
import {
  GameIndexRoute,
  createAuthenticatedRoutes,
  createUnauthenticatedRoutes,
} from "./Router";

const mockUseIsMobile = vi.fn();

vi.mock("./hooks/use-mobile", () => ({
  useIsMobile: () => mockUseIsMobile(),
}));

vi.mock("./screens", () => ({
  GameDetail: {
    MapScreen: React.lazy(() =>
      Promise.resolve({ default: () => <div data-testid="map-screen" /> })
    ),
    OrdersScreen: React.lazy(() =>
      Promise.resolve({ default: () => <div data-testid="orders-screen" /> })
    ),
    GameInfoScreen: React.lazy(() =>
      Promise.resolve({ default: () => <div data-testid="game-info-screen" /> })
    ),
  },
  Home: {},
  Variants: {},
  Tutorial: {},
  Blog: {},
}));

const mockGameStatus = vi.fn();

vi.mock("./api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("./api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: { status: mockGameStatus() } }),
}));

const renderRoute = () =>
  render(
    <MemoryRouter initialEntries={["/game/game-1/phase/5"]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId"
          element={
            <Suspense fallback={null}>
              <GameIndexRoute />
            </Suspense>
          }
        />
      </Routes>
    </MemoryRouter>
  );

describe("GameIndexRoute", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReset();
    mockGameStatus.mockReturnValue("active");
  });

  it("renders MapScreen on mobile", async () => {
    mockUseIsMobile.mockReturnValue(true);
    renderRoute();
    expect(await screen.findByTestId("map-screen")).toBeTruthy();
    expect(screen.queryByTestId("orders-screen")).toBeNull();
  });

  it("renders OrdersScreen on desktop", async () => {
    mockUseIsMobile.mockReturnValue(false);
    renderRoute();
    expect(await screen.findByTestId("orders-screen")).toBeTruthy();
    expect(screen.queryByTestId("map-screen")).toBeNull();
  });

  it("renders GameInfoScreen on desktop for a game that has not started", async () => {
    mockUseIsMobile.mockReturnValue(false);
    mockGameStatus.mockReturnValue("mustering");
    renderRoute();
    expect(await screen.findByTestId("game-info-screen")).toBeTruthy();
    expect(screen.queryByTestId("orders-screen")).toBeNull();
  });
});

describe("createAuthenticatedRoutes", () => {
  it("redirects unknown paths to home so logged-in users never hit a 404", async () => {
    const routes = createAuthenticatedRoutes(new QueryClient());
    const catchAll = routes.find((route) => route.path === "*");

    expect(catchAll).toBeDefined();
    if (typeof catchAll?.loader !== "function") {
      throw new Error("Expected the catch-all route to have a loader");
    }

    const response = await catchAll.loader({
      request: new Request("http://localhost/register"),
      params: {},
    } as unknown as LoaderFunctionArgs);

    expect(response).toBeInstanceOf(Response);
    expect((response as Response).status).toBe(302);
    expect((response as Response).headers.get("Location")).toBe("/");
  });
});

describe("blog routes", () => {
  const routeTrees = [
    ["logged in", createAuthenticatedRoutes(new QueryClient())],
    ["logged out", createUnauthenticatedRoutes()],
  ] as const;

  it.each(routeTrees)("serves the blog index when %s", (_, routes) => {
    const matches = matchRoutes([...routes], "/blog");
    expect(matches?.map(match => match.route.path)).toEqual(["/blog", undefined]);
  });

  it.each(routeTrees)("serves a blog post when %s", (_, routes) => {
    const matches = matchRoutes([...routes], "/blog/spring-1901-update");
    expect(matches?.map(match => match.route.path)).toEqual(["/blog", ":slug"]);
    expect(matches?.at(-1)?.params.slug).toBe("spring-1901-update");
  });
});
