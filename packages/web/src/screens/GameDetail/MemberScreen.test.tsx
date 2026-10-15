import { render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { MemberScreen } from "./MemberScreen";

const mockMemberData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { id: "game-1", variantId: "classical" },
  }),
  useGameMemberRetrieveSuspense: () => ({ data: mockMemberData() }),
  useVariantsListSuspense: () => ({ data: [] }),
  useVariantsRetrieve: () => ({ data: undefined }),
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

interface MockActionListProps {
  actions: { key: string; blockedReason: string | null }[];
  children?: React.ReactNode;
}

vi.mock("@/components/ActionList", () => ({
  ActionList: ({ actions, children }: MockActionListProps) => (
    <>
      <div data-testid="action-list">
        {actions.map(action => action.key).join(",")}
      </div>
      {children}
    </>
  ),
}));

const renderMemberScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/5/member/7"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/member/:memberId"
            element={<MemberScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

const baseMember = {
  id: 7,
  userId: 20,
  name: "Bob",
  picture: null,
  isCurrentUser: false,
  isBot: false,
  commitment: "high",
  isAdmin: false,
  nation: "France",
  participationStatus: "playing",
  supplyCenterCount: 5,
  unitCount: 4,
  nmrExtensionsRemaining: 1,
  nmrExtensionsAllowed: 2,
  nationPreferences: null,
  actions: [],
};

const rowValue = (label: string) =>
  within(screen.getByText(label).closest("div.flex") as HTMLElement)
    .getAllByText(/./)
    .at(-1)?.textContent;

describe("MemberScreen", () => {
  beforeEach(() => {
    mockMemberData.mockReturnValue(baseMember);
  });

  it("titles the screen Player details", async () => {
    renderMemberScreen();

    expect(await screen.findByText("Player details")).toBeInTheDocument();
  });

  it("shows the member's place in the game", async () => {
    renderMemberScreen();

    expect(await screen.findByText("In this game")).toBeInTheDocument();
    expect(rowValue("Nation")).toBe("France");
    expect(rowValue("Participation status")).toBe("Playing");
    expect(rowValue("Deadline extensions")).toBe("1 of 2 remaining");
    expect(screen.getByLabelText("Supply centres: 5")).toBeInTheDocument();
    expect(screen.getByLabelText("Units: 4")).toBeInTheDocument();
  });

  it.each([
    ["game_master", "Game master"],
    ["replaced", "Replaced"],
    ["removed", "Removed"],
    ["withdrawn", "Withdrawn"],
    ["won", "Won"],
    ["drew", "Drew"],
    ["eliminated", "Eliminated"],
    ["civil_disorder", "Civil disorder"],
    ["seat_unconfirmed", "Seat not confirmed"],
    ["seat_confirmed", "Seat confirmed"],
    ["joined", "Joined"],
    ["playing", "Playing"],
  ])("labels the %s participation status", async (participationStatus, label) => {
    mockMemberData.mockReturnValue({ ...baseMember, participationStatus });

    renderMemberScreen();

    await screen.findByText("In this game");
    expect(rowValue("Participation status")).toBe(label);
  });

  it("shows only the participation status for a game master", async () => {
    mockMemberData.mockReturnValue({
      ...baseMember,
      nation: null,
      participationStatus: "game_master",
      supplyCenterCount: null,
      unitCount: null,
    });

    renderMemberScreen();

    await screen.findByText("In this game");
    expect(screen.queryByText("Nation")).not.toBeInTheDocument();
    expect(screen.queryByText("Deadline extensions")).not.toBeInTheDocument();
    expect(screen.getAllByText("Game master")).toHaveLength(2);
  });

  it("marks an unassigned nation", async () => {
    mockMemberData.mockReturnValue({
      ...baseMember,
      nation: null,
      participationStatus: "joined",
      supplyCenterCount: null,
      unitCount: null,
    });

    renderMemberScreen();

    await screen.findByText("In this game");
    expect(rowValue("Nation")).toBe("Unassigned");
    expect(screen.queryByLabelText(/Supply centres/)).not.toBeInTheDocument();
  });

  it("omits deadline extensions for a game without them", async () => {
    mockMemberData.mockReturnValue({ ...baseMember, nmrExtensionsAllowed: 0 });

    renderMemberScreen();

    await screen.findByText("In this game");
    expect(screen.queryByText("Deadline extensions")).not.toBeInTheDocument();
  });

  it("links the player card to the profile", async () => {
    renderMemberScreen();

    expect(
      await screen.findByRole("link", { name: "View profile for Bob" })
    ).toHaveAttribute("href", "/game/game-1/phase/5/player/20?member=7");
  });

  it("does not link an anonymous member and shows the nation as the title", async () => {
    mockMemberData.mockReturnValue({
      ...baseMember,
      userId: null,
      name: "Anonymous",
    });

    renderMemberScreen();

    await screen.findByText("In this game");
    expect(screen.queryByRole("link", { name: /View profile/ })).not.toBeInTheDocument();
    expect(screen.getAllByText("France")).not.toHaveLength(0);
    expect(screen.getByText("Anonymous")).toBeInTheDocument();
  });

  it("shows nation preferences when the response carries them", async () => {
    mockMemberData.mockReturnValue({
      ...baseMember,
      isCurrentUser: true,
      nation: null,
      participationStatus: "joined",
      nationPreferences: ["France", "England"],
    });

    renderMemberScreen();

    expect(await screen.findByText("Your settings")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Nation preferences/ })
    ).toHaveAttribute("href", "/game/game-1/phase/5/nation-preference");
    expect(screen.getByText("France, England")).toBeInTheDocument();
  });

  it("omits the settings group without nation preferences", async () => {
    renderMemberScreen();

    await screen.findByText("In this game");
    expect(screen.queryByText("Your settings")).not.toBeInTheDocument();
  });

  it("renders the actions in the order the response gives them", async () => {
    mockMemberData.mockReturnValue({
      ...baseMember,
      actions: [
        { key: "share_replacement_link", blockedReason: null },
        { key: "remove_from_game", blockedReason: "no_missed_orders" },
      ],
    });

    renderMemberScreen();

    expect(await screen.findByTestId("action-list")).toHaveTextContent(
      "share_replacement_link,remove_from_game"
    );
  });
});
