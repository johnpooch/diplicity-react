import { act, render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { GameDetailLayout } from "./GameDetailLayout";

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual =
    await importOriginal<typeof import("@/api/generated/endpoints")>();
  return {
    ...actual,
    useGameRetrieve: (gameId: string) =>
      useQuery({
        queryKey: actual.getGameRetrieveQueryKey(gameId),
        queryFn: () => new Promise(() => {}),
        enabled: false,
      }),
  };
});

vi.mock("@/components/GameMap", () => ({ GameMap: () => null }));
vi.mock("@/components/OfflineBanner", () => ({ OfflineBanner: () => null }));

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const pollGame = async (
  queryClient: QueryClient,
  gameId: string,
  game: { currentPhaseId: number | null; status: string }
) => {
  queryClient.setQueryData([`/game/${gameId}/`], {
    id: gameId,
    members: [],
    sandbox: false,
    ...game,
  });
  await act(() => new Promise(resolve => setTimeout(resolve, 0)));
};

const renderLayout = () => {
  const queryClient = new QueryClient();
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  const router = createMemoryRouter(
    [
      {
        path: "/game/:gameId/phase/:phaseId",
        element: (
          <GameDetailLayout>
            <div />
          </GameDetailLayout>
        ),
      },
    ],
    { initialEntries: ["/game/game-1/phase/1"] }
  );
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
  const invalidatedKeys = () =>
    invalidateQueries.mock.calls.map(([filters]) => filters?.queryKey);
  return { queryClient, router, invalidatedKeys };
};

describe("GameDetailLayout phase transitions", () => {
  it("invalidates phase-dependent queries when the current phase advances", async () => {
    const { queryClient, invalidatedKeys } = renderLayout();
    await pollGame(queryClient, "game-1", { currentPhaseId: 1, status: "active" });

    await pollGame(queryClient, "game-1", { currentPhaseId: 2, status: "active" });

    expect(invalidatedKeys()).toEqual([
      ["/game/game-1/phase-states/"],
      ["/game/game-1/options/"],
      ["/game/game-1/phases/"],
      ["/game/game-1/phase/1/"],
      ["/game/game-1/orders/1"],
      ["/game/game-1/phase/2/"],
      ["/game/game-1/orders/2"],
    ]);
  });

  it("invalidates phase-dependent queries when the game status changes on the same phase", async () => {
    const { queryClient, invalidatedKeys } = renderLayout();
    await pollGame(queryClient, "game-1", { currentPhaseId: 1, status: "active" });

    await pollGame(queryClient, "game-1", { currentPhaseId: 1, status: "completed" });

    expect(invalidatedKeys()).toEqual([
      ["/game/game-1/phase-states/"],
      ["/game/game-1/options/"],
      ["/game/game-1/phases/"],
      ["/game/game-1/phase/1/"],
      ["/game/game-1/orders/1"],
    ]);
  });

  it("does not invalidate the polled game query", async () => {
    const { queryClient, invalidatedKeys } = renderLayout();
    await pollGame(queryClient, "game-1", { currentPhaseId: 1, status: "active" });

    await pollGame(queryClient, "game-1", { currentPhaseId: 2, status: "active" });

    expect(invalidatedKeys()).not.toContainEqual(["/game/game-1/"]);
  });

  it("does not invalidate on initial load or when a poll returns the same phase", async () => {
    const { queryClient, invalidatedKeys } = renderLayout();

    await pollGame(queryClient, "game-1", { currentPhaseId: 1, status: "active" });
    await pollGame(queryClient, "game-1", { currentPhaseId: 1, status: "active" });

    expect(invalidatedKeys()).toEqual([]);
  });

  it("does not treat navigating to another game as a phase transition", async () => {
    const { queryClient, router, invalidatedKeys } = renderLayout();
    await pollGame(queryClient, "game-1", { currentPhaseId: 1, status: "active" });

    await act(() => router.navigate("/game/game-2/phase/7"));
    await pollGame(queryClient, "game-2", { currentPhaseId: 7, status: "completed" });

    expect(invalidatedKeys()).toEqual([]);
  });
});
