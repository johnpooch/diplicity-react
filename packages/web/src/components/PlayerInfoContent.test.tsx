import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi } from "vitest";

import { PlayerInfoContent } from "./PlayerInfoContent";

const mockGameData = vi.fn();
const mockVariantsData = vi.fn();
const mockCurrentPhaseData = vi.fn();
const mockUserProfileData = vi.fn();
const mockKickMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamePhaseRetrieve: () => ({ data: mockCurrentPhaseData() }),
  useUserRetrieveSuspense: () => ({ data: mockUserProfileData() }),
  useGameKickDestroy: () => ({
    mutateAsync: mockKickMutateAsync,
    isPending: false,
  }),
  getGameRetrieveQueryKey: () => ["game"],
  getGameAvailableBotsListQueryKey: () => ["available-bots"],
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
  findNationColor: () => null,
}));

interface MockAddBotSheetProps {
  open: boolean;
}

vi.mock("@/components/AddBotSheet", () => ({
  AddBotSheet: ({ open }: MockAddBotSheetProps) =>
    open ? <div data-testid="add-bot-sheet" /> : null,
}));

const renderPlayerInfo = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1"]}>
        <Routes>
          <Route path="/game/:gameId" element={<PlayerInfoContent />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

const baseMember = {
  id: 1,
  name: "Alice",
  picture: null,
  isCurrentUser: true,
  isBot: false,
  nation: "England",
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
};

const classicalVariant = {
  id: "classical",
  name: "Classical",
  nations: Array.from({ length: 7 }, (_, index) => ({
    name: `Nation ${index}`,
    nonPlayable: false,
  })),
};

describe("PlayerInfoContent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVariantsData.mockReturnValue([classicalVariant]);
    mockCurrentPhaseData.mockReturnValue({ supplyCenters: [] });
    mockUserProfileData.mockReturnValue({ canCreateBotGames: true });
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

  it("shows a bot badge for bot members only", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice" },
        { ...baseMember, id: 2, name: "The Dealmaker", isBot: true },
      ],
    });

    renderPlayerInfo();

    expect(screen.getAllByText("Bot")).toHaveLength(1);
  });

  it("shows add AI player rows for each open seat to a managing admin", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      canManage: true,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [],
      members: [
        { ...baseMember, nation: null },
        { ...baseMember, id: 2, name: "Bob", isCurrentUser: false, nation: null },
      ],
    });

    renderPlayerInfo();

    expect(screen.getAllByText("Add AI player")).toHaveLength(5);
    expect(screen.queryByText("Open seat")).not.toBeInTheDocument();
  });

  it("shows open seat rows without the add affordance to non-admins", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      canManage: false,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [],
      members: [{ ...baseMember, nation: null }],
    });

    renderPlayerInfo();

    expect(screen.getAllByText("Open seat")).toHaveLength(6);
    expect(screen.queryByText("Add AI player")).not.toBeInTheDocument();
  });

  it("shows open seat rows when the admin cannot use bot opponents", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      canManage: true,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [],
      members: [{ ...baseMember, nation: null }],
    });
    mockUserProfileData.mockReturnValue({ canCreateBotGames: false });

    renderPlayerInfo();

    expect(screen.getAllByText("Open seat")).toHaveLength(6);
    expect(screen.queryByText("Add AI player")).not.toBeInTheDocument();
  });

  it("does not show open seats for active games", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      canManage: true,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember }],
    });

    renderPlayerInfo();

    expect(screen.queryByText("Open seat")).not.toBeInTheDocument();
    expect(screen.queryByText("Add AI player")).not.toBeInTheDocument();
  });

  it("opens the add bot sheet when an admin clicks an open seat", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      canManage: true,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [],
      members: [{ ...baseMember, nation: null }],
    });

    renderPlayerInfo();

    expect(screen.queryByTestId("add-bot-sheet")).not.toBeInTheDocument();
    await user.click(screen.getAllByText("Add AI player")[0]);
    expect(screen.getByTestId("add-bot-sheet")).toBeInTheDocument();
  });

  it("lets an admin remove a bot from a pending game", async () => {
    const user = userEvent.setup();
    mockKickMutateAsync.mockResolvedValue(undefined);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      canManage: true,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [],
      members: [
        { ...baseMember, nation: null },
        {
          ...baseMember,
          id: 2,
          name: "The Dealmaker",
          isCurrentUser: false,
          isBot: true,
          nation: null,
        },
      ],
    });

    renderPlayerInfo();

    await user.click(screen.getByLabelText("Remove The Dealmaker"));
    expect(mockKickMutateAsync).toHaveBeenCalledWith({
      gameId: "game-1",
      memberId: 2,
    });
  });

  it("does not show a remove button to non-admins or for humans", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      canManage: false,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [],
      members: [
        { ...baseMember, nation: null },
        {
          ...baseMember,
          id: 2,
          name: "The Dealmaker",
          isCurrentUser: false,
          isBot: true,
          nation: null,
        },
      ],
    });

    renderPlayerInfo();

    expect(screen.queryByLabelText("Remove The Dealmaker")).not.toBeInTheDocument();
  });
});
