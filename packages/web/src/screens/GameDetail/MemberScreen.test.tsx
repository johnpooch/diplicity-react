import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  GameRetrieve,
  MemberDetail,
  PublicUserProfile,
  RatingPairingOutput,
  RatingResultOutput,
} from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MemberScreen } from "./MemberScreen";

let game: GameRetrieve;
let member: MemberDetail;
let rating: RatingResultOutput;

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
  marks: [],
};

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: game }),
  useGameMemberRetrieveSuspense: () => ({ data: member }),
  useGameMemberRatingRetrieveSuspense: () => ({ data: rating }),
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
  rated: false,
  ...overrides,
});

const buildPairing = (
  overrides: Partial<RatingPairingOutput> = {}
): RatingPairingOutput => ({
  id: 1,
  opponent: {
    id: 4,
    userId: 6,
    name: "John Smith",
    picture: null,
    isCurrentUser: false,
    isBot: false,
    nation: "France",
  },
  opponentRating: 1612.4,
  score: 1,
  change: 12.6,
  ...overrides,
});

const buildRating = (
  overrides: Partial<RatingResultOutput> = {}
): RatingResultOutput => ({
  id: 1,
  ratingBefore: 1530.2,
  ratingAfter: 1561.4,
  ratingChange: 31.2,
  protected: false,
  pairings: [buildPairing()],
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
    rating = buildRating();
  });

  it("shows the player's commitment", () => {
    renderScreen();

    expect(
      screen.getByRole("heading", { name: "Commitment" })
    ).toBeInTheDocument();
    expect(screen.getByText("+434")).toBeInTheDocument();
  });

  it("shows the player's conduct history", () => {
    renderScreen();

    expect(
      screen.getByRole("heading", { name: "Conduct history" })
    ).toBeInTheDocument();
    expect(screen.getByText("No bad conduct")).toBeInTheDocument();
  });

  it("hides commitment in an anonymous game", () => {
    game = buildGame({ anonymous: true });
    renderScreen();

    expect(
      screen.queryByRole("heading", { name: "Commitment" })
    ).not.toBeInTheDocument();
  });

  it("hides conduct history in an anonymous game", () => {
    game = buildGame({ anonymous: true });
    renderScreen();

    expect(
      screen.queryByRole("heading", { name: "Conduct history" })
    ).not.toBeInTheDocument();
  });

  it("hides commitment for a member without a user", () => {
    member = buildMember({ userId: null });
    renderScreen();

    expect(
      screen.queryByRole("heading", { name: "Commitment" })
    ).not.toBeInTheDocument();
  });

  it("shows the rating before and after a rated game", () => {
    member = buildMember({ rated: true });
    renderScreen();

    expect(screen.getByRole("heading", { name: "Rating" })).toBeInTheDocument();
    expect(screen.getByText("1,530")).toBeInTheDocument();
    expect(screen.getByText("1,561")).toBeInTheDocument();
    expect(screen.getByText("+31")).toBeInTheDocument();
  });

  it("shows a row per opponent in the rating breakdown", () => {
    member = buildMember({ rated: true });
    rating = buildRating({
      pairings: [
        buildPairing(),
        buildPairing({
          id: 2,
          opponent: { ...buildPairing().opponent, id: 5, nation: "Germany" },
          score: 0.5,
          change: -1.2,
        }),
        buildPairing({
          id: 3,
          opponent: { ...buildPairing().opponent, id: 6, nation: "Russia" },
          score: 0,
          change: -8.4,
        }),
      ],
    });
    renderScreen();

    expect(
      screen.getByRole("heading", { name: "Rating breakdown" })
    ).toBeInTheDocument();
    expect(screen.getByText("Beat France")).toBeInTheDocument();
    expect(screen.getByText("Tied with Germany")).toBeInTheDocument();
    expect(screen.getByText("Lost to Russia")).toBeInTheDocument();
    expect(screen.getAllByText("John Smith · 1,612")).toHaveLength(3);
    expect(screen.getByText("+13")).toBeInTheDocument();
    expect(screen.getByText("−1")).toBeInTheDocument();
    expect(screen.getByText("−8")).toBeInTheDocument();
  });

  it("tells a protected replacement their rating can only go up", () => {
    member = buildMember({ rated: true });
    rating = buildRating({
      ratingAfter: 1530.2,
      ratingChange: 0,
      protected: true,
      pairings: [buildPairing({ score: 0, change: -9.8 })],
    });
    renderScreen();

    expect(
      screen.getByText(
        "A replacement's rating can only go up. This result would have lowered it, so it was not applied."
      )
    ).toBeInTheDocument();
  });

  it("shows the rating between commitment and conduct history", () => {
    member = buildMember({ rated: true });
    renderScreen();

    expect(
      screen
        .getAllByRole("heading")
        .map(heading => heading.textContent)
        .filter(name =>
          ["Commitment", "Rating", "Rating breakdown", "Conduct history"].includes(
            name ?? ""
          )
        )
    ).toEqual(["Commitment", "Rating", "Rating breakdown", "Conduct history"]);
  });

  it("hides the rating for an unrated member", () => {
    renderScreen();

    expect(
      screen.queryByRole("heading", { name: "Rating" })
    ).not.toBeInTheDocument();
  });
});
