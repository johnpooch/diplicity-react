import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameInfoScreen } from "./GameInfoScreen";
import { mockPendingGames, mockActiveGames } from "@/mocks/legacy";

const mockJoinMutateAsync = vi.fn();
const mockLeaveMutateAsync = vi.fn();
const mockUseGameRetrieveSuspense = vi.fn();

vi.mock("@/api/generated/endpoints", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useGameRetrieveSuspense: (...args: unknown[]) =>
      mockUseGameRetrieveSuspense(...args),
    useGameMemberJoinCreate: () => ({
      mutateAsync: mockJoinMutateAsync,
      isPending: false,
    }),
    useGameLeaveDestroy: () => ({
      mutateAsync: mockLeaveMutateAsync,
      isPending: false,
    }),
    useVariantsListSuspense: () => ({
      data: [
        {
          id: "Classical",
          name: "Classical",
          nations: Array.from({ length: 7 }, (_, index) => ({
            name: `Nation ${index}`,
            nonPlayable: false,
          })),
        },
      ],
    }),
    useUserRetrieveSuspense: () => ({
      data: { canCreateBotGames: true },
    }),
    getGameRetrieveQueryKey: (gameId: string) => ["games", gameId],
  };
});

vi.mock("@/components/AddBotSheet", () => ({
  AddBotSheet: ({ open }: { open: boolean }) =>
    open ? <div data-testid="add-bot-sheet" /> : null,
}));

vi.mock("@/components/GameInfoContent", () => ({
  GameInfoContent: ({
    pendingAction,
  }: {
    pendingAction?: React.ReactNode;
  }) => <div data-testid="game-info-content">{pendingAction}</div>,
}));

vi.mock("@/components/MapView", () => ({
  MapView: () => <div data-testid="map-preview" />,
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

const pendingGameCanJoin = mockPendingGames.find((g) => g.canJoin)!;
const pendingGameCanLeave = mockPendingGames.find((g) => !g.canJoin && g.canLeave)!;
const pendingGameReliabilityRequired = {
  ...mockPendingGames.find((g) => g.canJoin)!,
  id: "game-reliability-test",
  canJoin: false,
  canLeave: false,
  minReliability: "reliable_only" as const,
};
const pendingGameCanManage = {
  ...mockPendingGames.find((g) => !g.canJoin && g.canLeave)!,
  id: "game-manage-test",
  canManage: true,
};

const renderGameInfo = (gameId: string) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  vi.spyOn(queryClient, "invalidateQueries").mockResolvedValue();

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/game/${gameId}/game-info`]}>
        <Routes>
          <Route path="/game/:gameId/game-info" element={<GameInfoScreen />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

  return { queryClient };
};

describe("GameInfoScreen (shell)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockJoinMutateAsync.mockResolvedValue(undefined);
    mockLeaveMutateAsync.mockResolvedValue(undefined);
  });

  describe("header button", () => {
    it("shows no header button for a pending game (Join/Leave live in the body)", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      renderGameInfo(pendingGameCanJoin.id);

      const content = screen.getByTestId("game-info-content");
      const headerButtons = screen
        .queryAllByRole("button", { name: /join game|leave game/i })
        .filter((button) => !content.contains(button));
      expect(headerButtons).toHaveLength(0);
    });

    it("shows a Join icon button for an active game the user can join", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({
        data: { ...mockActiveGames[0], canJoin: true },
      });
      renderGameInfo(mockActiveGames[0].id);

      expect(
        screen.getByRole("button", { name: /join game/i })
      ).toBeInTheDocument();
    });

    it("shows no join/leave button for an active game the user cannot join", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({
        data: { ...mockActiveGames[0], canJoin: false },
      });
      renderGameInfo(mockActiveGames[0].id);

      expect(
        screen.queryByRole("button", { name: /join game/i })
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /leave game/i })
      ).not.toBeInTheDocument();
    });
  });

  describe("pendingAction content", () => {
    it("shows a primary 'Join game' button in the body for a pending game the user can join", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      renderGameInfo(pendingGameCanJoin.id);

      const content = screen.getByTestId("game-info-content");
      expect(
        within(content).getByRole("button", { name: /join game/i })
      ).toBeInTheDocument();
    });

    it("calls the join mutation when the body Join button is clicked", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      renderGameInfo(pendingGameCanJoin.id);

      const content = screen.getByTestId("game-info-content");
      await userEvent.click(
        within(content).getByRole("button", { name: /join game/i })
      );

      expect(mockJoinMutateAsync).toHaveBeenCalledWith({
        gameId: pendingGameCanJoin.id,
      });
    });

    it("shows a 'Leave' button in the body for a pending game the user has joined", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      renderGameInfo(pendingGameCanLeave.id);

      const content = screen.getByTestId("game-info-content");
      expect(
        within(content).getByRole("button", { name: /^leave$/i })
      ).toBeInTheDocument();
    });

    it("calls the leave mutation when the body Leave button is clicked", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      renderGameInfo(pendingGameCanLeave.id);

      const content = screen.getByTestId("game-info-content");
      await userEvent.click(
        within(content).getByRole("button", { name: /^leave$/i })
      );

      expect(mockLeaveMutateAsync).toHaveBeenCalledWith({
        gameId: pendingGameCanLeave.id,
      });
    });

    it("shows a disabled Join button with a reliability message when reliability-gated", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({
        data: pendingGameReliabilityRequired,
      });
      renderGameInfo(pendingGameReliabilityRequired.id);

      const content = screen.getByTestId("game-info-content");
      const joinButton = within(content).getByRole("button", { name: /join game/i });
      expect(joinButton).toBeDisabled();
      expect(
        within(content).getByText(/your reliability is too low to join this game/i)
      ).toBeInTheDocument();
    });

    it("shows 'Add AI player' for a pending game the user manages", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanManage });
      renderGameInfo(pendingGameCanManage.id);

      const content = screen.getByTestId("game-info-content");
      const addButton = within(content).getByRole("button", {
        name: /add ai player/i,
      });
      expect(screen.queryByTestId("add-bot-sheet")).not.toBeInTheDocument();
      await userEvent.click(addButton);
      expect(screen.getByTestId("add-bot-sheet")).toBeInTheDocument();
    });

    it("does not show 'Add AI player' to non-managing members", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      renderGameInfo(pendingGameCanLeave.id);

      const content = screen.getByTestId("game-info-content");
      expect(
        within(content).queryByRole("button", { name: /add ai player/i })
      ).not.toBeInTheDocument();
    });
  });
});
