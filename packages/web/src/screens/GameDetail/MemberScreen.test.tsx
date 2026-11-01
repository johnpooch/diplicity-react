import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  GameRetrieve,
  MemberDetail,
  PublicUserProfile,
} from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MemberScreen } from "./MemberScreen";

let game: GameRetrieve;
let member: MemberDetail;

const profile: PublicUserProfile = {
  id: 5,
  name: "Jane Doe",
  picture: null,
  createdAt: "2025-01-15T00:00:00Z",
  totalGames: 15,
  activeGames: 3,
  commitmentTotal: 434,
  commitmentBand: "neutral",
  commitmentSquares: [],
};

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: game }),
  useGameMemberRetrieveSuspense: () => ({ data: member }),
  useUsersRetrieveSuspense: () => ({ data: profile }),
}));

vi.mock("@/hooks/useGameVariant", () => ({ useGameVariant: () => undefined }));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

vi.mock("@/components/ActionList", () => ({
  ActionList: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

const buildMember = (overrides: Partial<MemberDetail> = {}): MemberDetail => ({
  id: 3,
  userId: 5,
  name: "Jane Doe",
  picture: null,
  isCurrentUser: false,
  isBot: false,
  isAdmin: false,
  nation: "England",
  participationStatus: "playing",
  supplyCenterCount: null,
  unitCount: null,
  nmrExtensionsRemaining: 1,
  nmrExtensionsAllowed: 1,
  nationPreferences: null,
  actions: [],
  canReport: false,
  alreadyReported: false,
  ...overrides,
});

const buildGame = (overrides: Partial<GameRetrieve> = {}): GameRetrieve => ({
  id: "g1",
  name: "Concert of Europe",
  status: "active",
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

const renderScreen = () =>
  render(
    <TooltipProvider>
      <MemoryRouter initialEntries={["/game/g1/phase/7/member/3"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/member/:memberId"
            element={<MemberScreen />}
          />
        </Routes>
      </MemoryRouter>
    </TooltipProvider>
  );

describe("MemberScreen", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  beforeEach(() => {
    game = buildGame();
    member = buildMember();
  });

  it("shows the player's commitment", () => {
    renderScreen();

    expect(
      screen.getByRole("heading", { name: "Commitment" })
    ).toBeInTheDocument();
    expect(screen.getByText("+434")).toBeInTheDocument();
  });

  it("hides commitment in an anonymous game", () => {
    game = buildGame({ anonymous: true });
    renderScreen();

    expect(
      screen.queryByRole("heading", { name: "Commitment" })
    ).not.toBeInTheDocument();
  });

  it("hides commitment for a member without a user", () => {
    member = buildMember({ userId: null });
    renderScreen();

    expect(
      screen.queryByRole("heading", { name: "Commitment" })
    ).not.toBeInTheDocument();
  });
});
