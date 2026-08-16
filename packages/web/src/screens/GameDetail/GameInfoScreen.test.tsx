import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { GameInfoScreen } from "./GameInfoScreen";

vi.mock("@/components/GameInfoContent", () => ({
  GameInfoContent: () => <div>Game information</div>,
}));

vi.mock("./AppBar", () => ({
  GameDetailAppBar: ({
    onNavigateBack,
  }: {
    onNavigateBack?: () => void;
  }) => <button onClick={onNavigateBack}>Close Game Info</button>,
}));

describe("GameInfoScreen", () => {
  it("returns to Overview when closed", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/game/g1/phase/1/game-info"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/game-info"
            element={<GameInfoScreen />}
          />
          <Route
            path="/game/:gameId/phase/:phaseId/overview"
            element={<div>Overview screen</div>}
          />
        </Routes>
      </MemoryRouter>
    );

    await user.click(
      screen.getByRole("button", { name: "Close Game Info" })
    );

    expect(screen.getByText("Overview screen")).toBeInTheDocument();
  });
});
