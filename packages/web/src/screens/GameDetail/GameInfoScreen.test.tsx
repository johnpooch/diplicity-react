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

vi.mock("@/components/ExpandableMapPreview", () => ({
  ExpandableMapPreview: () => <div data-testid="map-preview" />,
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

  describe("header Join/Leave button", () => {
    it("shows a Join button for a pending game the user can join", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      renderGameInfo(pendingGameCanJoin.id);

      expect(
        screen.getByRole("button", { name: /join game/i })
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /leave game/i })
      ).not.toBeInTheDocument();
    });

    it("shows a Leave button, in the same slot, for a pending game the user has joined", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      renderGameInfo(pendingGameCanLeave.id);

      expect(
        screen.getByRole("button", { name: /leave game/i })
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /join game/i })
      ).not.toBeInTheDocument();
    });

    it("shows a disabled Join button once neither joining nor leaving is possible, rather than no button at all", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({
        data: pendingGameReliabilityRequired,
      });
      renderGameInfo(pendingGameReliabilityRequired.id);

      const content = screen.getByTestId("game-info-content");
      const headerJoinButton = screen
        .getAllByRole("button", { name: /join game/i })
        .find((button) => !content.contains(button));
      expect(headerJoinButton).toBeDisabled();
    });

    it("calls the join mutation when Join is clicked", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      renderGameInfo(pendingGameCanJoin.id);

      await userEvent.click(screen.getByRole("button", { name: /join game/i }));

      expect(mockJoinMutateAsync).toHaveBeenCalledWith({
        gameId: pendingGameCanJoin.id,
      });
    });

    it("calls the leave mutation when Leave is clicked", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      renderGameInfo(pendingGameCanLeave.id);

      await userEvent.click(screen.getByRole("button", { name: /leave game/i }));

      expect(mockLeaveMutateAsync).toHaveBeenCalledWith({
        gameId: pendingGameCanLeave.id,
      });
    });

    it("shows no join/leave button for an active game", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: mockActiveGames[0] });
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
    it("shows a reliability message when reliability-gated (the disabled Join button itself lives in the header)", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({
        data: pendingGameReliabilityRequired,
      });
      renderGameInfo(pendingGameReliabilityRequired.id);

      const content = screen.getByTestId("game-info-content");
      expect(
        within(content).getByText(/your reliability is too low to join this game/i)
      ).toBeInTheDocument();
      expect(
        within(content).queryByRole("button", { name: /join game/i })
      ).not.toBeInTheDocument();
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
