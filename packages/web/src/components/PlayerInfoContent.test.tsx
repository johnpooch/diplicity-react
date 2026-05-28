import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi } from "vitest";

import { PlayerInfoContent } from "./PlayerInfoContent";

const mockGameData = vi.fn();
const mockVariantsData = vi.fn();
const mockCurrentPhaseData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useGamePhaseRetrieve: () => ({ data: mockCurrentPhaseData() }),
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
}));

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
  isGameMaster: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
};

describe("PlayerInfoContent", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([
      { id: "classical", name: "Classical" },
    ]);
    mockCurrentPhaseData.mockReturnValue({ supplyCenters: [] });
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

  it("shows the eliminated badge for eliminated members", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice", eliminated: true },
        { ...baseMember, id: 2, name: "Bob", eliminated: false },
      ],
    });

    renderPlayerInfo();

    const badges = screen.getAllByText("Eliminated");
    expect(badges).toHaveLength(1);
  });

  it("does not show the eliminated badge for surviving members", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, eliminated: false }],
    });

    renderPlayerInfo();

    expect(screen.queryByText("Eliminated")).not.toBeInTheDocument();
  });
});
