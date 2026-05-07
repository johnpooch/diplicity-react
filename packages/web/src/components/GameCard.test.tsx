import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import { GameCard } from "./GameCard";
import type { GameList, Member } from "@/api/generated/endpoints";

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
