import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GamePhaseRedirect } from "./GamePhaseRedirect";

const mockUseGameRetrieveSuspense = vi.fn();
const mockUseIsMobile = vi.fn();

vi.mock("@/api/generated/endpoints", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/api/generated/endpoints")>();
  return {
    ...actual,
    useGameRetrieveSuspense: (gameId: string) =>
      mockUseGameRetrieveSuspense(gameId),
  };
});

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => mockUseIsMobile(),
}));

const LocationProbe: React.FC = () => {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
};

const renderAtGameRoute = (gameId: string) =>
  render(
    <MemoryRouter initialEntries={[`/game/${gameId}`]}>
      <Routes>
        <Route path="/game/:gameId" element={<GamePhaseRedirect />} />
        <Route path="*" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter>
  );

describe("GamePhaseRedirect", () => {
  beforeEach(() => {
    mockUseGameRetrieveSuspense.mockReset();
    mockUseIsMobile.mockReset();
  });

  it("redirects forming games to the game-info screen", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "abc-1", status: "pending", currentPhaseId: 5 },
    });
    mockUseIsMobile.mockReturnValue(false);

    renderAtGameRoute("abc-1");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game-info/abc-1"
    );
  });

  it("redirects forming games to game-info on mobile too", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "abc-2", status: "pending", currentPhaseId: null },
    });
    mockUseIsMobile.mockReturnValue(true);

    renderAtGameRoute("abc-2");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game-info/abc-2"
    );
  });

  it("redirects active games on mobile to the phase index", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "abc-3", status: "active", currentPhaseId: 7 },
    });
    mockUseIsMobile.mockReturnValue(true);

    renderAtGameRoute("abc-3");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/abc-3/phase/7"
    );
  });

  it("redirects active games on desktop to the orders sub-route", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "abc-3", status: "active", currentPhaseId: 7 },
    });
    mockUseIsMobile.mockReturnValue(false);

    renderAtGameRoute("abc-3");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/abc-3/phase/7/orders"
    );
  });

  it("redirects active games with no current phase back to home", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "abc-4", status: "active", currentPhaseId: null },
    });
    mockUseIsMobile.mockReturnValue(false);

    renderAtGameRoute("abc-4");

    expect(screen.getByTestId("location")).toHaveTextContent("/");
  });
});
