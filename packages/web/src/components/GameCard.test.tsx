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
} from "@/mocks";

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
  variant: { name: "Classical Diplomacy", id: "Classical" },
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
      await userEvent.click(screen.getByRole("button", { name: game.name }));
      expect(mockNavigate).toHaveBeenCalledWith(
        `/game/${game.id}/phase/${game.currentPhaseId}`
      );
    });

    it("navigates active games on desktop to the orders sub-route", async () => {
      mockUseIsMobile.mockReturnValue(false);
      const game = mockActiveGames[0];
      renderGameCard({ game, ...defaultProps });
      await userEvent.click(screen.getByRole("button", { name: game.name }));
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

  describe("unread count badge", () => {
    it("does not show badge when totalUnreadMessageCount is 0", () => {
      renderGameCard({
        game: { ...mockGames[0], totalUnreadMessageCount: 0 },
        ...defaultProps,
      });
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    it("shows count badge when totalUnreadMessageCount is positive", () => {
      renderGameCard({
        game: { ...mockGames[0], totalUnreadMessageCount: 5 },
        ...defaultProps,
      });
      expect(screen.getByText("5")).toBeInTheDocument();
    });

    it("caps badge at 99+ when totalUnreadMessageCount exceeds 99", () => {
      renderGameCard({
        game: { ...mockGames[0], totalUnreadMessageCount: 150 },
        ...defaultProps,
      });
      expect(screen.getByText("99+")).toBeInTheDocument();
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
  });
});
