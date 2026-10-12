import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { PlayerProfileScreen } from "./PlayerProfileScreen";

const mockNavigate = vi.fn();
vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("@/components/PlayerProfileContent", () => ({
  PlayerProfileContent: () => <div data-testid="profile" />,
  PlayerProfileContentSkeleton: () => null,
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => true,
}));

const renderProfile = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/player/:userId"
          element={<PlayerProfileScreen />}
        />
      </Routes>
    </MemoryRouter>
  );

describe("PlayerProfileScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("goes back to the member screen it was opened from", async () => {
    const user = userEvent.setup();
    renderProfile("/game/game-1/phase/5/player/20?member=7");

    await user.click(screen.getAllByRole("button")[0]);

    expect(mockNavigate).toHaveBeenCalledWith("/game/game-1/phase/5/member/7");
  });

  it("goes back to the players screen without a member to return to", async () => {
    const user = userEvent.setup();
    renderProfile("/game/game-1/phase/5/player/20");

    await user.click(screen.getAllByRole("button")[0]);

    expect(mockNavigate).toHaveBeenCalledWith("/game/game-1/phase/5/player-info");
  });
});
