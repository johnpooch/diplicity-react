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
  useGameRetrieveSuspense: () => ({ data: { actions: [], ...mockGameData() } }),
  useUserRetrieveSuspense: () => ({ data: mockUserProfileData() }),
  useGamePauseUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameUnpausePartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameExtendDeadlineUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameCloneToSandboxCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameKickDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameLeaveDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameMemberJoinCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameMemberWithdrawPartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameMusterCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDevicesCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  getDevicesListQueryKey: () => ["devices"],
  getGameAddableUserListQueryKey: () => ["addable"],
  getGameMemberRetrieveQueryKey: () => ["member"],
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
      <MemoryRouter initialEntries={["/game-info/game-1"]}>
        <Routes>
          <Route path="/game-info/:gameId" element={<GameInfoContent />} />
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

    expect(mockNavigate).toHaveBeenCalledWith("/nation-preference/game-1");
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

describe("GameInfoContent paused notice", () => {
  it("tells everyone the game is paused", () => {
    mockUserProfileData.mockReturnValue({ userId: 1 });
    mockGameData.mockReturnValue({
      ...mockActiveGames[0],
      isPaused: true,
      members: [{ ...mockMembers[6], isCurrentUser: true, nation: "Austria" }],
    });

    renderGameInfo();

    expect(
      screen.getByText("This game is currently paused.")
    ).toBeInTheDocument();
    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
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

