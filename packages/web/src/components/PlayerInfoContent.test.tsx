import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi } from "vitest";

import { PlayerInfoContent } from "./PlayerInfoContent";

const mockGameData = vi.fn();
const mockVariantsData = vi.fn();
const mockCurrentPhaseData = vi.fn();
const mockMutateAsync = vi.fn().mockResolvedValue({});
const mockInvalidateQueries = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useGamePhaseRetrieve: () => ({ data: mockCurrentPhaseData() }),
  useGameRecoverFromCivilDisorderCreate: () => ({ mutateAsync: mockMutateAsync }),
  getGameRetrieveQueryKey: (gameId: string) => ["game", gameId],
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
  findNationColor: () => null,
}));

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }),
  };
});

const renderPlayerInfo = () =>
  render(
    <MemoryRouter initialEntries={["/game/game-1"]}>
      <Routes>
        <Route path="/game/:gameId" element={<PlayerInfoContent />} />
      </Routes>
    </MemoryRouter>
  );

const baseMember = {
  id: 1,
  name: "Alice",
  picture: null,
  isCurrentUser: true,
  nation: "England",
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
};

describe("PlayerInfoContent", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([
      { id: "classical", name: "Classical" },
    ]);
    mockCurrentPhaseData.mockReturnValue({ supplyCenters: [] });
    mockMutateAsync.mockResolvedValue({});
    mockInvalidateQueries.mockReset();
  });

  it("shows the civil disorder badge for members in civil disorder", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice", civilDisorder: true },
        { ...baseMember, id: 2, name: "Bob", civilDisorder: false },
      ],
    });

    renderPlayerInfo();

    const badges = screen.getAllByText("Civil Disorder");
    expect(badges).toHaveLength(1);
  });

  it("does not show the civil disorder badge for active members", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, civilDisorder: false }],
    });

    renderPlayerInfo();

    expect(screen.queryByText("Civil Disorder")).not.toBeInTheDocument();
  });

  it("shows the game master above the players when one is set", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      gameMaster: { userId: 42, name: "Carol", picture: null },
      members: [{ ...baseMember }],
    });

    renderPlayerInfo();

    expect(screen.getByText("Carol")).toBeInTheDocument();
    expect(screen.getByText("Game Master")).toBeInTheDocument();
  });

  it("does not show a game master row when none is set", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      gameMaster: null,
      members: [{ ...baseMember }],
    });

    renderPlayerInfo();

    expect(screen.queryByText("Game Master")).not.toBeInTheDocument();
  });

  it("shows I'm back button for current user in civil disorder", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, isCurrentUser: true, civilDisorder: true }],
    });

    renderPlayerInfo();

    expect(screen.getByRole("button", { name: "I'm back" })).toBeInTheDocument();
  });

  it("does not show I'm back button for other users in civil disorder", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, isCurrentUser: false, civilDisorder: true }],
    });

    renderPlayerInfo();

    expect(screen.queryByRole("button", { name: "I'm back" })).not.toBeInTheDocument();
  });

  it("does not show I'm back button for current user not in civil disorder", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, isCurrentUser: true, civilDisorder: false }],
    });

    renderPlayerInfo();

    expect(screen.queryByRole("button", { name: "I'm back" })).not.toBeInTheDocument();
  });

  it("calls the recovery mutation when I'm back button is clicked", async () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, isCurrentUser: true, civilDisorder: true }],
    });

    renderPlayerInfo();

    fireEvent.click(screen.getByRole("button", { name: "I'm back" }));

    expect(mockMutateAsync).toHaveBeenCalledWith({ gameId: "game-1" });
  });
});
