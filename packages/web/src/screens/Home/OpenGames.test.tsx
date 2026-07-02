import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OpenGames } from "./OpenGames";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";

const mockFetchNextPage = vi.fn();
const mockSentinelRef = { current: null };

const defaultGamesListResult = {
  data: { pages: [{ results: [] }] },
  fetchNextPage: mockFetchNextPage,
  hasNextPage: false,
  isFetchingNextPage: false,
} as unknown as ReturnType<typeof useGamesListInfinite>;

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal<
    typeof import("@/api/generated/endpoints")
  >();
  return {
    ...actual,
    useVariantsListSuspense: () => ({
      data: [{ id: "classical", name: "Classical", templatePhase: {} }],
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

vi.mock("@/components/MapView", () => ({
  MapView: () => <div data-testid="map-view" />,
}));

const mockUseGamesListInfinite = vi.mocked(useGamesListInfinite);

const buildGame = (id: string, variantId: string, memberCount = 0) => ({
  id,
  variantId,
  members: Array.from({ length: memberCount }, (_, i) => ({ id: i + 1 })),
  phases: [1],
});

const renderOpenGames = () =>
  render(
    <MemoryRouter>
      <OpenGames />
    </MemoryRouter>
  );

describe("OpenGames", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGamesListInfinite.mockReturnValue(defaultGamesListResult);
  });

  it("queries pending games ordered by slots remaining", () => {
    renderOpenGames();

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith({
      status: "pending",
      ordering: "slots_remaining",
    });
  });

  it("does not use the auth-only can_join / eligible_only filters", () => {
    renderOpenGames();

    const params = mockUseGamesListInfinite.mock.calls[0][0];
    expect(params).not.toHaveProperty("can_join");
    expect(params).not.toHaveProperty("eligible_only");
  });

  it("shows an empty-state notice when there are no open games", () => {
    renderOpenGames();

    expect(screen.getByText("No open games")).toBeInTheDocument();
  });

  it("renders a card per known game", () => {
    mockUseGamesListInfinite.mockReturnValue({
      ...defaultGamesListResult,
      data: {
        pages: [
          { results: [buildGame("g1", "classical"), buildGame("g2", "classical")] },
        ],
      },
    } as unknown as ReturnType<typeof useGamesListInfinite>);

    renderOpenGames();

    expect(screen.getAllByTestId("game-card")).toHaveLength(2);
  });

  it("shows the Fastest Start and More games headers when the top game has at least 3 members", () => {
    mockUseGamesListInfinite.mockReturnValue({
      ...defaultGamesListResult,
      data: {
        pages: [
          {
            results: [
              buildGame("g1", "classical", 4),
              buildGame("g2", "classical", 2),
              buildGame("g3", "classical", 1),
            ],
          },
        ],
      },
    } as unknown as ReturnType<typeof useGamesListInfinite>);

    renderOpenGames();

    expect(screen.getByText(/fastest start/i)).toBeInTheDocument();
    expect(screen.getByText(/more games/i)).toBeInTheDocument();
    expect(screen.getAllByTestId("game-card")).toHaveLength(3);
  });

  it("omits the More games header when only the Fastest Start game is present", () => {
    mockUseGamesListInfinite.mockReturnValue({
      ...defaultGamesListResult,
      data: {
        pages: [{ results: [buildGame("g1", "classical", 4)] }],
      },
    } as unknown as ReturnType<typeof useGamesListInfinite>);

    renderOpenGames();

    expect(screen.getByText(/fastest start/i)).toBeInTheDocument();
    expect(screen.queryByText(/more games/i)).not.toBeInTheDocument();
    expect(screen.getAllByTestId("game-card")).toHaveLength(1);
  });

  it("renders a flat list when the top game has fewer than 3 members", () => {
    mockUseGamesListInfinite.mockReturnValue({
      ...defaultGamesListResult,
      data: {
        pages: [
          {
            results: [buildGame("g1", "classical", 2), buildGame("g2", "classical", 1)],
          },
        ],
      },
    } as unknown as ReturnType<typeof useGamesListInfinite>);

    renderOpenGames();

    expect(screen.queryByText(/fastest start/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/more games/i)).not.toBeInTheDocument();
    expect(screen.getAllByTestId("game-card")).toHaveLength(2);
  });

  it("omits games whose variant is not loaded", () => {
    mockUseGamesListInfinite.mockReturnValue({
      ...defaultGamesListResult,
      data: {
        pages: [
          {
            results: [
              buildGame("g1", "classical"),
              buildGame("g2", "unknown-variant"),
            ],
          },
        ],
      },
    } as unknown as ReturnType<typeof useGamesListInfinite>);

    renderOpenGames();

    expect(screen.getAllByTestId("game-card")).toHaveLength(1);
  });
});
