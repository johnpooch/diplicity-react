import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ActionList } from "./ActionList";

const mockNavigate = vi.fn();
vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockGameData = vi.fn();
const mockJoin = vi.fn();
const mockMuster = vi.fn();
const mockLeave = vi.fn();
const mockWithdraw = vi.fn();
const mockPause = vi.fn();
const mockUnpause = vi.fn();
const mockExtendDeadline = vi.fn();
const mockKick = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useGameMemberJoinCreate: () => ({ mutateAsync: mockJoin, isPending: false }),
  useGameMusterCreate: () => ({ mutateAsync: mockMuster, isPending: false }),
  useGameLeaveDestroy: () => ({ mutateAsync: mockLeave, isPending: false }),
  useGameMemberWithdrawPartialUpdate: () => ({ mutateAsync: mockWithdraw, isPending: false }),
  useGamePauseUpdate: () => ({ mutateAsync: mockPause, isPending: false }),
  useGameUnpausePartialUpdate: () => ({ mutateAsync: mockUnpause, isPending: false }),
  useGameExtendDeadlineUpdate: () => ({ mutateAsync: mockExtendDeadline, isPending: false }),
  useGameKickDestroy: () => ({ mutateAsync: mockKick, isPending: false }),
  getGameAddableUserListQueryKey: () => ["addable"],
  getGameMemberRetrieveQueryKey: () => ["member"],
  getGamePhaseRetrieveQueryKey: () => ["phase"],
  getGamePhasesListQueryKey: () => ["phases"],
  getGameRetrieveQueryKey: () => ["game"],
  getGamesListQueryKey: () => ["games"],
  DurationEnum: {
    "1_hour": "1 hour",
    "24_hours": "24 hours",
    "48_hours": "48 hours",
  },
}));

const mockCheckNotificationPermission = vi.fn();
vi.mock("@/hooks/useCheckNotificationPermission", () => ({
  useCheckNotificationPermission: () => mockCheckNotificationPermission,
}));

const mockCopyLink = vi.fn();
vi.mock("@/utils/copyLink", () => ({
  copyLink: (path: string) => mockCopyLink(path),
}));

const mockToastError = vi.fn();
vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: (message: string) => mockToastError(message) },
}));

if (!Element.prototype.hasPointerCapture)
  Element.prototype.hasPointerCapture = () => false;
if (!Element.prototype.releasePointerCapture)
  Element.prototype.releasePointerCapture = () => {};
if (!Element.prototype.scrollIntoView)
  Element.prototype.scrollIntoView = () => {};

const member = { id: 7, name: "Bob", nation: "France" };

type ActionListProps = React.ComponentProps<typeof ActionList>;

