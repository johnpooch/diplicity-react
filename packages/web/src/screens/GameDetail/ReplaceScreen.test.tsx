import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ReplaceScreen } from "./ReplaceScreen";

const mockGameData = vi.fn();
const mockVariantsData = vi.fn();
const mockCurrentPhaseData = vi.fn();
const mockReplaceMutateAsync = vi.fn();
const mockNavigate = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamePhaseRetrieve: () => ({ data: mockCurrentPhaseData() }),
  useGameMembersReplaceCreate: () => ({
    mutateAsync: mockReplaceMutateAsync,
    isPending: false,
  }),
  getGameRetrieveQueryKey: () => ["game"],
  getGamesListQueryKey: () => ["games"],
  StatusEnum: { pending: "pending", active: "active", completed: "completed" },
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
  findNationColor: () => null,
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const renderReplaceScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/replace/2"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/replace/:memberId"
            element={<ReplaceScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

const openSeat = {
  id: 2,
  userId: 20,
  name: "Bob",
  picture: null,
  isCurrentUser: false,
  isBot: false,
  nation: "Turkey",
  eliminated: false,
  kicked: true,
  isGameCreator: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
  seekingReplacement: false,
  replaceable: true,
};

const otherSeat = { ...openSeat, id: 1, userId: 10, name: "Alice", nation: "England", kicked: false, replaceable: false };

const activeGame = {
  id: "game-1",
  variantId: "classical",
  status: "active",
  isPaused: false,
  pressType: "full_press",
  gameMaster: null,
  currentPhaseId: 1,
  phases: [{ id: 1, status: "active" }],
  nmrExtensionsAllowed: 0,
  victory: null,
  members: [otherSeat, openSeat],
};

const classicalVariant = {
  id: "classical",
  name: "Classical",
  nations: [
    { name: "England", nonPlayable: false },
    { name: "Turkey", nonPlayable: false },
  ],
};

describe("ReplaceScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVariantsData.mockReturnValue([classicalVariant]);
    mockCurrentPhaseData.mockReturnValue({
      id: 1,
      name: "Fall 1901, Movement",
      remainingTime: 3600,
      scheduledResolution: "2026-05-02T10:00:00Z",
      supplyCenters: [{ nation: { name: "Turkey" } }, { nation: { name: "Turkey" } }],
    });
    mockGameData.mockReturnValue(activeGame);
  });

  it("describes the seat on offer", () => {
    renderReplaceScreen();

    expect(screen.getByText("Turkey")).toBeInTheDocument();
    expect(
      screen.getByText(/Removed from the game by the game creator/)
    ).toBeInTheDocument();
    expect(screen.getByText("Fall 1901, Movement")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("names the civil disorder reason when the seat was not removed", () => {
    mockGameData.mockReturnValue({
      ...activeGame,
      members: [otherSeat, { ...openSeat, kicked: false, civilDisorder: true }],
    });

    renderReplaceScreen();

    expect(screen.getByText(/civil disorder/)).toBeInTheDocument();
  });

  it("takes over the seat and navigates into the game", async () => {
    const user = userEvent.setup();
    mockReplaceMutateAsync.mockResolvedValue({});

    renderReplaceScreen();

    await user.click(screen.getByRole("button", { name: "Take Over Turkey" }));

    expect(mockReplaceMutateAsync).toHaveBeenCalledWith({
      gameId: "game-1",
      memberId: 2,
    });
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith("/game/game-1/phase/1/orders")
    );
  });

  it("blocks a player who is already in the game", () => {
    mockGameData.mockReturnValue({
      ...activeGame,
      members: [{ ...otherSeat, isCurrentUser: true }, openSeat],
    });

    renderReplaceScreen();

    expect(screen.getByText("Already playing")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Take Over Turkey" })
    ).not.toBeInTheDocument();
  });

  it("blocks a seat that is no longer open", () => {
    mockGameData.mockReturnValue({
      ...activeGame,
      members: [otherSeat, { ...openSeat, kicked: false, replaceable: false }],
    });

    renderReplaceScreen();

    expect(screen.getByText("Seat filled")).toBeInTheDocument();
  });

  it("blocks a game that is not in progress", () => {
    mockGameData.mockReturnValue({ ...activeGame, status: "completed" });

    renderReplaceScreen();

    expect(screen.getByText("Game not in progress")).toBeInTheDocument();
  });
});
