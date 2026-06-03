import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GamePhaseRedirect } from "./GamePhaseRedirect";
import { deepLinkStorage } from "@/deepLink";

const mockUseGameRetrieveSuspense = vi.fn();
const mockUseIsMobile = vi.fn();
const mockUseAuth = vi.fn();

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

vi.mock("@/auth", () => ({
  useAuth: () => mockUseAuth(),
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
    mockUseAuth.mockReturnValue({ loggedIn: true });
    deepLinkStorage.consumePendingPath();
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

  it("redirects to / and stores path when game is private and user is not logged in", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "priv-1", status: "active", currentPhaseId: 3, private: true },
    });
    mockUseAuth.mockReturnValue({ loggedIn: false });
    mockUseIsMobile.mockReturnValue(false);

    renderAtGameRoute("priv-1");

    expect(screen.getByTestId("location")).toHaveTextContent("/");
    expect(deepLinkStorage.getPendingPath()).toBe("/game/priv-1");
  });

  it("does not redirect private game when user is logged in", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "priv-2", status: "active", currentPhaseId: 5, private: true },
    });
    mockUseAuth.mockReturnValue({ loggedIn: true });
    mockUseIsMobile.mockReturnValue(false);

    renderAtGameRoute("priv-2");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/priv-2/phase/5/orders"
    );
    expect(deepLinkStorage.getPendingPath()).toBeNull();
  });

  it("proceeds normally for public game when user is not logged in", () => {
    mockUseGameRetrieveSuspense.mockReturnValue({
      data: { id: "pub-1", status: "active", currentPhaseId: 7, private: false },
    });
    mockUseAuth.mockReturnValue({ loggedIn: false });
    mockUseIsMobile.mockReturnValue(false);

    renderAtGameRoute("pub-1");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/pub-1/phase/7/orders"
    );
    expect(deepLinkStorage.getPendingPath()).toBeNull();
  });
});