const renderActions = (
  actions: ActionListProps["actions"],
  props: Partial<ActionListProps> = {}
) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <ActionList gameId="game-1" actions={actions} {...props} />
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ActionList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGameData.mockReturnValue({
      sandbox: false,
      showShortGameJoinWarning: false,
    });
  });

  it("renders the actions in the order it receives them", () => {
    renderActions([
      { key: "withdraw", blockedReason: null },
      { key: "pause", blockedReason: null },
      { key: "extend_deadline", blockedReason: null },
    ]);

    expect(screen.getAllByRole("button").map(button => button.textContent)).toEqual([
      "Withdraw from game",
      "Pause game",
      "Extend deadline",
    ]);
  });

  it("renders a blocked action disabled with its reason beneath it", () => {
    renderActions(
      [{ key: "remove_from_game", blockedReason: "no_missed_orders" }],
      { member }
    );

    expect(screen.getByRole("button", { name: /remove player/i })).toBeDisabled();
    expect(
      screen.getByText("This player has not missed any orders.")
    ).toBeInTheDocument();
  });

  it("explains a takeover blocked by commitment", () => {
    renderActions([{ key: "take_over", blockedReason: "commitment_too_low" }], {
      member,
    });

    expect(screen.getByRole("button", { name: /take over seat/i })).toBeDisabled();
    expect(
      screen.getByText("Your commitment rating does not meet this game's requirement.")
    ).toBeInTheDocument();
  });

  it("confirms before removing a player from an active game", async () => {
    const user = userEvent.setup();
    renderActions([{ key: "remove_from_game", blockedReason: null }], { member });

    await user.click(screen.getByRole("button", { name: /remove player/i }));

    expect(mockKick).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Their orders for this phase are discarded/)
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Remove" }));

    expect(mockKick).toHaveBeenCalledWith({ gameId: "game-1", memberId: 7 });
  });

  it("leaves the member screen after removing a player from the lobby", async () => {
    const user = userEvent.setup();
    const onMemberGone = vi.fn();
    renderActions([{ key: "remove_from_lobby", blockedReason: null }], {
      member,
      onMemberGone,
    });

    await user.click(screen.getByRole("button", { name: /remove player/i }));

    expect(screen.getByText("Bob is removed from the lobby. They can join again while the game has an open seat.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Remove" }));

    expect(mockKick).toHaveBeenCalledWith({ gameId: "game-1", memberId: 7 });
    expect(onMemberGone).toHaveBeenCalled();
  });

  it("does not leave the game when the confirmation is cancelled", async () => {
    const user = userEvent.setup();
    renderActions([{ key: "leave", blockedReason: null }]);

    await user.click(screen.getByRole("button", { name: /leave game/i }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(mockLeave).not.toHaveBeenCalled();
  });

  it("confirms withdrawal with the withdrawal explanation", async () => {
    const user = userEvent.setup();
    renderActions([{ key: "withdraw", blockedReason: null }]);

    await user.click(screen.getByRole("button", { name: /withdraw from game/i }));

    expect(
      screen.getByText(/Your seat will be left for another player to claim/)
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Withdraw" }));

    expect(mockWithdraw).toHaveBeenCalledWith({ gameId: "game-1" });
  });

  it("pauses and resumes without a confirmation", async () => {
    const user = userEvent.setup();
    renderActions([
      { key: "pause", blockedReason: null },
      { key: "unpause", blockedReason: null },
    ]);

    await user.click(screen.getByRole("button", { name: /pause game/i }));
    await user.click(screen.getByRole("button", { name: /resume game/i }));

    expect(mockPause).toHaveBeenCalledWith({ gameId: "game-1" });
    expect(mockUnpause).toHaveBeenCalledWith({ gameId: "game-1" });
  });

  it("extends the deadline with the default duration", async () => {
    const user = userEvent.setup();
    renderActions([{ key: "extend_deadline", blockedReason: null }]);

    await user.click(screen.getByRole("button", { name: /extend deadline/i }));
    await user.click(screen.getByRole("button", { name: "Extend" }));

    expect(mockExtendDeadline).toHaveBeenCalledWith({
      gameId: "game-1",
      data: { duration: "24 hours" },
    });
  });

  it("confirms the seat", async () => {
    const user = userEvent.setup();
    renderActions([{ key: "confirm_seat", blockedReason: null }]);

    await user.click(screen.getByRole("button", { name: /confirm seat/i }));

    expect(mockMuster).toHaveBeenCalledWith({ gameId: "game-1" });
  });

  it("warns before joining a game with short phases", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue({ sandbox: false, showShortGameJoinWarning: true });
    renderActions([{ key: "join", blockedReason: null }]);

    await user.click(screen.getByRole("button", { name: /join game/i }));

    expect(mockJoin).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Join" }));

    expect(mockJoin).toHaveBeenCalledWith({ gameId: "game-1" });
  });

  it("navigates for actions that open another screen", async () => {
    const user = userEvent.setup();
    renderActions(
      [
        { key: "take_over", blockedReason: null },
        { key: "edit_nation_preferences", blockedReason: null },
        { key: "assign_nations", blockedReason: null },
      ],
      { member }
    );

    await user.click(screen.getByRole("button", { name: /take over seat/i }));
    await user.click(screen.getByRole("button", { name: /nation preferences/i }));
    await user.click(screen.getByRole("button", { name: /assign nations/i }));

    expect(mockNavigate).toHaveBeenNthCalledWith(1, "/game/game-1/replace/7");
    expect(mockNavigate).toHaveBeenNthCalledWith(2, "/nation-preference/game-1");
    expect(mockNavigate).toHaveBeenNthCalledWith(3, "/nation-assignment/game-1");
  });

  it("copies the replacement link", async () => {
    const user = userEvent.setup();
    renderActions([{ key: "share_replacement_link", blockedReason: null }], {
      member,
    });

    await user.click(screen.getByRole("button", { name: /invite replacement/i }));

    expect(mockCopyLink).toHaveBeenCalledWith("/game/game-1/replace/7");
  });

  it("reports a failed action", async () => {
    const user = userEvent.setup();
    mockPause.mockRejectedValue(new Error("nope"));
    renderActions([{ key: "pause", blockedReason: null }]);

    await user.click(screen.getByRole("button", { name: /pause game/i }));

    expect(mockToastError).toHaveBeenCalledWith("Failed to pause game");
  });
});
