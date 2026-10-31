import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { GameRetrieve, Member } from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { PlayerInfoContent } from "./PlayerInfoContent";

let game: GameRetrieve;

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: game }),
  useGamePhaseRetrieve: () => ({ data: undefined }),
  useUserRetrieveSuspense: () => ({ data: { canCreateBotGames: false } }),
}));

vi.mock("@/hooks/useGameVariant", () => ({ useGameVariant: () => undefined }));

vi.mock("@/components/ActionList", () => ({
  ActionList: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

vi.mock("@/components/GameStatusAlerts", () => ({
  GameStatusAlerts: () => null,
}));

const buildMember = (overrides: Partial<Member> = {}): Member => ({
  id: 1,
  userId: 1,
  name: "Jane Doe",
  picture: null,
  isCurrentUser: false,
  isBot: false,
  nation: null,
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  isAdmin: false,
  nmrExtensionsRemaining: 1,
  civilDisorder: false,
  withdrawn: false,
  seekingReplacement: false,
  replaceable: false,
  seatConfirmed: null,
  removable: false,
  nationPreferenceIds: [],
  commitmentTotal: 0,
  commitmentBand: "neutral",
  ...overrides,
});

const buildGame = (overrides: Partial<GameRetrieve> = {}): GameRetrieve => ({
  id: "g1",
  name: "Concert of Europe",
  status: "pending",
  createdAt: "2026-10-01T00:00:00Z",
  canJoin: false,
  canLeave: false,
  canWithdraw: false,
  isFirstYear: false,
  canDelete: false,
  canManage: false,
  canCreateChannel: false,
  gameMaster: null,
  gameMasterMemberId: null,
  phases: [],
  currentPhaseId: null,
  members: [],
  sandbox: false,
  victory: null,
  variantId: "classical",
  phaseConfirmed: false,
  orderStatus: null,
  memberStatus: null,
  movementPhaseDuration: "24 hours",
  retreatPhaseDuration: null,
  showShortGameJoinWarning: false,
  private: false,
  anonymous: false,
  isPaused: false,
  pausedAt: null,
  nmrExtensionsAllowed: 1,
  deadlineMode: "duration",
  fixedDeadlineTime: null,
  fixedDeadlineTimezone: null,
  movementFrequency: null,
  retreatFrequency: null,
  pressType: "full_press",
  commitmentRequirement: "none",
  joinBlockedReason: null,
  musterRequired: false,
  musterDeadline: null,
  musterStatus: null,
  totalUnreadMessageCount: 0,
  actions: [],
  playerListActions: [],
  ...overrides,
});

const renderContent = () =>
  render(
    <TooltipProvider>
      <MemoryRouter initialEntries={["/game-info/g1"]}>
        <Routes>
          <Route path="/game-info/:gameId" element={<PlayerInfoContent />} />
        </Routes>
      </MemoryRouter>
    </TooltipProvider>
  );

const rowFor = (name: string) =>
  screen.getByRole("link", { name: `View profile for ${name}` });

describe("PlayerInfoContent", () => {
  beforeEach(() => {
    game = buildGame({
      members: [
        buildMember({ id: 1, userId: 1, name: "Alice", commitmentTotal: 48 }),
        buildMember({ id: 2, userId: 2, name: "Bob", commitmentTotal: -14 }),
        buildMember({ id: 3, userId: 3, name: "Carol", commitmentTotal: 0 }),
      ],
    });
  });

  it("shows each player's commitment total just before the chevron", () => {
    renderContent();

    const score = within(rowFor("Alice")).getByLabelText("Commitment: 48");
    expect(score).toHaveTextContent("+48");
    expect(score.nextElementSibling?.tagName.toLowerCase()).toBe("svg");
  });

  it("colours positive totals green, negative totals red and zero plainly", () => {
    renderContent();

    const positive = within(rowFor("Alice")).getByLabelText("Commitment: 48");
    const negative = within(rowFor("Bob")).getByLabelText("Commitment: -14");
    const zero = within(rowFor("Carol")).getByLabelText("Commitment: 0");

    expect(positive).toHaveClass("text-emerald-700");
    expect(negative).toHaveTextContent("−14");
    expect(negative).toHaveClass("text-red-700");
    expect(zero).toHaveTextContent("0");
    expect(zero).not.toHaveClass("text-emerald-700");
    expect(zero).not.toHaveClass("text-red-700");
  });

  it("shows commitment totals while mustering", () => {
    game = { ...game, status: "mustering" };
    renderContent();

    expect(
      within(rowFor("Alice")).getByLabelText("Commitment: 48")
    ).toBeInTheDocument();
  });

  it("shows no commitment when the API omits it", () => {
    game = buildGame({
      anonymous: true,
      members: [
        buildMember({
          id: 1,
          userId: 1,
          name: "Anonymous",
          commitmentTotal: null,
          commitmentBand: null,
        }),
        buildMember({
          id: 2,
          userId: 2,
          name: "Jane Doe",
          isCurrentUser: true,
          commitmentTotal: null,
          commitmentBand: null,
        }),
      ],
    });
    renderContent();

    expect(screen.queryByLabelText(/^Commitment:/)).not.toBeInTheDocument();
  });

  it("shows no commitment on the game master card", () => {
    game = {
      ...game,
      gameMaster: { userId: 9, name: "Grace", picture: null },
      gameMasterMemberId: 9,
    };
    renderContent();

    const gameMasterSection = screen
      .getByRole("heading", { name: "Game master" })
      .closest("section");
    expect(gameMasterSection).not.toBeNull();
    expect(
      within(gameMasterSection as HTMLElement).queryByLabelText(/^Commitment:/)
    ).not.toBeInTheDocument();
  });
});
