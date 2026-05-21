import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MyGames } from "./MyGames";
import { mockActiveGames, mockPhaseMovement, mockVariants } from "@/mocks";

const mockUseGamesListInfinite = vi.fn();
const mockUseGamePhaseRetrieve = vi.fn();
const mockUseVariantsListSuspense = vi.fn();

vi.mock("@/hooks/useGamesListInfinite", () => ({
  useGamesListInfinite: (...args: unknown[]) => mockUseGamesListInfinite(...args),
}));

vi.mock("@/api/generated/endpoints", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useVariantsListSuspense: () => mockUseVariantsListSuspense(),
    useUserRetrieveSuspense: () => ({
      data: { id: 1, email: "test@example.com", name: "Test", picture: null },
    }),
    useGamePhaseRetrieve: (...args: unknown[]) => mockUseGamePhaseRetrieve(...args),
    useGameJoinCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  };
});

vi.mock("@/hooks/useInfiniteScroll", () => ({
  useInfiniteScroll: () => ({ current: null }),
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

const renderMyGames = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <MyGames />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

beforeEach(() => {
  mockUseGamesListInfinite.mockReset();
  mockUseGamesListInfinite.mockReturnValue({
    data: { pages: [{ results: [], next: null }] },
    fetchNextPage: vi.fn(),
    hasNextPage: false,
    isFetchingNextPage: false,
  });
  mockUseGamePhaseRetrieve.mockReset();
  mockUseGamePhaseRetrieve.mockReturnValue({ data: mockPhaseMovement });
  mockUseVariantsListSuspense.mockReset();
  mockUseVariantsListSuspense.mockReturnValue({ data: [] });
});

describe("MyGames empty states", () => {
  it("shows welcoming message with action buttons on the active tab", async () => {
    renderMyGames();
    expect(
      await screen.findByText(/create a new game/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create a game/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /find a game/i })).toBeInTheDocument();
  });

  it("shows welcoming message with action buttons on the staging tab", async () => {
    const user = userEvent.setup();
    renderMyGames();
    const stagingTab = await screen.findByRole("tab", { name: /staging/i });
    await user.click(stagingTab);
    expect(
      await screen.findByText(/waiting for more players/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create a game/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /find a game/i })).toBeInTheDocument();
  });

  it("shows welcoming message with create button on the finished tab", async () => {
    const user = userEvent.setup();
    renderMyGames();
    const finishedTab = await screen.findByRole("tab", { name: /finished/i });
    await user.click(finishedTab);
    expect(
      await screen.findByText(/completed games will appear here/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create a game/i })).toBeInTheDocument();
  });

  it("action links point to the correct routes", async () => {
    renderMyGames();
    const createLink = await screen.findByRole("link", { name: /create a game/i });
    const findLink = screen.getByRole("link", { name: /find a game/i });
    expect(createLink).toHaveAttribute("href", "/create-game");
    expect(findLink).toHaveAttribute("href", "/find-games");
  });

  it("active tab message mentions sandbox as an option", async () => {
    renderMyGames();
    expect(
      await screen.findByText(/sandbox/i)
    ).toBeInTheDocument();
  });
});

describe("MyGames phase fetching", () => {
  it("passes currentPhaseId to GameCard, not phases[0]", async () => {
    const game = mockActiveGames[0]; // phases: [1,2,3,4,5], currentPhaseId: 5
    mockUseGamesListInfinite.mockReturnValue({
      data: { pages: [{ results: [game], next: null }] },
      fetchNextPage: vi.fn(),
      hasNextPage: false,
      isFetchingNextPage: false,
    });
    mockUseVariantsListSuspense.mockReturnValue({ data: mockVariants });

    renderMyGames();
    await screen.findByText(game.name);

    expect(mockUseGamePhaseRetrieve).toHaveBeenCalledWith(game.id, game.currentPhaseId);
    expect(mockUseGamePhaseRetrieve).not.toHaveBeenCalledWith(game.id, game.phases[0]);
  });
});
