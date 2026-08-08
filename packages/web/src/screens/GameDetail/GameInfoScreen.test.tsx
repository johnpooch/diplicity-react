import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";

import { GameInfoScreen } from "./GameInfoScreen";

const mockGameData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
}));

vi.mock("@/components/GameInfoContent", () => ({
  GameInfoContent: () => <div data-testid="game-info-content" />,
}));

vi.mock("@/components/GameDropdownMenu", () => ({
  GameDropdownMenu: () => <div data-testid="game-dropdown-menu" />,
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => true,
}));

const baseGame = {
  id: "game-1",
  status: "active",
  canLeave: false,
  canDelete: false,
  canManage: false,
  isPaused: false,
  sandbox: false,
};

const LocationProbe: React.FC = () => {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
};

const renderGameInfoScreen = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/game-info"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/game-info"
            element={<GameInfoScreen />}
          />
          <Route path="*" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("GameInfoScreen", () => {
  it("shows the game dropdown menu for a pending game", () => {
    mockGameData.mockReturnValue({ ...baseGame, status: "pending" });
    renderGameInfoScreen();

    expect(screen.getByTestId("game-dropdown-menu")).toBeInTheDocument();
  });

  it("does not show the game dropdown menu for an active game", () => {
    mockGameData.mockReturnValue({ ...baseGame, status: "active" });
    renderGameInfoScreen();

    expect(screen.queryByTestId("game-dropdown-menu")).not.toBeInTheDocument();
  });

  it("navigates back to home for a pending game", async () => {
    mockGameData.mockReturnValue({ ...baseGame, status: "pending" });
    renderGameInfoScreen();

    await userEvent.click(screen.getByRole("button"));

    expect(screen.getByTestId("location")).toHaveTextContent("/");
  });

  it("navigates back to the phase root for an active game", async () => {
    mockGameData.mockReturnValue({ ...baseGame, status: "active" });
    renderGameInfoScreen();

    await userEvent.click(screen.getByRole("button"));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/game-1/phase/1"
    );
  });
});
