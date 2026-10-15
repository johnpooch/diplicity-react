import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi } from "vitest";

import { PlayerInfoContent } from "./PlayerInfoContent";

const mockNavigate = vi.fn();
vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockGameData = vi.fn();
const mockVariantsData = vi.fn();
const mockCurrentPhaseData = vi.fn();
const mockUserProfileData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { actions: [], playerListActions: [], gameMasterMemberId: null, ...mockGameData() },
  }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamePhaseRetrieve: () => ({ data: mockCurrentPhaseData() }),
  useUserRetrieveSuspense: () => ({ data: mockUserProfileData() }),
}));

interface MockActionListProps {
  actions: { key: string }[];
  children?: React.ReactNode;
}

vi.mock("@/components/ActionList", () => ({
  ActionList: ({ actions, children }: MockActionListProps) => (
    <>
      {actions.length > 0 && (
        <div data-testid="action-list">
          {actions.map(action => action.key).join(",")}
        </div>
      )}
      {children}
    </>
  ),
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
  findNationColor: () => null,
  getContrastColor: () => "#ffffff",
}));

interface MockAddBotSheetProps {
  open: boolean;
}

vi.mock("@/components/AddBotSheet", () => ({
  AddBotSheet: ({ open }: MockAddBotSheetProps) =>
    open ? <div data-testid="add-bot-sheet" /> : null,
}));

if (!Element.prototype.hasPointerCapture)
  Element.prototype.hasPointerCapture = () => false;
if (!Element.prototype.releasePointerCapture)
  Element.prototype.releasePointerCapture = () => {};
if (!Element.prototype.scrollIntoView)
  Element.prototype.scrollIntoView = () => {};

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

const renderGamePlayerInfo = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/5/player-info"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/player-info"
            element={<PlayerInfoContent />}
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
  isAdmin: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
  withdrawn: false,
  removable: false,
  nationPreferenceIds: [],
};

const classicalVariant = {
  id: "classical",
  name: "Classical",
  nations: Array.from({ length: 7 }, (_, index) => ({
    nationId: `nation-${index}`,
    name: `Nation ${index}`,
    color: "#cccccc",
    flagUrl: null,
    nonPlayable: false,
  })),
};

