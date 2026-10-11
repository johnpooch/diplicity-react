import { act, render, screen } from "@testing-library/react";
import {
  MemoryRouter,
  Route,
  Routes,
  useNavigate,
  type NavigateFunction,
} from "react-router";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { GameDetailLayout } from "./GameDetailLayout";
import type { GameRetrieve } from "@/api/generated/endpoints";

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
  game: {
    currentPhaseId: number | null;
    status: string;
    orderStatus?: GameRetrieve["orderStatus"];
  }
) => {
  queryClient.setQueryData([`/game/${gameId}/`], {
    id: gameId,
    members: [],
    sandbox: false,
    ...game,
  });
  await act(() => new Promise(resolve => setTimeout(resolve, 0)));
};

let navigate: NavigateFunction;

const NavigateProbe: React.FC = () => {
  navigate = useNavigate();
  return null;
};

const renderLayout = () => {
  const queryClient = new QueryClient();
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1"]}>
        <NavigateProbe />
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId"
            element={
              <GameDetailLayout>
                <div />
              </GameDetailLayout>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
  const invalidatedKeys = () =>
    invalidateQueries.mock.calls.map(([filters]) => filters?.queryKey);
  return { queryClient, invalidatedKeys };
};

describe("GameDetailLayout phase transitions", () => {
  it("invalidates phase-dependent queries when the current phase advances", async () => {
    const { queryClient, invalidatedKeys } = renderLayout();
    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
    });

    await pollGame(queryClient, "game-1", {
      currentPhaseId: 2,
      status: "active",
    });

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
    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
    });

    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "completed",
    });

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
    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
    });

    await pollGame(queryClient, "game-1", {
      currentPhaseId: 2,
      status: "active",
    });

    expect(invalidatedKeys()).not.toContainEqual(["/game/game-1/"]);
  });

  it("does not invalidate on initial load or when a poll returns the same phase", async () => {
    const { queryClient, invalidatedKeys } = renderLayout();

    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
    });
    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
    });

    expect(invalidatedKeys()).toEqual([]);
  });

  it("does not treat navigating to another game as a phase transition", async () => {
    const { queryClient, invalidatedKeys } = renderLayout();
    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
    });

    act(() => navigate("/game/game-2/phase/7"));
    await pollGame(queryClient, "game-2", {
      currentPhaseId: 7,
      status: "completed",
    });

    expect(invalidatedKeys()).toEqual([]);
  });

  it.each(["completed", "abandoned"])(
    "renames the Players navigation item to Results when the game is %s",
    async status => {
      const { queryClient } = renderLayout();

      await pollGame(queryClient, "game-1", {
        currentPhaseId: 1,
        status,
      });

      const resultsButton = screen.getByRole("button", { name: "Results" });
      expect(resultsButton.querySelector(".lucide-trophy")).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "Players" })
      ).not.toBeInTheDocument();
    }
  );
});

describe("GameDetailLayout orders navigation dot", () => {
  const ordersDot = () =>
    screen
      .getByRole("button", { name: "Orders" })
      .querySelector(".rounded-full.bg-primary");

  it.each(["orders_required", "orders_not_confirmed"] as const)(
    "shows the dot when the order status is %s",
    async orderStatus => {
      const { queryClient } = renderLayout();

      await pollGame(queryClient, "game-1", {
        currentPhaseId: 1,
        status: "active",
        orderStatus,
      });

      expect(ordersDot()).toBeInTheDocument();
    }
  );

  it.each(["orders_submitted", "no_orders_required", null] as const)(
    "hides the dot when the order status is %s",
    async orderStatus => {
      const { queryClient } = renderLayout();

      await pollGame(queryClient, "game-1", {
        currentPhaseId: 1,
        status: "active",
        orderStatus,
      });

      expect(ordersDot()).not.toBeInTheDocument();
    }
  );

  it("hides the dot for a member in civil disorder whose order status is null", async () => {
    const { queryClient } = renderLayout();

    queryClient.setQueryData(["/game/game-1/"], {
      id: "game-1",
      currentPhaseId: 1,
      status: "active",
      sandbox: false,
      orderStatus: null,
      members: [{ isCurrentUser: true, civilDisorder: true, withdrawn: false }],
    });
    await act(() => new Promise(resolve => setTimeout(resolve, 0)));

    expect(ordersDot()).not.toBeInTheDocument();
  });

  it("clears the dot when a poll reports the orders as submitted", async () => {
    const { queryClient } = renderLayout();
    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
      orderStatus: "orders_required",
    });

    await pollGame(queryClient, "game-1", {
      currentPhaseId: 1,
      status: "active",
      orderStatus: "orders_submitted",
    });

    expect(ordersDot()).not.toBeInTheDocument();
  });
});
