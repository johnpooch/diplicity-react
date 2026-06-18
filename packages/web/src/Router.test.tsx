import React, { Suspense } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameIndexRoute } from "./Router";

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
