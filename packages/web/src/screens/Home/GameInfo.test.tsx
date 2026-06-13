import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameInfoScreen } from "./GameInfo";
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
    useGameJoinCreate: () => ({
      mutateAsync: mockJoinMutateAsync,
      isPending: false,
    }),
    useGameLeaveDestroy: () => ({
      mutateAsync: mockLeaveMutateAsync,
      isPending: false,
    }),
    getGameRetrieveQueryKey: (gameId: string) => ["games", gameId],
  };
});

vi.mock("@/components/GameInfoContent", () => ({
  GameInfoContent: ({
    pendingAction,
  }: {
    pendingAction?: React.ReactNode;
    onNavigateToPlayerInfo: () => void;
  }) => <div data-testid="game-info-content">{pendingAction}</div>,
}));

vi.mock("@/components/GameDropdownMenu", () => ({
  GameDropdownMenu: () => <div data-testid="game-dropdown-menu" />,
}));

const pendingGameCanJoin = mockPendingGames.find((g) => g.canJoin)!;
const pendingGameCanLeave = mockPendingGames.find((g) => !g.canJoin)!;

const renderGameInfo = (gameId: string) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  vi.spyOn(queryClient, "invalidateQueries").mockResolvedValue();

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/game-info/${gameId}`]}>
        <Routes>
          <Route path="/game-info/:gameId" element={<GameInfoScreen />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

  return { queryClient };
};

describe("GameInfoScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockJoinMutateAsync.mockResolvedValue(undefined);
    mockLeaveMutateAsync.mockResolvedValue(undefined);
  });

  describe("CTA placement", () => {
    it("shows 'Join game' button in the content area for a pending game the user can join", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      renderGameInfo(pendingGameCanJoin.id);

      const content = screen.getByTestId("game-info-content");
      expect(
        within(content).getByRole("button", { name: /join game/i })
      ).toBeInTheDocument();
    });

    it("shows 'Leave game' button in the content area for a pending game the user has already joined", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      renderGameInfo(pendingGameCanLeave.id);

      const content = screen.getByTestId("game-info-content");
      expect(
        within(content).getByRole("button", { name: /^leave$/i })
      ).toBeInTheDocument();
    });

    it("shows no join/leave button for an active game", () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: mockActiveGames[0] });
      renderGameInfo(mockActiveGames[0].id);

      const content = screen.getByTestId("game-info-content");
      expect(
        within(content).queryByRole("button", { name: /join game/i })
      ).not.toBeInTheDocument();
      expect(
        within(content).queryByRole("button", { name: /^leave$/i })
      ).not.toBeInTheDocument();
    });
  });

  describe("join game", () => {
    it("calls the join mutation when 'Join game' is clicked", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      renderGameInfo(pendingGameCanJoin.id);

      await userEvent.click(screen.getByRole("button", { name: /join game/i }));

      expect(mockJoinMutateAsync).toHaveBeenCalledWith({
        gameId: pendingGameCanJoin.id,
        data: {},
      });
    });

    it("invalidates the game query after joining so the button updates immediately", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanJoin });
      const { queryClient } = renderGameInfo(pendingGameCanJoin.id);

      await userEvent.click(screen.getByRole("button", { name: /join game/i }));

      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ["games", pendingGameCanJoin.id],
      });
    });
  });

  describe("leave game", () => {
    it("calls the leave mutation when 'Leave' is clicked", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      renderGameInfo(pendingGameCanLeave.id);

      await userEvent.click(
        screen.getByRole("button", { name: /^leave$/i })
      );

      expect(mockLeaveMutateAsync).toHaveBeenCalledWith({
        gameId: pendingGameCanLeave.id,
      });
    });

    it("invalidates the game query after leaving so the button updates immediately", async () => {
      mockUseGameRetrieveSuspense.mockReturnValue({ data: pendingGameCanLeave });
      const { queryClient } = renderGameInfo(pendingGameCanLeave.id);

      await userEvent.click(
        screen.getByRole("button", { name: /^leave$/i })
      );

      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ["games", pendingGameCanLeave.id],
      });
    });
  });
});
