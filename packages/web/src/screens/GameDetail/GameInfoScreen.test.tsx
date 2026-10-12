import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { GameInfoScreen } from "./GameInfoScreen";

const mockGameData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
}));

vi.mock("@/components/GameInfoContent", () => ({
  GameInfoContent: () => <div data-testid="game-info-content" />,
}));

interface MockActionListProps {
  actions: { key: string }[];
}

vi.mock("@/components/ActionList", () => ({
  ActionList: ({ actions }: MockActionListProps) => (
    <div data-testid="action-list">
      {actions.map(action => action.key).join(",")}
    </div>
  ),
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

const mockCopyLink = vi.fn();
vi.mock("@/utils/copyLink", () => ({
  copyLink: (path: string) => mockCopyLink(path),
}));

const renderGameInfoScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/5/game-info"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/game-info"
            element={<GameInfoScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("GameInfoScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGameData.mockReturnValue({ id: "game-1", name: "Holding Pattern", actions: [] });
  });

  it("shares the game from the top right", async () => {
    const user = userEvent.setup();
    renderGameInfoScreen();

    await user.click(await screen.findByRole("button", { name: "Share game" }));

    expect(mockCopyLink).toHaveBeenCalledWith("/game/game-1");
  });

  it("renders the game's actions at the bottom in the order given", async () => {
    mockGameData.mockReturnValue({
      id: "game-1",
      name: "Holding Pattern",
      actions: [
        { key: "unpause", blockedReason: null },
        { key: "clone_to_sandbox", blockedReason: null },
        { key: "withdraw", blockedReason: null },
      ],
    });

    renderGameInfoScreen();

    expect(await screen.findByTestId("action-list")).toHaveTextContent(
      "unpause,clone_to_sandbox,withdraw"
    );
  });

  it("renders no action list when the game offers none", async () => {
    renderGameInfoScreen();

    await screen.findByTestId("game-info-content");
    expect(screen.queryByTestId("action-list")).not.toBeInTheDocument();
  });
});
