import React, { Suspense } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import type { LoaderFunctionArgs } from "react-router";
import { GameIndexRoute, createAuthenticatedRoutes } from "./Router";

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
  },
  Home: {},
  Variants: {},
  LLMCalls: {},
  Tutorial: {},
}));

const renderRoute = () =>
  render(
    <MemoryRouter>
      <Suspense fallback={null}>
        <GameIndexRoute />
      </Suspense>
    </MemoryRouter>
  );

describe("GameIndexRoute", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReset();
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
