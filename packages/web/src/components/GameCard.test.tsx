import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameCard } from "./GameCard";
import type { GameList, Member } from "@/api/generated/endpoints";

const mockNavigate = vi.fn();
const mockUseIsMobile = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => mockUseIsMobile(),
}));

vi.mock("@/api/generated/endpoints", async () => {
  const actual = await vi.importActual("@/api/generated/endpoints");
  return {
    ...actual,
    useGamePhaseRetrieve: () => ({ data: null }),
    useGameJoinCreate: () => ({
      mutateAsync: vi.fn(),
      isPending: false,
    }),
    getGamesListQueryKey: () => ["games"],
  };
});

const buildMember = (overrides: Partial<Member> = {}): Member => ({
  id: 1,
  name: "Alice",
  picture: null,
  nation: "Austria",
  isCurrentUser: false,
  eliminated: false,
  kicked: false,
  isGameMaster: false,
  nmrExtensionsRemaining: 0,
  reliabilityTier: "reliable",
  reliabilityGamesFinished: 5,
  reliabilityGamesAbandonedRecent: 0,
  ...overrides,
});

const baseMembers: Member[] = [
  buildMember({ id: 1, name: "Alice", isGameMaster: true }),
  buildMember({ id: 2, name: "Bob", nation: "England" }),
  buildMember({ id: 3, name: "Charlie", nation: "France" }),
];

const buildGame = (overrides: Partial<GameList> = {}): GameList => ({
  id: "game-1",
  name: "Test Game",
  status: "active",
  createdAt: "2026-04-20T10:00:00Z",
  canJoin: false,
  canLeave: true,
  canDelete: false,
  variantId: "Classical",
  phases: [1],
  currentPhaseId: 1,
  private: false,
  anonymous: false,
  movementPhaseDuration: "24 hours",
  retreatPhaseDuration: null,
  nationAssignment: "random",
  members: baseMembers,
  victory: null,
  sandbox: false,
  isPaused: false,
  pausedAt: null,
  nmrExtensionsAllowed: 0,
  deadlineMode: "duration",
  fixedDeadlineTime: null,
  fixedDeadlineTimezone: null,
  movementFrequency: null,
  retreatFrequency: null,
  pressType: "full_press",
  minReliability: "open",
  ...overrides,
});

const renderGameCard = (props: React.ComponentProps<typeof GameCard>) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <GameCard {...props} />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const defaultProps = {
  variant: { name: "Classical Diplomacy", id: "Classical" },
  phaseId: 1,
  map: <div data-testid="map" />,
};

describe("GameCard", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockUseIsMobile.mockReset();
    mockUseIsMobile.mockReturnValue(false);
  });

  describe("click navigation", () => {
    it("navigates pending games to game-info on desktop", async () => {
      mockUseIsMobile.mockReturnValue(false);
      const game = buildGame({ id: "pending-1", name: "Pending Game", status: "pending" });
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(screen.getByRole("button", { name: game.name }));
      expect(mockNavigate).toHaveBeenCalledWith(`/game-info/${game.id}`);
    });

    it("navigates pending games to game-info on mobile", async () => {
      mockUseIsMobile.mockReturnValue(true);
      const game = buildGame({ id: "pending-1", name: "Pending Game", status: "pending" });
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(screen.getByRole("button", { name: game.name }));
      expect(mockNavigate).toHaveBeenCalledWith(`/game-info/${game.id}`);
    });

    it("navigates active games on mobile to the phase index", async () => {
      mockUseIsMobile.mockReturnValue(true);
      const game = buildGame({
        id: "active-1",
        name: "Active Game",
        status: "active",
        currentPhaseId: 42,
      });
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(screen.getByRole("button", { name: game.name }));
      expect(mockNavigate).toHaveBeenCalledWith(
        `/game/${game.id}/phase/${game.currentPhaseId}`
      );
    });

    it("navigates active games on desktop to the orders sub-route", async () => {
      mockUseIsMobile.mockReturnValue(false);
      const game = buildGame({
        id: "active-1",
        name: "Active Game",
        status: "active",
        currentPhaseId: 42,
      });
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(screen.getByRole("button", { name: game.name }));
      expect(mockNavigate).toHaveBeenCalledWith(
        `/game/${game.id}/phase/${game.currentPhaseId}/orders`
      );
    });
  });

  describe("sandbox visual treatment", () => {
    it("displays a Sandbox badge when game.sandbox is true", () => {
      renderGameCard({
        game: buildGame({ sandbox: true }),
        ...defaultProps,
      });
      expect(screen.getByText("Sandbox")).toBeInTheDocument();
    });

    it("does not display a Sandbox badge when game.sandbox is false", () => {
      renderGameCard({
        game: buildGame({ sandbox: false }),
        ...defaultProps,
      });
      expect(screen.queryByText("Sandbox")).not.toBeInTheDocument();
    });

    it("hides avatar group for sandbox games", () => {
      const sandboxGame = buildGame({ sandbox: true });
      renderGameCard({
        game: sandboxGame,
        ...defaultProps,
      });
      for (const member of sandboxGame.members) {
        expect(
          screen.queryByText(member.name?.[0]?.toUpperCase() ?? "?")
        ).not.toBeInTheDocument();
      }
    });

    it("shows avatar group for non-sandbox games", () => {
      renderGameCard({
        game: buildGame({ sandbox: false }),
        ...defaultProps,
      });
      expect(screen.getByText("A")).toBeInTheDocument();
    });
  });
});
