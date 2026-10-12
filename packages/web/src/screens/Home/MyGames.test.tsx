import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import { MyGames } from "./MyGames";
import { classicalVariant } from "@/mocks/fixtures";
import type {
  MyGamesSectionKeyEnum,
  MyGame,
  MyGameState,
  MyGamesCurrent,
  PaginatedMyGameList,
} from "@/api/generated/endpoints";

const mockUseGamesMineCurrentRetrieveSuspense = vi.fn();
const mockGamesMineFinishedList = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useGamesMineCurrentRetrieveSuspense: (...args: unknown[]) =>
      mockUseGamesMineCurrentRetrieveSuspense(...args),
    gamesMineFinishedList: (...args: unknown[]) => mockGamesMineFinishedList(...args),
    useVariantsListSuspense: () => ({ data: [classicalVariant] }),
    useVariantsRetrieve: () => ({ data: undefined }),
    useUserRetrieveSuspense: () => ({
      data: { id: 1, email: "test@example.com", name: "Test", picture: null },
    }),
  };
});

vi.mock("@/hooks/useInfiniteScroll", () => ({
  useInfiniteScroll: () => ({ current: null }),
}));

vi.mock("@/components/MapView", () => ({
  MapView: () => <div data-testid="map-preview" />,
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

const now = new Date("2026-05-01T12:00:00Z");
const inHours = (hours: number) =>
  new Date(now.getTime() + hours * 60 * 60 * 1000).toISOString();

let gameCounter = 0;

const makeGame = (
  state: Partial<MyGameState> & Pick<MyGameState, "kind">,
  overrides: Partial<MyGame> = {}
): MyGame => ({
  id: `game-${++gameCounter}`,
  name: `Game ${gameCounter}`,
  status: "active",
  variantId: classicalVariant.id,
  sandbox: false,
  currentPhaseId: 1,
  currentPhase: null,
  nation: "England",
  seats: null,
  unreadCount: 0,
  state: { deadline: null, result: null, winner: null, departure: null, ...state },
  ...overrides,
});

const current = (...sections: [MyGamesSectionKeyEnum, MyGame[]][]): MyGamesCurrent => ({
  sections: sections.map(([key, games]) => ({ key, games })),
});

const finished = (games: MyGame[]): PaginatedMyGameList => ({
  count: games.length,
  next: null,
  previous: null,
  results: games,
});

const LocationDisplay = () => {
  const location = useLocation();
  return <div data-testid="location">{location.search}</div>;
};

const renderMyGames = (path = "/") => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <MyGames />
        <LocationDisplay />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const setCurrent = (data: MyGamesCurrent) =>
  mockUseGamesMineCurrentRetrieveSuspense.mockReturnValue({ data });

const renderCurrentGame = (game: MyGame) => {
  setCurrent(current(["active", [game]]));
  renderMyGames();
};

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(now);
  mockUseGamesMineCurrentRetrieveSuspense.mockReset();
  setCurrent(current());
  mockGamesMineFinishedList.mockReset();
  mockGamesMineFinishedList.mockResolvedValue(finished([]));
});

afterEach(() => {
  vi.useRealTimers();
});

describe("MyGames Current sections", () => {
  it("renders sections in the order received with their titles", () => {
    setCurrent(
      current(
        ["sandbox", [makeGame({ kind: "sandbox" }, { sandbox: true })]],
        ["needs_attention", [makeGame({ kind: "submit_orders" })]],
        ["managing", [makeGame({ kind: "resolving" })]],
        ["active", [makeGame({ kind: "paused" })]],
        ["mustering", [makeGame({ kind: "seat_confirmed" })]],
        ["pending", [makeGame({ kind: "waiting_for_players" })]],
        ["recently_finished", [makeGame({ kind: "finished", result: "draw" })]]
      )
    );
    renderMyGames();

    expect(
      screen.getAllByRole("heading", { level: 2 }).map(h => h.textContent)
    ).toEqual([
      "Sandbox",
      "Needs attention",
      "Managing",
      "Active",
      "Mustering",
      "Pending",
      "Recently finished",
    ]);
  });

  it("renders each game's name under its section", () => {
    const game = makeGame({ kind: "submit_orders" }, { name: "Spring Awakening" });
    setCurrent(current(["needs_attention", [game]]));
    renderMyGames();

    const section = screen.getByRole("heading", { name: "Needs attention" })
      .parentElement as HTMLElement;
    expect(within(section).getByText("Spring Awakening")).toBeInTheDocument();
  });

  it("shows the all caught up line when there is no needs attention section", () => {
    setCurrent(current(["active", [makeGame({ kind: "resolving" })]]));
    renderMyGames();

    expect(screen.getByText("You're all caught up")).toBeInTheDocument();
  });

  it("does not show the all caught up line when there is a needs attention section", () => {
    setCurrent(current(["needs_attention", [makeGame({ kind: "submit_orders" })]]));
    renderMyGames();

    expect(screen.queryByText("You're all caught up")).not.toBeInTheDocument();
  });
});

describe("MyGames state badges", () => {
  it.each([
    [{ kind: "confirm_seat", deadline: inHours(5) }, "Confirm seat · 5 hours left"],
    [{ kind: "submit_orders", deadline: inHours(30) }, "Submit orders · 1 day left"],
    [{ kind: "submit_orders" }, "Submit orders"],
    [{ kind: "vote_on_draw", deadline: inHours(0.5) }, "Vote on draw · 30 min left"],
    [{ kind: "vote_on_draw" }, "Vote on draw"],
    [{ kind: "seat_confirmed", deadline: inHours(1) }, "Seat confirmed · 1 hour left"],
    [{ kind: "seat_confirmed" }, "Seat confirmed"],
    [{ kind: "orders_unconfirmed" }, "Orders in · confirm to resolve early"],
    [{ kind: "orders_confirmed", deadline: inHours(49) }, "Confirmed · Resolves in 2 days"],
    [{ kind: "orders_confirmed" }, "Confirmed"],
    [{ kind: "resolving", deadline: inHours(3) }, "Resolves in 3 hours"],
    [{ kind: "mustering", deadline: inHours(2) }, "Mustering · 2 hours left"],
    [{ kind: "mustering" }, "Mustering"],
    [{ kind: "paused" }, "Paused"],
    [{ kind: "finished", result: "solo_victory" }, "Solo victory"],
    [{ kind: "finished", result: "won_by", winner: "France" }, "Won by France"],
    [{ kind: "finished", result: "draw" }, "Draw"],
    [{ kind: "finished", result: "abandoned" }, "Abandoned"],
    [
      { kind: "finished", result: "ongoing", departure: "eliminated" },
      "Eliminated · game ongoing",
    ],
    [
      { kind: "finished", result: "ongoing", departure: "civil_disorder" },
      "Civil disorder · game ongoing",
    ],
    [{ kind: "finished", result: "draw", departure: "withdrawn" }, "Withdrew · Draw"],
    [
      { kind: "finished", result: "won_by", winner: "Turkey", departure: "removed" },
      "Removed · Won by Turkey",
    ],
  ] as [Partial<MyGameState> & Pick<MyGameState, "kind">, string][])(
    "renders %o as %s",
    (state, label) => {
      renderCurrentGame(makeGame(state));

      expect(screen.getByText(label)).toBeInTheDocument();
    }
  );

  it("renders the player count for games waiting for players", () => {
    renderCurrentGame(
      makeGame(
        { kind: "waiting_for_players" },
        { status: "pending", nation: null, seats: { filled: 3, total: 7 } }
      )
    );

    expect(screen.getByText("3/7 players")).toBeInTheDocument();
  });

  it("renders no state badge for resolving games without a deadline", () => {
    renderCurrentGame(makeGame({ kind: "resolving" }));

    expect(screen.queryByText(/Resolves in/)).not.toBeInTheDocument();
  });

  it.each([
    ["confirm_seat", "Confirm seat"],
    ["submit_orders", "Submit orders"],
    ["vote_on_draw", "Vote on draw"],
  ] as const)("highlights %s in amber", (kind, label) => {
    renderCurrentGame(makeGame({ kind }));

    expect(screen.getByText(label).closest("[data-slot=badge]")).toHaveClass(
      "bg-amber-50"
    );
  });

  it.each([
    [{ kind: "seat_confirmed" }, "Seat confirmed"],
    [{ kind: "orders_unconfirmed" }, "Orders in · confirm to resolve early"],
    [{ kind: "orders_confirmed" }, "Confirmed"],
    [{ kind: "paused" }, "Paused"],
    [{ kind: "finished", result: "draw" }, "Draw"],
  ] as [Pick<MyGameState, "kind" | "result">, string][])(
    "does not highlight %o",
    (state, label) => {
      renderCurrentGame(makeGame(state));

      expect(screen.getByText(label).closest("[data-slot=badge]")).not.toHaveClass(
        "bg-amber-50"
      );
    }
  );

  it("outlines confirmed orders in green", () => {
    renderCurrentGame(makeGame({ kind: "orders_confirmed" }));

    expect(screen.getByText("Confirmed").closest("[data-slot=badge]")).toHaveClass(
      "border-green-600"
    );
  });

  it.each([
    ["submit_orders", "Submit orders"],
    ["orders_unconfirmed", "Orders in · confirm to resolve early"],
  ] as const)("does not outline %s in green", (kind, label) => {
    renderCurrentGame(makeGame({ kind }));

    expect(screen.getByText(label).closest("[data-slot=badge]")).not.toHaveClass(
      "border-green-600"
    );
  });
});

describe("MyGames card badges", () => {
  it("shows the nation badge for games with a seat", () => {
    renderCurrentGame(makeGame({ kind: "resolving" }, { nation: "England" }));

    expect(screen.getByText("England")).toBeInTheDocument();
  });

  it("shows the sandbox badge and no state badge for sandbox games", () => {
    renderCurrentGame(
      makeGame({ kind: "sandbox" }, { sandbox: true, nation: null, name: "Practice" })
    );

    const card = screen.getByRole("link", { name: /Practice/ });
    expect(within(card).getByText("Sandbox")).toBeInTheDocument();
    expect(card.querySelectorAll("[data-slot=badge]")).toHaveLength(1);
  });

  it("shows no nation badge for pending and mustering games", () => {
    setCurrent(
      current(
        [
          "mustering",
          [
            makeGame(
              { kind: "seat_confirmed" },
              { status: "mustering", nation: null, seats: { filled: 4, total: 7 } }
            ),
          ],
        ],
        [
          "pending",
          [
            makeGame(
              { kind: "waiting_for_players" },
              { status: "pending", nation: null, seats: { filled: 2, total: 7 } }
            ),
          ],
        ]
      )
    );
    renderMyGames();

    expect(screen.queryByText("England")).not.toBeInTheDocument();
    expect(screen.getByText("4/7 seats confirmed")).toBeInTheDocument();
    expect(screen.getByText("Waiting for players")).toBeInTheDocument();
  });

  it("shows the unread count when above zero", () => {
    renderCurrentGame(makeGame({ kind: "resolving" }, { unreadCount: 4 }));

    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("links the card to the game", () => {
    renderCurrentGame(
      makeGame({ kind: "resolving" }, { id: "abc", name: "Linked", currentPhaseId: 7 })
    );

    expect(screen.getByRole("link", { name: /Linked/ })).toHaveAttribute(
      "href",
      "/game/abc/phase/7/orders"
    );
  });
});

describe("MyGames view selector", () => {
  it("sets the finished view in the URL and renders the finished list", async () => {
    vi.useRealTimers();
    const user = userEvent.setup();
    mockGamesMineFinishedList.mockResolvedValue(
      finished([makeGame({ kind: "finished", result: "draw" }, { name: "Stalemate" })])
    );
    renderMyGames();

    await user.click(screen.getByRole("button", { name: /Current selected/ }));
    await user.click(screen.getByRole("button", { name: "Finished" }));

    expect(screen.getByTestId("location")).toHaveTextContent("?view=finished");
    expect(await screen.findByText("Stalemate")).toBeInTheDocument();
  });

  it("opens the finished view when loaded with the view parameter", async () => {
    mockGamesMineFinishedList.mockResolvedValue(
      finished([makeGame({ kind: "finished", result: "abandoned" }, { name: "Collapse" })])
    );
    renderMyGames("/?view=finished");

    expect(await screen.findByText("Collapse")).toBeInTheDocument();
    expect(mockGamesMineFinishedList).toHaveBeenCalledWith({ page: 1 });
    expect(mockUseGamesMineCurrentRetrieveSuspense).not.toHaveBeenCalled();
  });
});

describe("MyGames empty states", () => {
  it("shows the empty Current state with actions and a link to Finished", () => {
    renderMyGames();

    expect(screen.getByText("No current games")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Find games" })).toHaveAttribute(
      "href",
      "/find-games"
    );
    expect(screen.getByRole("link", { name: "Create a game" })).toHaveAttribute(
      "href",
      "/create-game"
    );
    expect(screen.getByRole("link", { name: "Show finished games" })).toHaveAttribute(
      "href",
      "/?view=finished"
    );
  });

  it("shows the empty Finished state", async () => {
    renderMyGames("/?view=finished");

    expect(await screen.findByText("No finished games yet")).toBeInTheDocument();
    expect(
      screen.getByText("Games you finish, leave or are eliminated from will appear here.")
    ).toBeInTheDocument();
  });
});
