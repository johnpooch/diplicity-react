import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";

import { GameInfoContent } from "./GameInfoContent";
import { mockPendingGames, mockActiveGames, mockMembers } from "@/mocks/legacy";

const mockNavigate = vi.fn();
vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockGameData = vi.fn();
const mockUserProfileData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useUserRetrieveSuspense: () => ({ data: mockUserProfileData() }),
  useGamePauseUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameUnpausePartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameExtendDeadlineUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameCloneToSandboxCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  getGameRetrieveQueryKey: () => ["game"],
  getGamesListQueryKey: () => ["games"],
  getGamePhasesListQueryKey: () => ["phases"],
  getGamePhaseRetrieveQueryKey: () => ["phase"],
  DurationEnum: {
    "1_hour": "1 hour",
    "2_hours": "2 hours",
    "4_hours": "4 hours",
    "8_hours": "8 hours",
    "12_hours": "12 hours",
    "24_hours": "24 hours",
    "48_hours": "48 hours",
    "3_days": "3 days",
    "4_days": "4 days",
    "1_week": "1 week",
    "2_weeks": "2 weeks",
  },
  useVariantsListSuspense: () => ({
    data: [
      {
        id: "Classical",
        name: "Classical",
        nations: [],
        templatePhase: { season: "Spring", year: 1901, type: "Movement" },
      },
    ],
  }),
  useVariantsRetrieve: () => ({ data: undefined }),
}));

vi.mock("@/components/MapView", () => ({
  MapView: () => <div data-testid="map-preview" />,
}));

const renderGameInfo = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/game-info"]}>
        <Routes>
          <Route path="/game/:gameId/game-info" element={<GameInfoContent />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

const pendingGameFor = (overrides: Record<string, unknown>) => ({
  ...mockPendingGames[0],
  members: [{ ...mockMembers[6], isCurrentUser: true, nation: null, ...overrides }],
});

describe("GameInfoContent nation preference alert", () => {
  it("asks a player who has not chosen to set preferences", async () => {
    const user = userEvent.setup();
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue(pendingGameFor({}));

    renderGameInfo();

    expect(
      screen.getByText("You have not chosen which nations you want to play.")
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Set Nation Preferences" }));

    expect(mockNavigate).toHaveBeenCalledWith("/game/game-1/nation-preference");
  });

  it("confirms that a player has provided preferences", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue(
      pendingGameFor({ nationPreferenceIds: ["austria", "england", "france"] })
    );

    renderGameInfo();

    expect(
      screen.getByText("You have provided nation preferences.")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Edit Preferences" })
    ).toBeInTheDocument();
  });

  it("explains a nation assigned by the game master and offers no edit", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue(pendingGameFor({ nation: "Austria" }));

    renderGameInfo();

    expect(
      screen.getByText("The Game Master assigned you Austria.")
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Preferences/ })
    ).not.toBeInTheDocument();
  });

  it("is not shown to a non-member", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockPendingGames[0],
      members: [{ ...mockMembers[0], isCurrentUser: false, nation: null }],
    });

    renderGameInfo();

    expect(
      screen.queryByRole("button", { name: /Preferences/ })
    ).not.toBeInTheDocument();
  });

  it("is not shown once the game is active", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockActiveGames[0],
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: "Austria" }],
    });

    renderGameInfo();

    expect(
      screen.queryByText(/nations you want to play/)
    ).not.toBeInTheDocument();
  });
});

describe("GameInfoContent nation assignment alert", () => {
  it("offers nation assignment to the game master while pending", () => {
    mockUserProfileData.mockReturnValue({ userId: 9 });
    mockGameData.mockReturnValue({
      ...mockPendingGames[0],
      gameMaster: { userId: 9, name: "GM", picture: null },
      members: [{ ...mockMembers[6], isCurrentUser: false, nation: null }],
    });

    renderGameInfo();

    expect(
      screen.getByRole("button", { name: /assign nations/i })
    ).toBeInTheDocument();
  });

  it("does not offer nation assignment to players", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockPendingGames[0],
      gameMaster: { userId: 9, name: "GM", picture: null },
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: null }],
    });

    renderGameInfo();

    expect(
      screen.queryByRole("button", { name: /assign nations/i })
    ).not.toBeInTheDocument();
  });
});

describe("GameInfoContent admin actions", () => {
  it("shows Pause and Extend deadline to a manager of an active, unpaused game", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockActiveGames[0],
      canManage: true,
      isPaused: false,
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: "Austria" }],
    });

    renderGameInfo();

    expect(screen.getByRole("button", { name: /pause/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /extend deadline/i })
    ).toBeInTheDocument();
  });

  it("shows Resume to a manager of a paused game, still under the Admin title", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockActiveGames[0],
      canManage: true,
      isPaused: true,
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: "Austria" }],
    });

    renderGameInfo();

    expect(screen.getByRole("button", { name: /resume/i })).toBeInTheDocument();
    expect(screen.getByText("Admin")).toBeInTheDocument();
    expect(screen.getByText("Paused")).toBeInTheDocument();
  });

  it("is not shown to a player who cannot manage the game", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockActiveGames[0],
      canManage: false,
      isPaused: false,
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: "Austria" }],
    });

    renderGameInfo();

    expect(
      screen.queryByRole("button", { name: /pause/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /extend deadline/i })
    ).not.toBeInTheDocument();
  });
});

describe("GameInfoContent clone to sandbox", () => {
  it("is shown to any player of an active, non-sandbox game", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockActiveGames[0],
      canManage: false,
      sandbox: false,
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: "Austria" }],
    });

    renderGameInfo();

    expect(
      screen.getByRole("button", { name: /clone to sandbox/i })
    ).toBeInTheDocument();
  });

  it("is not shown for a sandbox game", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockActiveGames[0],
      canManage: false,
      sandbox: true,
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: "Austria" }],
    });

    renderGameInfo();

    expect(
      screen.queryByRole("button", { name: /clone to sandbox/i })
    ).not.toBeInTheDocument();
  });

  it("is not shown for a pending game", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue(
      pendingGameFor({ isCurrentUser: true, nation: null })
    );

    renderGameInfo();

    expect(
      screen.queryByRole("button", { name: /clone to sandbox/i })
    ).not.toBeInTheDocument();
  });
});

describe("GameInfoContent commitment-locked message", () => {
  it("tells a commitment-locked viewer why they can't join, in the pending status alert", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockPendingGames[0],
      status: "pending",
      canJoin: true,
      canLeave: false,
      canManage: false,
      commitmentEligibility: "committed_locked",
      members: [],
    });

    renderGameInfo();

    expect(
      screen.getByText(
        "You can't join because you don't meet the commitment requirements."
      )
    ).toBeInTheDocument();
  });

  it("is not shown when the viewer can actually join", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockPendingGames[0],
      status: "pending",
      canJoin: true,
      canLeave: false,
      canManage: false,
      commitmentEligibility: "eligible",
      members: [],
    });

    renderGameInfo();

    expect(
      screen.queryByText(/don't meet the commitment requirements/)
    ).not.toBeInTheDocument();
  });
});
