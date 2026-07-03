import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameCard } from "./GameCard";
import {
  mockGames,
  mockMembers,
  mockNations,
  mockSandboxGames,
  mockPendingGames,
  mockActiveGames,
  mockCompletedGames,
} from "@/mocks/legacy";

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
    useGameJoinCreate: () => ({
      mutateAsync: vi.fn(),
      isPending: false,
    }),
    getGamesListQueryKey: () => ["games"],
  };
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
  variant: { name: "Classical Diplomacy", id: "Classical", nations: mockNations },
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
      renderGameCard({ game: mockPendingGames[0], ...defaultProps });
      await userEvent.click(
        screen.getByRole("button", { name: mockPendingGames[0].name })
      );
      expect(mockNavigate).toHaveBeenCalledWith(
        `/game-info/${mockPendingGames[0].id}`
      );
    });

    it("navigates active games on mobile to the phase index", async () => {
      mockUseIsMobile.mockReturnValue(true);
      const game = mockActiveGames[0];
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(
        screen.getByRole("button", {
          name: (accessibleName: string) => accessibleName.includes(game.name),
        })
      );
      expect(mockNavigate).toHaveBeenCalledWith(
        `/game/${game.id}/phase/${game.currentPhaseId}`
      );
    });

    it("navigates active games on desktop to the orders sub-route", async () => {
      mockUseIsMobile.mockReturnValue(false);
      const game = mockActiveGames[0];
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(
        screen.getByRole("button", {
          name: (accessibleName: string) => accessibleName.includes(game.name),
        })
      );
      expect(mockNavigate).toHaveBeenCalledWith(
        `/game/${game.id}/phase/${game.currentPhaseId}/orders`
      );
    });
  });

  describe("cadence display", () => {
    const baseGame = mockGames[0];

    it("shows movementPhaseDuration for duration mode", () => {
      renderGameCard({
        game: { ...baseGame, deadlineMode: "duration", movementPhaseDuration: "12 hours" },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • 12 hours/)).toBeInTheDocument();
    });

    it("shows 'Resolve when ready' for duration mode with no duration", () => {
      renderGameCard({
        game: { ...baseGame, deadlineMode: "duration", movementPhaseDuration: null },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • Resolve when ready/)).toBeInTheDocument();
    });

    it("shows frequency label for fixed_time mode (hourly)", () => {
      renderGameCard({
        game: { ...baseGame, deadlineMode: "fixed_time", movementFrequency: "hourly", movementPhaseDuration: "24 hours" },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • Hourly/)).toBeInTheDocument();
    });

    it("shows 'Fixed time' for fixed_time mode with unknown frequency", () => {
      renderGameCard({
        game: { ...baseGame, deadlineMode: "fixed_time", movementFrequency: null, movementPhaseDuration: "24 hours" },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • Fixed time/)).toBeInTheDocument();
    });
  });

  describe("active mode", () => {
    const activePhase = {
      id: 5,
      ordinal: 3,
      season: "Fall",
      year: 1901,
      name: "Fall 1901 Movement",
      type: "Movement",
      status: "active",
      scheduledResolution: "2099-01-18T12:00:00Z",
      remainingTime: 13200,
      units: [],
      supplyCenters: [],
    };
    const activeGame = {
      ...mockActiveGames[0],
      currentPhase: activePhase,
      isPaused: false,
    };

    it("shows 'Orders due in' when orders are required", () => {
      renderGameCard({
        game: { ...activeGame, orderStatus: "orders_required" },
        mode: "active",
        ...defaultProps,
      });
      expect(screen.getByText(/Orders due in 3h 40m/)).toBeInTheDocument();
    });

    it("shows 'Orders not confirmed' when orders are not confirmed", () => {
      renderGameCard({
        game: { ...activeGame, orderStatus: "orders_not_confirmed" },
        mode: "active",
        ...defaultProps,
      });
      expect(
        screen.getByText(/Orders not confirmed\. Phase resolves in 3h 40m/)
      ).toBeInTheDocument();
    });

    it("shows 'Orders confirmed' when orders are submitted", () => {
      renderGameCard({
        game: { ...activeGame, orderStatus: "orders_submitted" },
        mode: "active",
        ...defaultProps,
      });
      expect(
        screen.getByText(/Orders confirmed\. Phase resolves in 3h 40m/)
      ).toBeInTheDocument();
    });

    it("shows 'No orders required' when no orders are required", () => {
      renderGameCard({
        game: { ...activeGame, orderStatus: "no_orders_required" },
        mode: "active",
        ...defaultProps,
      });
      expect(
        screen.getByText(/No orders required\. Phase resolves in 3h 40m/)
      ).toBeInTheDocument();
    });

    it("renders the nation as a floating chip on the map", () => {
      renderGameCard({
        game: { ...activeGame, orderStatus: "orders_required" },
        mode: "active",
        ...defaultProps,
      });
      expect(screen.getByText("Turkey")).toBeInTheDocument();
    });

    it("shows a paused treatment instead of a countdown when paused", () => {
      renderGameCard({
        game: { ...activeGame, orderStatus: "orders_required", isPaused: true },
        mode: "active",
        ...defaultProps,
      });
      expect(
        screen.getByText(/Paused — resumes when unpaused/)
      ).toBeInTheDocument();
      expect(screen.queryByText(/Orders due in/)).not.toBeInTheDocument();
    });
  });

  describe("gunboat badge", () => {
    it("shows gunboat badge when pressType is no_press", () => {
      renderGameCard({
        game: { ...mockGames[0], pressType: "no_press" },
        ...defaultProps,
      });
      expect(screen.getByLabelText("Gunboat")).toBeInTheDocument();
    });

    it("does not show gunboat badge when pressType is full_press", () => {
      renderGameCard({
        game: { ...mockGames[0], pressType: "full_press" },
        ...defaultProps,
      });
      expect(screen.queryByLabelText("Gunboat")).not.toBeInTheDocument();
    });
  });

  describe("unread message indicator", () => {
    it("shows the unread count for active games", () => {
      renderGameCard({
        game: { ...mockGames[0], totalUnreadMessageCount: 4 },
        ...defaultProps,
      });
      expect(screen.getByText(/4 new/)).toBeInTheDocument();
    });

    it("shows the unread count for finished games", () => {
      renderGameCard({
        game: { ...mockCompletedGames[0], totalUnreadMessageCount: 2 },
        ...defaultProps,
      });
      expect(screen.getByText(/2 new/)).toBeInTheDocument();
    });

    it("does not show an indicator when there are no unread messages", () => {
      renderGameCard({
        game: { ...mockGames[0], totalUnreadMessageCount: 0 },
        ...defaultProps,
      });
      expect(screen.queryByText(/new/)).not.toBeInTheDocument();
    });

    it("does not show an indicator for sandbox games", () => {
      renderGameCard({
        game: { ...mockSandboxGames[0], totalUnreadMessageCount: 3 },
        ...defaultProps,
      });
      expect(screen.queryByText(/new/)).not.toBeInTheDocument();
    });
  });

  describe("order and member status badges", () => {
    it("shows 'Orders required' badge when orderStatus is orders_required", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "orders_required", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Orders required")).toBeInTheDocument();
    });

    it("shows 'Orders submitted' badge when orderStatus is orders_submitted", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "orders_submitted", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Orders submitted")).toBeInTheDocument();
    });

    it("shows 'Orders not confirmed' badge when orderStatus is orders_not_confirmed", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "orders_not_confirmed", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Orders not confirmed")).toBeInTheDocument();
    });

    it("shows 'Orders not required' badge when orderStatus is no_orders_required", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "no_orders_required", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Orders not required")).toBeInTheDocument();
    });

    it("shows no order status badge when orderStatus is null", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: [] }, ...defaultProps });
      expect(screen.queryByText("Orders required")).not.toBeInTheDocument();
      expect(screen.queryByText("Orders submitted")).not.toBeInTheDocument();
    });

    it("shows 'NMR' badge for active games when memberStatus includes nmr", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: ["nmr"] }, ...defaultProps });
      expect(screen.getByText("NMR")).toBeInTheDocument();
    });

    it("shows 'CD' badge when memberStatus includes civil_disorder", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: ["civil_disorder"] }, ...defaultProps });
      expect(screen.getByText("CD")).toBeInTheDocument();
    });

    it("renders without crashing when memberStatus is null", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: null }, ...defaultProps });
      expect(screen.queryByText("NMR")).not.toBeInTheDocument();
      expect(screen.queryByText("CD")).not.toBeInTheDocument();
    });
  });

  describe("eliminated player", () => {
    const eliminatedMembers = mockMembers.map(m =>
      m.isCurrentUser ? { ...m, eliminated: true } : m
    );

    it("shows 'Eliminated' badge when the current user is eliminated in an active game", () => {
      renderGameCard({
        game: { ...mockGames[0], members: eliminatedMembers },
        ...defaultProps,
      });
      expect(screen.getByText("Eliminated")).toBeInTheDocument();
    });

    it("does not show 'Eliminated' badge when the current user is not eliminated", () => {
      renderGameCard({
        game: { ...mockGames[0], members: mockMembers },
        ...defaultProps,
      });
      expect(screen.queryByText("Eliminated")).not.toBeInTheDocument();
    });

    it("does not show 'Eliminated' badge for sandbox games", () => {
      renderGameCard({
        game: { ...mockSandboxGames[0], members: eliminatedMembers },
        ...defaultProps,
      });
      expect(screen.queryByText("Eliminated")).not.toBeInTheDocument();
    });

    it("does not show 'Eliminated' badge when no member is the current user", () => {
      renderGameCard({
        game: {
          ...mockGames[0],
          members: mockMembers.map(m => ({ ...m, isCurrentUser: false, eliminated: true })),
        },
        ...defaultProps,
      });
      expect(screen.queryByText("Eliminated")).not.toBeInTheDocument();
    });
  });

  describe("finished games", () => {
    it("shows a solo victory result badge", () => {
      renderGameCard({ game: mockCompletedGames[0], ...defaultProps });
      expect(screen.getByText(/won/)).toBeInTheDocument();
    });

    it("shows a draw result badge with player count", () => {
      renderGameCard({ game: mockCompletedGames[1], ...defaultProps });
      expect(screen.getByText(/Draw · 3 players/)).toBeInTheDocument();
    });

    it("shows an abandoned badge for abandoned games", () => {
      renderGameCard({
        game: { ...mockCompletedGames[0], status: "abandoned", victory: null },
        ...defaultProps,
      });
      expect(screen.getByText("Abandoned")).toBeInTheDocument();
    });

    it("keeps the CD badge but suppresses NMR for finished games", () => {
      renderGameCard({
        game: { ...mockCompletedGames[0], memberStatus: ["nmr", "civil_disorder"] },
        ...defaultProps,
      });
      expect(screen.getByText("CD")).toBeInTheDocument();
      expect(screen.queryByText("NMR")).not.toBeInTheDocument();
    });
  });

  describe("pending games", () => {
    it("shows the joined count out of total slots", () => {
      renderGameCard({ game: mockPendingGames[0], ...defaultProps });
      expect(
        screen.getByText(`${mockPendingGames[0].members.length}/${mockNations.length} joined`)
      ).toBeInTheDocument();
    });

    it("does not show order status or result badges", () => {
      renderGameCard({ game: mockPendingGames[0], ...defaultProps });
      expect(screen.queryByText(/joined/)).toBeInTheDocument();
      expect(screen.queryByText("Orders required")).not.toBeInTheDocument();
      expect(screen.queryByText(/won/)).not.toBeInTheDocument();
    });
  });

  describe("non-playing game master", () => {
    it("renders a separate game master avatar without counting it toward joined", () => {
      renderGameCard({
        game: {
          ...mockPendingGames[0],
          gameMaster: { userId: 999, name: "Zara", picture: null },
        },
        ...defaultProps,
      });
      expect(screen.getByText("Z")).toBeInTheDocument();
      expect(
        screen.getByText(`${mockPendingGames[0].members.length}/${mockNations.length} joined`)
      ).toBeInTheDocument();
    });
  });

  describe("sandbox visual treatment", () => {
    it("displays a Sandbox badge when game.sandbox is true", () => {
      renderGameCard({ game: mockSandboxGames[0], ...defaultProps });
      expect(screen.getByText("Sandbox")).toBeInTheDocument();
    });

    it("does not display a Sandbox badge when game.sandbox is false", () => {
      renderGameCard({ game: mockGames[0], ...defaultProps });
      expect(screen.queryByText("Sandbox")).not.toBeInTheDocument();
    });

    it("hides avatar group for sandbox games", () => {
      renderGameCard({ game: mockSandboxGames[0], ...defaultProps });
      for (const member of mockSandboxGames[0].members.slice(0, 7)) {
        expect(
          screen.queryByText(member.name?.[0]?.toUpperCase() ?? "?")
        ).not.toBeInTheDocument();
      }
    });

    it("shows avatar group for non-sandbox games", () => {
      renderGameCard({ game: mockGames[0], ...defaultProps });
      expect(screen.getByText("A")).toBeInTheDocument();
    });

    it("shows 'Resolve when ready' for sandbox games regardless of deadline mode", () => {
      renderGameCard({
        game: { ...mockSandboxGames[0], deadlineMode: "fixed_time", movementFrequency: null },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • Resolve when ready/)).toBeInTheDocument();
    });
  });
});
