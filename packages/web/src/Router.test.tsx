import React, { Suspense } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Router, { GameIndexRoute } from "./Router";
import { getVariantsListQueryKey } from "./api/generated/endpoints";

const mockUseIsMobile = vi.fn();

vi.mock("./hooks/use-mobile", () => ({
  useIsMobile: () => mockUseIsMobile(),
}));

vi.mock("./components/HomeLayout", () => ({
  HomeLayout: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("./screens", () => {
  const passthrough: React.FC = () => null;
  const proxy = (overrides: Record<string, React.FC> = {}) =>
    new Proxy(overrides, {
      get: (target, prop) => target[prop as string] ?? passthrough,
    });
  return {
    Home: proxy({ MyGames: () => <div data-testid="home-screen" /> }),
    GameDetail: proxy({
      MapScreen: React.lazy(() =>
        Promise.resolve({ default: () => <div data-testid="map-screen" /> })
      ),
      OrdersScreen: React.lazy(() =>
        Promise.resolve({ default: () => <div data-testid="orders-screen" /> })
      ),
    }),
    Variants: proxy(),
    LLMCalls: proxy(),
    Tutorial: proxy(),
  };
});

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

describe("Router", () => {
  const createQueryClient = () => {
    const queryClient = new QueryClient();
    queryClient.setQueryDefaults(getVariantsListQueryKey(), {
      staleTime: Infinity,
    });
    queryClient.setQueryData(getVariantsListQueryKey(), []);
    return queryClient;
  };

  it("redirects a logged-in user from an unknown path to home", async () => {
    window.history.pushState({}, "", "/register");
    render(<Router loggedIn queryClient={createQueryClient()} />);
    expect(await screen.findByTestId("home-screen")).toBeTruthy();
    expect(window.location.pathname).toBe("/");
  });
});