describe("PlayerInfoContent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVariantsData.mockReturnValue([classicalVariant]);
    mockCurrentPhaseData.mockReturnValue({ supplyCenters: [], units: [] });
    mockUserProfileData.mockReturnValue({ canCreateBotGames: true });
  });

  it("does not show a paused-game notice even when the game is paused", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      isPaused: true,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, civilDisorder: false }],
    });

    renderPlayerInfo();

    expect(
      screen.queryByText(/this game is (currently )?paused/i)
    ).not.toBeInTheDocument();
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
    expect(screen.getByText("(Admin)")).toBeInTheDocument();
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

    expect(screen.queryByText("(Admin)")).not.toBeInTheDocument();
  });

  it("shows a bot label for bot members only", () => {
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

    expect(screen.getAllByText("(Bot)")).toHaveLength(1);
  });

  it("shows an admin label for the member holding admin rights only", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice", isAdmin: true },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          isAdmin: false,
        },
      ],
    });

    renderPlayerInfo();

    expect(screen.getAllByText("(Admin)")).toHaveLength(1);
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
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          nation: null,
        },
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

  it("navigates to the profile when the card is clicked", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice" },
        { ...baseMember, id: 2, userId: 77, name: "Bob", isCurrentUser: false },
      ],
    });

    renderPlayerInfo();

    await user.click(screen.getByLabelText("View profile for Bob"));

    expect(mockNavigate).toHaveBeenCalledWith("/player/77");
  });

  it("does not link the chevron for a member with no profile to link to", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, userId: 1, name: "Alice" },
        {
          ...baseMember,
          id: 2,
          userId: null,
          name: "Anonymous",
          isCurrentUser: false,
        },
      ],
    });

    const { container } = renderPlayerInfo();

    expect(
      screen.queryByLabelText("View profile for Anonymous")
    ).not.toBeInTheDocument();
    expect(container.querySelectorAll(".lucide-chevron-right")).toHaveLength(1);
  });

  it("groups eliminated members into their own section", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice" },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          eliminated: true,
        },
      ],
    });

    renderPlayerInfo();

    expect(screen.getByText("Eliminated")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("ranks players by supply centres, then units, then their original order", () => {
    mockCurrentPhaseData.mockReturnValue({
      supplyCenters: [
        { nation: { name: "France" } },
        { nation: { name: "France" } },
        { nation: { name: "Germany" } },
        { nation: { name: "Germany" } },
        { nation: { name: "Italy" } },
        { nation: { name: "Italy" } },
        { nation: { name: "England" } },
      ],
      units: [
        { nation: { name: "France" } },
        { nation: { name: "Germany" } },
        { nation: { name: "Germany" } },
        { nation: { name: "Italy" } },
        { nation: { name: "Italy" } },
      ],
    });
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, userId: 1, name: "Alice", nation: "England" },
        { ...baseMember, id: 2, userId: 2, name: "Bob", nation: "France" },
        { ...baseMember, id: 3, userId: 3, name: "Carol", nation: "Germany" },
        { ...baseMember, id: 4, userId: 4, name: "Diana", nation: "Italy" },
      ],
    });

    renderPlayerInfo();

    expect(
      screen.getAllByRole("link").map(link => link.getAttribute("aria-label"))
    ).toEqual([
      "View profile for Carol",
      "View profile for Diana",
      "View profile for Bob",
      "View profile for Alice",
    ]);
  });

  it("dims eliminated and Civil Disorder players", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, userId: 1, name: "Alice", eliminated: true },
        {
          ...baseMember,
          id: 2,
          userId: 2,
          name: "Bob",
          nation: "France",
          civilDisorder: true,
        },
      ],
    });

    renderPlayerInfo();

    expect(
      screen.getByLabelText("View profile for Alice").parentElement
    ).toHaveClass("opacity-70");
    expect(
      screen.getByLabelText("View profile for Bob").parentElement
    ).toHaveClass("opacity-70");
  });

  it("shows Civil Disorder as a red badge without colouring either name", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        {
          ...baseMember,
          userId: 1,
          name: "Alice",
          civilDisorder: true,
        },
      ],
    });

    renderPlayerInfo();

    expect(screen.getByText("England")).not.toHaveClass("text-destructive");
    expect(screen.getByText("Alice")).not.toHaveClass("text-destructive");
    expect(screen.getByLabelText("Civil Disorder")).toHaveClass(
      "bg-destructive",
      "text-white"
    );
  });

  it("renders the player list actions below the list", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember }],
      playerListActions: [
        { key: "edit_nation_preferences", blockedReason: null },
        { key: "assign_nations", blockedReason: null },
      ],
    });

    renderPlayerInfo();

    expect(screen.getByTestId("action-list")).toHaveTextContent(
      "edit_nation_preferences,assign_nations"
    );
  });

  it("renders no actions when the player list offers none", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember }],
    });

    renderPlayerInfo();

    expect(screen.queryByTestId("action-list")).not.toBeInTheDocument();
  });

  it("does not render seat controls on the rows", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      canManage: true,
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice", isCurrentUser: false },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          civilDisorder: true,
          replaceable: true,
          removable: true,
        },
      ],
    });

    renderGamePlayerInfo();

    expect(screen.queryByRole("button", { name: /replace/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /invite replacement/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /remove/i })).not.toBeInTheDocument();
  });

  it("navigates to the member screen when a row is clicked inside a game", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, userId: 1, name: "Alice" },
        { ...baseMember, id: 2, userId: 77, name: "Bob", isCurrentUser: false },
      ],
    });

    renderGamePlayerInfo();

    await user.click(screen.getByLabelText("View details for Bob"));

    expect(mockNavigate).toHaveBeenCalledWith("/game/game-1/phase/5/member/2");
  });

  it("navigates to the member screen for anonymous, bot and former rows", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, userId: 1, name: "Alice" },
        { ...baseMember, id: 2, userId: null, name: "Anonymous", isCurrentUser: false },
        { ...baseMember, id: 3, userId: 101, name: "The Bear", isBot: true, isCurrentUser: false },
        { ...baseMember, id: 4, userId: 9, name: "Dan", kicked: true, isCurrentUser: false },
      ],
    });

    renderGamePlayerInfo();

    await user.click(screen.getByLabelText("View details for Anonymous"));
    await user.click(screen.getByLabelText("View details for The Bear"));
    await user.click(screen.getByLabelText("View details for Dan"));

    expect(mockNavigate).toHaveBeenNthCalledWith(1, "/game/game-1/phase/5/member/2");
    expect(mockNavigate).toHaveBeenNthCalledWith(2, "/game/game-1/phase/5/member/3");
    expect(mockNavigate).toHaveBeenNthCalledWith(3, "/game/game-1/phase/5/member/4");
  });

  it("links the game master to their member screen inside a game", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      gameMaster: { userId: 42, name: "Gina", picture: null },
      gameMasterMemberId: 900,
      members: [{ ...baseMember }],
    });

    renderGamePlayerInfo();

    expect(screen.getByRole("link", { name: "Gina" })).toHaveAttribute(
      "href",
      "/game/game-1/phase/5/member/900"
    );
  });

  it("dims and labels withdrawn players", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, userId: 1, name: "Alice" },
        {
          ...baseMember,
          id: 2,
          userId: 2,
          name: "Bob",
          nation: "France",
          isCurrentUser: false,
          withdrawn: true,
        },
      ],
    });

    renderPlayerInfo();

    expect(
      screen.getByLabelText("View profile for Bob").parentElement
    ).toHaveClass("opacity-70");
    expect(
      screen.getByLabelText("View profile for Alice").parentElement
    ).not.toHaveClass("opacity-70");
    expect(screen.getByLabelText("Withdrawn")).toBeInTheDocument();
    expect(screen.queryByLabelText("Civil Disorder")).not.toBeInTheDocument();
  });

  it("explains the player metrics with tooltips", async () => {
    const user = userEvent.setup();
    mockCurrentPhaseData.mockReturnValue({
      supplyCenters: [{ nation: { name: "England" } }],
      units: [{ nation: { name: "England" } }],
    });
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 2,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember, nmrExtensionsRemaining: 2 }],
    });

    renderPlayerInfo();

    expect(screen.getByLabelText("Supply centres: 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Units: 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Deadline extensions: 2")).toBeInTheDocument();

    await user.hover(screen.getByLabelText("Supply centres: 1"));
    await screen.findByRole("tooltip", { name: "Supply centres" });
    expect(
      document.querySelector('[data-slot="tooltip-content"]')
    ).toHaveAttribute("data-side", "bottom");
  });

  it("does not open the player profile when a metric tooltip is activated", () => {
    mockCurrentPhaseData.mockReturnValue({
      supplyCenters: [{ nation: { name: "England" } }],
      units: [],
    });
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember }],
    });

    renderPlayerInfo();

    const supplyCentres = screen.getByLabelText("Supply centres: 1");
    fireEvent.pointerDown(supplyCentres);
    fireEvent.click(supplyCentres);
    fireEvent.keyDown(supplyCentres, { key: "Enter" });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("groups completed solo results into Winner, Other players, and Eliminated", () => {
    const winner = {
      ...baseMember,
      id: 2,
      name: "Bob",
      nation: "France",
      isCurrentUser: false,
    };
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      nmrExtensionsAllowed: 0,
      victory: { type: "solo", members: [winner] },
      phases: [{ id: 1, status: "completed" }],
      members: [
        { ...baseMember, name: "Alice" },
        winner,
        {
          ...baseMember,
          id: 3,
          name: "Carol",
          nation: "Germany",
          isCurrentUser: false,
          eliminated: true,
        },
      ],
    });

    renderPlayerInfo();

    expect(screen.getByRole("heading", { name: "Winner" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Other players" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Eliminated" })
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Winner")).toBeInTheDocument();
    expect(screen.queryByText(/has won the game/i)).not.toBeInTheDocument();
  });

  it("labels shared winners as Drawn", () => {
    const alice = { ...baseMember, id: 1, name: "Alice" };
    const bob = {
      ...baseMember,
      id: 2,
      name: "Bob",
      nation: "France",
      isCurrentUser: false,
    };
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      nmrExtensionsAllowed: 0,
      victory: { type: "draw", members: [alice, bob] },
      phases: [{ id: 1, status: "completed" }],
      members: [alice, bob],
    });

    renderPlayerInfo();

    expect(screen.getByRole("heading", { name: "Drawn" })).toBeInTheDocument();
    expect(screen.getAllByLabelText("Drawn player")).toHaveLength(2);
    expect(document.querySelectorAll(".lucide-handshake")).toHaveLength(2);
    expect(document.querySelector(".lucide-trophy")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Other players" })
    ).not.toBeInTheDocument();
  });

  it("keeps the abandoned warning above abandoned-game Results", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "abandoned",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "completed" }],
      members: [{ ...baseMember }],
    });

    renderPlayerInfo();

    expect(
      screen.getByText("This game was abandoned due to inactivity.")
    ).toHaveClass("!text-foreground");
    expect(
      screen.getByRole("heading", { name: "Other players" })
    ).toBeInTheDocument();
    expect(
      document.querySelector(".lucide-triangle-alert")
    ).not.toBeInTheDocument();
  });

  it("collapses and expands the former players section", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice" },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          kicked: true,
        },
      ],
    });

    renderPlayerInfo();

    expect(screen.getByText("Bob")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Former players/ }));
    expect(screen.queryByText("Bob")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Former players/ }));
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("groups a kicked member under former players", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [
        { ...baseMember, id: 1, name: "Alice" },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          kicked: true,
          replaceable: true,
        },
      ],
    });

    renderPlayerInfo();

    expect(screen.getByText("Former players (1)")).toBeInTheDocument();
  });

  it("does not announce assigned nations while pending with a pin", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "pending" }],
      members: [
        { ...baseMember, id: 1, name: "Alice", nation: "England" },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          nation: null,
        },
      ],
    });

    renderPlayerInfo();

    expect(
      screen.queryByText(/the game master has assigned some nations/i)
    ).not.toBeInTheDocument();
  });

  it("names the assigned nation on the current user's seat while pending", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "pending" }],
      members: [{ ...baseMember, nation: "England" }],
    });

    renderPlayerInfo();

    expect(screen.getByRole("button", { name: /England/ })).toBeInTheDocument();
  });

  it("invites the current user to set preferences while pending", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "pending" }],
      members: [
        { ...baseMember, nation: null },
        {
          ...baseMember,
          id: 2,
          name: "Bob",
          isCurrentUser: false,
          nation: null,
        },
      ],
    });

    renderPlayerInfo();

    const seat = screen.getAllByRole("button", {
      name: /choose nation preferences/i,
    });
    expect(seat).toHaveLength(1);

    await user.click(seat[0]);

    expect(mockNavigate).toHaveBeenCalledWith("/nation-preference/game-1");
  });

  it("marks the current user's seat once preferences are provided", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "pending" }],
      members: [
        {
          ...baseMember,
          nation: null,
          nationPreferenceIds: ["nation-1", "nation-2"],
        },
      ],
    });

    renderPlayerInfo();

    expect(
      screen.getByRole("button", { name: /nation preferences provided/i })
    ).toBeInTheDocument();
  });

  it("does not offer nation preferences once the game is active", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "active" }],
      members: [{ ...baseMember }],
    });

    renderPlayerInfo();

    expect(
      screen.queryByRole("button", { name: /nation preferences/i })
    ).not.toBeInTheDocument();
  });

  it("links to nation assignment from the game master card when the game offers it", () => {
    mockUserProfileData.mockReturnValue({ canCreateBotGames: true, userId: 9 });
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "pending" }],
      gameMaster: { userId: 9, name: "GM", picture: null },
      members: [{ ...baseMember, isCurrentUser: false, nation: null }],
      actions: [{ key: "assign_nations", blockedReason: null }],
    });

    renderPlayerInfo();

    expect(screen.getByRole("link", { name: "Assign nations" })).toHaveAttribute(
      "href",
      "/nation-assignment/game-1"
    );
  });

  it("does not offer nation assignment to players", () => {
    mockUserProfileData.mockReturnValue({ canCreateBotGames: true, userId: 1 });
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "pending",
      nmrExtensionsAllowed: 0,
      victory: null,
      phases: [{ id: 1, status: "pending" }],
      gameMaster: { userId: 9, name: "GM", picture: null },
      members: [{ ...baseMember, nation: null }],
    });

    renderPlayerInfo();

    expect(
      screen.queryByRole("link", { name: /assign nations/i })
    ).not.toBeInTheDocument();
  });
});
