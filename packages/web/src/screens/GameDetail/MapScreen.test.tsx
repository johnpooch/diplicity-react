import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";

import { MapScreen } from "./MapScreen";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const mockGameData = vi.fn();

vi.mock("@/api/generated/endpoints", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useGameRetrieveSuspense: () => ({ data: mockGameData() }),
    useVariantsListSuspense: () => ({ data: [] }),
    useVariantsRetrieve: () => ({ data: undefined }),
    useGameJoinCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
    useGameLeaveDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
    useUserRetrieveSuspense: () => ({ data: { canCreateBotGames: true } }),
    getGameRetrieveQueryKey: () => ["game"],
  };
});

vi.mock("@/components/PhaseSelect", () => ({ PhaseSelect: () => <div data-testid="phase-select" /> }));
vi.mock("@/components/PhaseGuidance", () => ({ PhaseGuidance: () => null }));
vi.mock("@/components/GameDropdownMenu", () => ({ GameDropdownMenu: () => null }));
vi.mock("@/components/GameMap", () => ({ GameMap: () => <div data-testid="game-map" /> }));
vi.mock("@/components/AddBotSheet", () => ({ AddBotSheet: () => null }));

const baseGame = {
  id: "game-1",
  name: "Gathering Forces",
  status: "active",
  variantId: "classical",
  members: [],
  canJoin: false,
  canLeave: false,
  canManage: false,
  minReliability: "open",
  sandbox: false,
};

const renderMapScreen = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1"]}>
        <Routes>
          <Route path="/game/:gameId/phase/:phaseId" element={<MapScreen />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("MapScreen", () => {
  it("shows the phase selector for an active game", () => {
    mockGameData.mockReturnValue({ ...baseGame, status: "active" });
    renderMapScreen();

    expect(screen.getByTestId("phase-select")).toBeInTheDocument();
    expect(screen.queryByText("Gathering Forces")).not.toBeInTheDocument();
  });

  it("shows the game name and no action row for a pending game with no join/leave available", () => {
    mockGameData.mockReturnValue({ ...baseGame, status: "pending" });
    renderMapScreen();

    expect(screen.queryByTestId("phase-select")).not.toBeInTheDocument();
    expect(screen.getByText("Gathering Forces")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /join game/i })).not.toBeInTheDocument();
  });

  it("shows a Join game button for a pending game the user can join", () => {
    mockGameData.mockReturnValue({ ...baseGame, status: "pending", canJoin: true });
    renderMapScreen();

    expect(screen.getByRole("button", { name: /join game/i })).toBeInTheDocument();
  });
});
