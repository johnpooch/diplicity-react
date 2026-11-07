import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GameDetailLayout } from "./GameDetailLayout";

const isMobile = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieve: () => ({ data: undefined }),
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => isMobile() }));

vi.mock("@/components/GameMap", () => ({
  GameMap: () => <div data-testid="game-map" />,
}));

vi.mock("@/components/OfflineBanner", () => ({ OfflineBanner: () => null }));

const renderLayout = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/abc/phase/1/orders"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/orders"
            element={
              <GameDetailLayout>
                <p>Content</p>
              </GameDetailLayout>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("GameDetailLayout map panel", () => {
  beforeEach(() => {
    isMobile.mockReturnValue(false);
  });

  it("renders the map beside the content on desktop", () => {
    renderLayout();

    expect(screen.getByTestId("game-map")).toBeInTheDocument();
  });

  it("does not mount the map on mobile", () => {
    isMobile.mockReturnValue(true);
    renderLayout();

    expect(screen.queryByTestId("game-map")).not.toBeInTheDocument();
  });
});
