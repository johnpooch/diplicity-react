import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { OverviewScreen } from "./OverviewScreen";

const mockGameData = vi.fn();
const mockDrawProposalsData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useGamesDrawProposalsList: () => ({ data: mockDrawProposalsData() }),
}));

vi.mock("@/components/PlayerInfoContent", () => ({
  PlayerInfoContent: () => <div>Players</div>,
}));

vi.mock("@/components/GameDropdownMenu", () => ({
  GameDropdownMenu: () => <button>Game menu</button>,
}));

vi.mock("./AppBar", () => ({
  GameDetailAppBar: ({ rightButton }: { rightButton?: React.ReactNode }) => (
    <header>{rightButton}</header>
  ),
}));

const renderOverview = () =>
  render(
    <MemoryRouter initialEntries={["/game/g1/phase/1/overview"]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/overview"
          element={<OverviewScreen />}
        />
      </Routes>
    </MemoryRouter>
  );

describe("OverviewScreen draw proposals", () => {
  it("shows the active-proposal notification badge on the button", () => {
    mockGameData.mockReturnValue({
      status: "active",
      sandbox: false,
    });
    mockDrawProposalsData.mockReturnValue([
      {
        id: 1,
        status: "pending",
        myVote: { included: true, accepted: null },
      },
    ]);

    renderOverview();

    const link = screen.getByRole("link", { name: /draw proposals/i });
    expect(within(link).getByText("1")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /game menu/i })
    ).toBeInTheDocument();
  });
});
