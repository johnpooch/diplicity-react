import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameReplaceRedirect } from "./GameReplaceRedirect";

const mockUseGameRetrieveSuspense = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual =
    await importOriginal<typeof import("@/api/generated/endpoints")>();
  return {
    ...actual,
    useGameRetrieveSuspense: (gameId: string) =>
      mockUseGameRetrieveSuspense(gameId),
  };
});

const LocationProbe: React.FC = () => {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
};

const renderAtReplaceRoute = (gameId: string, memberId: string) =>
  render(
    <MemoryRouter initialEntries={[`/game/${gameId}/replace/${memberId}`]}>
      <Routes>
        <Route
          path="/game/:gameId/replace/:memberId"
          element={<GameReplaceRedirect />}
        />
        <Route path="*" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter>
  );

describe("GameReplaceRedirect", () => {
  beforeEach(() => {
    mockUseGameRetrieveSuspense.mockReset();
  });

  it("redirects into the replace screen for the current phase", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "abc-1", currentPhaseId: 7 },
    });

    renderAtReplaceRoute("abc-1", "12");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/abc-1/phase/7/replace/12"
    );
  });

  it("redirects to game info when the game has no current phase", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "abc-2", currentPhaseId: null },
    });

    renderAtReplaceRoute("abc-2", "12");

    expect(screen.getByTestId("location")).toHaveTextContent("/game-info/abc-2");
  });
});
