import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { FindGames } from "./FindGames";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useGamesFastestRetrieveSuspense } from "@/api/generated/endpoints";

const mockFetchNextPage = vi.fn();
const mockSentinelRef = { current: null };

const defaultGamesListResult = {
  data: { pages: [{ results: [] }] },
  fetchNextPage: mockFetchNextPage,
  hasNextPage: false,
  isFetchingNextPage: false,
} as unknown as ReturnType<typeof useGamesListInfinite>;

const defaultFastestResult = {
  data: { game: null },
} as unknown as ReturnType<typeof useGamesFastestRetrieveSuspense>;

const buildGame = (id: string, variantId = "classical") => ({
  id,
  variantId,
  phases: [1],
  members: [],
});

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal<
    typeof import("@/api/generated/endpoints")
  >();
  return {
    ...actual,
    useGamesFastestRetrieveSuspense: vi.fn(),
    useVariantsListSuspense: () => ({
      data: [
        { id: "classical", name: "Classical" },
        { id: "pure", name: "Pure" },
      ],
    }),
  };
});

vi.mock("@/hooks/useGamesListInfinite", () => ({
  useGamesListInfinite: vi.fn(() => defaultGamesListResult),
}));

vi.mock("@/hooks/useInfiniteScroll", () => ({
  useInfiniteScroll: () => mockSentinelRef,
}));

vi.mock("@/components/GameCard", () => ({
  GameCard: ({ game }: { game: { id: string } }) => (
    <div data-testid="game-card" data-game-id={game.id} />
  ),
}));

vi.mock("@/components/UserAvatar", () => ({
  UserAvatar: () => <div data-testid="user-avatar" />,
}));

const mockUseGamesListInfinite = vi.mocked(useGamesListInfinite);
const mockUseGamesFastestRetrieveSuspense = vi.mocked(
  useGamesFastestRetrieveSuspense
);

const mockGamesList = (games: ReturnType<typeof buildGame>[]) =>
  mockUseGamesListInfinite.mockReturnValue({
    ...defaultGamesListResult,
    data: { pages: [{ results: games }] },
  } as unknown as ReturnType<typeof useGamesListInfinite>);

const mockFastestGame = (game: ReturnType<typeof buildGame>) =>
  mockUseGamesFastestRetrieveSuspense.mockReturnValue({
    data: { game },
  } as unknown as ReturnType<typeof useGamesFastestRetrieveSuspense>);

const renderFindGames = (initialEntries = ["/"]) =>
  render(
    <MemoryRouter initialEntries={initialEntries}>
      <FindGames />
    </MemoryRouter>
  );

describe("FindGames", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGamesListInfinite.mockReturnValue(defaultGamesListResult);
    mockUseGamesFastestRetrieveSuspense.mockReturnValue(defaultFastestResult);
  });

  it("shows the filter toggle button in the header", () => {
    renderFindGames();
    expect(
      screen.getByRole("button", { name: /toggle filters/i })
    ).toBeInTheDocument();
  });

  it("hides the filter panel by default", () => {
    renderFindGames();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("shows the filter panel when the toggle button is clicked", async () => {
    renderFindGames();

    await userEvent.click(
      screen.getByRole("button", { name: /toggle filters/i })
    );

    expect(screen.getAllByRole("combobox")).toHaveLength(2);
  });

  it("hides the filter panel when the toggle button is clicked twice", async () => {
    renderFindGames();

    const toggleButton = screen.getByRole("button", {
      name: /toggle filters/i,
    });

    await userEvent.click(toggleButton);
    expect(screen.getAllByRole("combobox")).toHaveLength(2);

    await userEvent.click(toggleButton);
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("passes can_join: true to the games list query", () => {
    renderFindGames();

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.objectContaining({ can_join: true })
    );
  });

  it("passes variant param from URL to the games list query", () => {
    renderFindGames(["/?variant=classical"]);

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.objectContaining({ can_join: true, variant: "classical" })
    );
  });

  it("passes movement_phase_duration param from URL to the games list query", () => {
    renderFindGames(["/?movement_phase_duration=24+hours"]);

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.objectContaining({
        can_join: true,
        movement_phase_duration: "24 hours",
      })
    );
  });

  it("passes ordering=slots_remaining to the games list query", () => {
    renderFindGames();

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.objectContaining({ ordering: "slots_remaining" })
    );
  });

  it("does not filter ineligible games out of the games list query", () => {
    renderFindGames();

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.not.objectContaining({ eligible_only: true })
    );
  });

  it("renders the recommended game in the Fastest Start slot above all games", () => {
    mockGamesList([buildGame("g1"), buildGame("g2"), buildGame("g3")]);
    mockFastestGame(buildGame("g2"));

    renderFindGames();

    expect(
      screen.getByText(/fastest start — join to start playing quickly/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/more games/i)).toBeInTheDocument();
    expect(
      screen.getAllByTestId("game-card").map(card => card.dataset.gameId)
    ).toEqual(["g2", "g1", "g2", "g3"]);
  });

  it("omits the Fastest Start slot when no game is recommended", () => {
    mockGamesList([buildGame("g1"), buildGame("g2")]);

    renderFindGames();

    expect(screen.queryByText(/fastest start/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/more games/i)).not.toBeInTheDocument();
    expect(screen.getAllByTestId("game-card")).toHaveLength(2);
  });

  it("hides the Fastest Start slot when a variant filter is active", () => {
    mockGamesList([buildGame("g1")]);
    mockFastestGame(buildGame("g1"));

    renderFindGames(["/?variant=classical"]);

    expect(screen.queryByText(/fastest start/i)).not.toBeInTheDocument();
    expect(screen.getAllByTestId("game-card")).toHaveLength(1);
  });

  it("hides the Fastest Start slot when a duration filter is active", () => {
    mockGamesList([buildGame("g1")]);
    mockFastestGame(buildGame("g1"));

    renderFindGames(["/?movement_phase_duration=24+hours"]);

    expect(screen.queryByText(/fastest start/i)).not.toBeInTheDocument();
    expect(screen.getAllByTestId("game-card")).toHaveLength(1);
  });

  it("omits the Fastest Start slot when the recommended game's variant is unknown", () => {
    mockGamesList([buildGame("g1")]);
    mockFastestGame(buildGame("g2", "unknown"));

    renderFindGames();

    expect(screen.queryByText(/fastest start/i)).not.toBeInTheDocument();
    expect(screen.getAllByTestId("game-card")).toHaveLength(1);
  });

  it("renders the empty state instead of crashing when pages is not an array", () => {
    mockUseGamesListInfinite.mockReturnValue({
      ...defaultGamesListResult,
      data: { pages: undefined },
    } as unknown as ReturnType<typeof useGamesListInfinite>);

    renderFindGames();

    expect(screen.getByText(/no games found/i)).toBeInTheDocument();
  });

  it("renders the empty state instead of crashing when page.results is not an array", () => {
    mockUseGamesListInfinite.mockReturnValue({
      ...defaultGamesListResult,
      data: { pages: [{ results: undefined }] },
    } as unknown as ReturnType<typeof useGamesListInfinite>);

    renderFindGames();

    expect(screen.getByText(/no games found/i)).toBeInTheDocument();
  });
});
