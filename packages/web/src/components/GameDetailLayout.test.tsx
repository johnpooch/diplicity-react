import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GameDetailLayout } from "./GameDetailLayout";

const isMobile = vi.fn();
const useGameRetrieve = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieve: (...args: unknown[]) => useGameRetrieve(...args),
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

const gameQueryOptions = () => {
  const [, options] = useGameRetrieve.mock.lastCall as [
    string,
    {
      query: {
        refetchInterval: (query: unknown) => number | false;
        refetchOnWindowFocus: (query: unknown) => boolean | "always";
      };
    },
  ];
  return options.query;
};

const queryWithStatus = (status: string) => ({
  state: { data: { status } },
});

describe("GameDetailLayout map panel", () => {
  beforeEach(() => {
    isMobile.mockReturnValue(false);
    useGameRetrieve.mockReturnValue({ data: undefined });
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

describe("GameDetailLayout game polling", () => {
  beforeEach(() => {
    isMobile.mockReturnValue(false);
    useGameRetrieve.mockReturnValue({ data: undefined });
  });

  it("polls an active game every 30 seconds", () => {
    renderLayout();

    expect(gameQueryOptions().refetchInterval(queryWithStatus("active"))).toBe(
      30000
    );
  });

  it("does not poll a game that is not active", () => {
    renderLayout();

    expect(
      gameQueryOptions().refetchInterval(queryWithStatus("completed"))
    ).toBe(false);
  });

  it("refetches an active game when the app regains focus", () => {
    renderLayout();

    expect(
      gameQueryOptions().refetchOnWindowFocus(queryWithStatus("active"))
    ).toBe("always");
  });

  it("does not refetch a game that is not active on focus", () => {
    renderLayout();

    expect(
      gameQueryOptions().refetchOnWindowFocus(queryWithStatus("completed"))
    ).toBe(false);
  });
});
