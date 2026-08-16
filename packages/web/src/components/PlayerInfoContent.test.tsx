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
const mockChannelsData = vi.fn();
const mockCreateChannelMutateAsync = vi.fn();
const mockIsMobile = vi.fn();

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => mockIsMobile(),
}));

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
  useGamesChannelsList: () => ({
    data: mockChannelsData(),
    isLoading: false,
  }),
  useGamesChannelsCreateCreate: () => ({
    mutateAsync: mockCreateChannelMutateAsync,
    isPending: false,
  }),
  getGameRetrieveQueryKey: () => ["game"],
  getGameAddableUserListQueryKey: () => ["addable-user"],
  getGamesChannelsListQueryKey: () => ["channels"],
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

const renderPlayerInfo = (initialEntry = "/game/game-1") =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/game/:gameId" element={<PlayerInfoContent />} />
          <Route
            path="/game/:gameId/phase/:phaseId/overview"
            element={<PlayerInfoContent />}
          />
          <Route
            path="/game/:gameId/phase/:phaseId/chat/channel/:channelId"
            element={<div data-testid="channel-screen" />}
          />
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
    mockCurrentPhaseData.mockReturnValue({ supplyCenters: [], units: [] });
    mockUserProfileData.mockReturnValue({ canCreateBotGames: true });
    mockChannelsData.mockReturnValue([]);
    mockIsMobile.mockReturnValue(false);
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

  it("shows unit and supply-center counts from the current phase", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember }],
    });
    mockCurrentPhaseData.mockReturnValue({
      units: [
        { nation: { name: "England" } },
        { nation: { name: "England" } },
        { nation: { name: "France" } },
      ],
      supplyCenters: [
        { nation: { name: "England" } },
        { nation: { name: "England" } },
        { nation: { name: "England" } },
      ],
    });

    renderPlayerInfo();

    expect(screen.getByText("2 units")).toBeInTheDocument();
    expect(screen.getByText("3 centers")).toBeInTheDocument();
  });

  it("uses the nation as the in-game title and puts player details in a popover", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      nmrExtensionsAllowed: 2,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, commitment: "high", nmrExtensionsRemaining: 1 },
      ],
    });

    renderPlayerInfo("/game/game-1/phase/1/overview");

    expect(screen.getByText("England")).toBeInTheDocument();
    expect(screen.queryByText("Alice")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Commitment: High")).not.toBeInTheDocument();
    expect(
      screen.queryByText("1 extension remaining")
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "View England player details" })
    );

    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByLabelText("Commitment: High")).toBeInTheDocument();
    expect(screen.getByText("1 extension remaining")).toBeInTheDocument();
    expect(screen.queryByText("Player")).not.toBeInTheDocument();
  });

  it("shows eliminated as the player's status", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, eliminated: true, civilDisorder: true }],
    });

    renderPlayerInfo();

    expect(screen.getByText("Eliminated")).toBeInTheDocument();
    expect(screen.queryByText("Civil Disorder")).not.toBeInTheDocument();
  });

  it("dims and moves eliminated and civil-disorder powers to the bottom", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, nation: "England", eliminated: true },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          nation: "France",
          isCurrentUser: false,
        },
        {
          ...baseMember,
          id: 3,
          name: "Carol",
          nation: "Germany",
          isCurrentUser: false,
          civilDisorder: true,
        },
      ],
    });

    renderPlayerInfo("/game/game-1/phase/1/overview");

    expect(
      screen
        .getAllByRole("button", { name: /View .* player details/ })
        .map(button => button.getAttribute("aria-label"))
    ).toEqual([
      "View France player details",
      "View England player details",
      "View Germany player details",
    ]);
    expect(screen.getByText("France").closest(".gap-4")).not.toHaveClass(
      "opacity-[0.7]"
    );
    expect(screen.getByText("England").closest(".gap-4")).toHaveClass(
      "opacity-[0.7]"
    );
    expect(screen.getByText("Germany").closest(".gap-4")).toHaveClass(
      "opacity-[0.7]"
    );
  });

  it("moves the winner to the top when the game is completed", () => {
    const winner = {
      ...baseMember,
      id: 3,
      name: "Carol",
      nation: "Germany",
      isCurrentUser: false,
      eliminated: true,
    };

    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      nmrExtensionsAllowed: 0,
      victory: {
        id: 1,
        type: "solo",
        winningPhaseId: 1,
        members: [winner],
      },
      phases: [{ id: 1, status: "completed" }],
      members: [
        { ...baseMember, nation: "England", eliminated: true },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          nation: "France",
          isCurrentUser: false,
        },
        winner,
      ],
    });

    renderPlayerInfo("/game/game-1/phase/1/overview");

    expect(
      screen
        .getAllByRole("button", { name: /View .* player details/ })
        .map(button => button.getAttribute("aria-label"))
    ).toEqual([
      "View Germany player details",
      "View France player details",
      "View England player details",
    ]);
  });

  it("opens an existing one-to-one chat with another human player", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      pressType: "regular",
      sandbox: false,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember },
        { ...baseMember, id: 2, name: "Bob", isCurrentUser: false },
      ],
    });
    mockChannelsData.mockReturnValue([
      { id: 42, private: true, memberIds: [1, 2] },
    ]);

    renderPlayerInfo("/game/game-1/phase/1/overview");
    await user.click(screen.getByLabelText("Message Bob"));

    expect(await screen.findByTestId("channel-screen")).toBeInTheDocument();
    expect(mockCreateChannelMutateAsync).not.toHaveBeenCalled();
  });

  it("marks a player's chat shortcut when their direct channel is unread", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      pressType: "regular",
      sandbox: false,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember },
        { ...baseMember, id: 2, name: "Bob", isCurrentUser: false },
      ],
    });
    mockChannelsData.mockReturnValue([
      {
        id: 42,
        private: true,
        memberIds: [1, 2],
        unreadMessageCount: 2,
      },
    ]);

    renderPlayerInfo("/game/game-1/phase/1/overview");

    expect(
      screen.getByRole("button", {
        name: "Message Bob, 2 unread messages",
      })
    ).toBeInTheDocument();
  });

  it("creates a one-to-one chat when one does not exist", async () => {
    const user = userEvent.setup();
    mockCreateChannelMutateAsync.mockResolvedValue({
      id: 43,
      private: true,
      memberIds: [1, 2],
    });
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      pressType: "regular",
      sandbox: false,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember },
        { ...baseMember, id: 2, name: "Bob", isCurrentUser: false },
      ],
    });

    renderPlayerInfo("/game/game-1/phase/1/overview");
    await user.click(screen.getByLabelText("Message Bob"));

    expect(mockCreateChannelMutateAsync).toHaveBeenCalledWith({
      gameId: "game-1",
      data: { memberIds: [2] },
    });
    expect(await screen.findByTestId("channel-screen")).toBeInTheDocument();
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
