import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameCard } from "./GameCard";
import {
  mockGames,
  mockSandboxGames,
  mockPhaseMovement,
  mockPendingGames,
  mockActiveGames,
} from "@/mocks/legacy";

const mockNavigate = vi.fn();
const mockUseIsMobile = vi.fn();
const mockUseGamePhaseRetrieve = vi.fn();

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
    useGamePhaseRetrieve: (...args: unknown[]) => mockUseGamePhaseRetrieve(...args),
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
  variant: { name: "Classical Diplomacy", id: "Classical", nations: [] },
  phaseId: 1,
  map: <div data-testid="map" />,
};

describe("GameCard", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockUseIsMobile.mockReset();
    mockUseIsMobile.mockReturnValue(false);
    mockUseGamePhaseRetrieve.mockReset();
    mockUseGamePhaseRetrieve.mockReturnValue({ data: mockPhaseMovement });
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

    it("navigates pending games to game-info on mobile", async () => {
      mockUseIsMobile.mockReturnValue(true);
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
      await userEvent.click(screen.getByRole("button", { name: (accessibleName: string) => accessibleName.includes(game.name) }));
      expect(mockNavigate).toHaveBeenCalledWith(
        `/game/${game.id}/phase/${game.currentPhaseId}`
      );
    });

    it("navigates active games on desktop to the orders sub-route", async () => {
      mockUseIsMobile.mockReturnValue(false);
      const game = mockActiveGames[0];
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(screen.getByRole("button", { name: (accessibleName: string) => accessibleName.includes(game.name) }));
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

    it("shows frequency label for fixed_time mode (daily)", () => {
      renderGameCard({
        game: { ...baseGame, deadlineMode: "fixed_time", movementFrequency: "daily", movementPhaseDuration: "24 hours" },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • Daily/)).toBeInTheDocument();
    });

    it("shows frequency label for fixed_time mode (weekly)", () => {
      renderGameCard({
        game: { ...baseGame, deadlineMode: "fixed_time", movementFrequency: "weekly", movementPhaseDuration: "24 hours" },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • Weekly/)).toBeInTheDocument();
    });

    it("shows 'Fixed time' for fixed_time mode with unknown frequency", () => {
      renderGameCard({
        game: { ...baseGame, deadlineMode: "fixed_time", movementFrequency: null, movementPhaseDuration: "24 hours" },
        ...defaultProps,
      });
      expect(screen.getByText(/Classical Diplomacy • Fixed time/)).toBeInTheDocument();
    });
  });

  describe("gunboat icon", () => {
    it("shows gunboat icon when pressType is no_press", () => {
      renderGameCard({
        game: { ...mockGames[0], pressType: "no_press" },
        ...defaultProps,
      });
      expect(screen.getByLabelText("Gunboat")).toBeInTheDocument();
    });

    it("does not show gunboat icon when pressType is full_press", () => {
      renderGameCard({
        game: { ...mockGames[0], pressType: "full_press" },
        ...defaultProps,
      });
      expect(screen.queryByLabelText("Gunboat")).not.toBeInTheDocument();
    });
  });

  describe("unread message indicator", () => {
    it("shows the total unread count when greater than zero", () => {
      renderGameCard({
        game: { ...mockGames[0], totalUnreadMessageCount: 4 },
        ...defaultProps,
      });
      expect(screen.getByText("4")).toBeInTheDocument();
    });

    it("does not show an indicator when there are no unread messages", () => {
      renderGameCard({
        game: { ...mockGames[0], totalUnreadMessageCount: 0 },
        ...defaultProps,
      });
      expect(screen.queryByText("0")).not.toBeInTheDocument();
    });

    it("does not show an indicator for sandbox games", () => {
      renderGameCard({
        game: { ...mockSandboxGames[0], totalUnreadMessageCount: 0 },
        ...defaultProps,
      });
      expect(screen.queryByText("0")).not.toBeInTheDocument();
    });
  });

  describe("order and member status badges", () => {
    it("shows 'Required' badge when orderStatus is orders_required", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "orders_required", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Required")).toBeInTheDocument();
    });

    it("shows 'Submitted' badge when orderStatus is orders_submitted", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "orders_submitted", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Submitted")).toBeInTheDocument();
    });

    it("shows 'Not confirmed' badge when orderStatus is orders_not_confirmed", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "orders_not_confirmed", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Not confirmed")).toBeInTheDocument();
    });

    it("shows 'Not required' badge when orderStatus is no_orders_required", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: "no_orders_required", memberStatus: [] }, ...defaultProps });
      expect(screen.getByText("Not required")).toBeInTheDocument();
    });

    it("shows no order status badge when orderStatus is null", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: [] }, ...defaultProps });
      expect(screen.queryByText("Required")).not.toBeInTheDocument();
      expect(screen.queryByText("Submitted")).not.toBeInTheDocument();
      expect(screen.queryByText("Not confirmed")).not.toBeInTheDocument();
      expect(screen.queryByText("Not required")).not.toBeInTheDocument();
    });

    it("shows 'NMR' badge when memberStatus includes nmr", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: ["nmr"] }, ...defaultProps });
      expect(screen.getByText("NMR")).toBeInTheDocument();
    });

    it("shows 'CD' badge when memberStatus includes civil_disorder", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: ["civil_disorder"] }, ...defaultProps });
      expect(screen.getByText("CD")).toBeInTheDocument();
    });

    it("shows no member status badges when memberStatus is empty", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: [] }, ...defaultProps });
      expect(screen.queryByText("NMR")).not.toBeInTheDocument();
      expect(screen.queryByText("CD")).not.toBeInTheDocument();
    });

    it("renders without crashing when memberStatus is null", () => {
      renderGameCard({ game: { ...mockGames[0], orderStatus: null, memberStatus: null }, ...defaultProps });
      expect(screen.queryByText("NMR")).not.toBeInTheDocument();
      expect(screen.queryByText("CD")).not.toBeInTheDocument();
    });
  });

  describe("sandbox visual treatment", () => {
    it("displays a Sandbox badge when game.sandbox is true", () => {
      renderGameCard({
        game: mockSandboxGames[0],
        ...defaultProps,
      });
      expect(screen.getByText("Sandbox")).toBeInTheDocument();
    });

    it("does not display a Sandbox badge when game.sandbox is false", () => {
      renderGameCard({
        game: mockGames[0],
        ...defaultProps,
      });
      expect(screen.queryByText("Sandbox")).not.toBeInTheDocument();
    });

    it("hides avatar group for sandbox games", () => {
      renderGameCard({
        game: mockSandboxGames[0],
        ...defaultProps,
      });
      for (const member of mockSandboxGames[0].members.slice(0, 7)) {
        expect(
          screen.queryByText(member.name?.[0]?.toUpperCase() ?? "?")
        ).not.toBeInTheDocument();
      }
    });

    it("shows avatar group for non-sandbox games", () => {
      renderGameCard({
        game: mockGames[0],
        ...defaultProps,
      });
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
