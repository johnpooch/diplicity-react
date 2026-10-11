import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { toast } from "sonner";
import { GameDropdownMenu } from "./GameDropdownMenu";

const mockWithdrawMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameLeaveDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameDeleteDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameMemberWithdrawPartialUpdate: () => ({
    mutateAsync: mockWithdrawMutateAsync,
    isPending: false,
  }),
  getGamesListQueryKey: () => ["games"],
  getGameRetrieveQueryKey: (gameId: string) => ["game", gameId],
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

if (!Element.prototype.hasPointerCapture)
  Element.prototype.hasPointerCapture = () => false;
if (!Element.prototype.releasePointerCapture)
  Element.prototype.releasePointerCapture = () => {};
if (!Element.prototype.scrollIntoView)
  Element.prototype.scrollIntoView = () => {};

const baseGame = {
  id: "game-1",
  sandbox: false,
  canLeave: false,
  canWithdraw: true,
  canDelete: false,
  status: "active",
};

const renderMenu = (overrides = {}) => {
  const queryClient = new QueryClient();
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <GameDropdownMenu game={{ ...baseGame, ...overrides }} />
      </MemoryRouter>
    </QueryClientProvider>
  );
  return { invalidateQueries };
};

const openWithdrawDialog = async () => {
  await userEvent.click(screen.getByRole("button", { name: /game menu/i }));
  await userEvent.click(
    screen.getByRole("menuitem", { name: /withdraw from game/i })
  );
  return within(screen.getByRole("alertdialog"));
};

describe("GameDropdownMenu withdrawal", () => {
  beforeEach(() => {
    mockWithdrawMutateAsync.mockReset();
    vi.mocked(toast.success).mockClear();
    vi.mocked(toast.error).mockClear();
  });

  it("offers withdrawal when the player can withdraw", async () => {
    renderMenu();

    await userEvent.click(screen.getByRole("button", { name: /game menu/i }));

    expect(
      screen.getByRole("menuitem", { name: /withdraw from game/i })
    ).toBeInTheDocument();
  });

  it("does not offer withdrawal when the player cannot withdraw", async () => {
    renderMenu({ canWithdraw: false });

    await userEvent.click(screen.getByRole("button", { name: /game menu/i }));

    expect(
      screen.queryByRole("menuitem", { name: /withdraw from game/i })
    ).not.toBeInTheDocument();
  });

  it("explains the consequences before withdrawing", async () => {
    renderMenu();

    const dialog = await openWithdrawDialog();

    expect(dialog.getByText("Withdraw from game")).toBeInTheDocument();
    expect(
      dialog.getByText(/left for another player to claim/i)
    ).toBeInTheDocument();
    expect(dialog.getByText(/cannot rejoin this game/i)).toBeInTheDocument();
    expect(
      dialog.getByText(/commitment rating is not affected/i)
    ).toBeInTheDocument();
    expect(mockWithdrawMutateAsync).not.toHaveBeenCalled();
  });

  it("withdraws and refreshes the game on confirm", async () => {
    mockWithdrawMutateAsync.mockResolvedValue({});
    const { invalidateQueries } = renderMenu();

    const dialog = await openWithdrawDialog();
    await userEvent.click(dialog.getByRole("button", { name: /^withdraw$/i }));

    expect(mockWithdrawMutateAsync).toHaveBeenCalledWith({ gameId: "game-1" });
    expect(toast.success).toHaveBeenCalledWith(
      "You have withdrawn from the game"
    );
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["games"] });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["game", "game-1"],
    });
  });

  it("does not withdraw when cancelled", async () => {
    renderMenu();

    const dialog = await openWithdrawDialog();
    await userEvent.click(dialog.getByRole("button", { name: /cancel/i }));

    expect(mockWithdrawMutateAsync).not.toHaveBeenCalled();
  });

  it("shows an error when withdrawal fails", async () => {
    mockWithdrawMutateAsync.mockRejectedValue(new Error("boom"));
    renderMenu();

    const dialog = await openWithdrawDialog();
    await userEvent.click(dialog.getByRole("button", { name: /^withdraw$/i }));

    expect(toast.error).toHaveBeenCalledWith("Failed to withdraw from game");
  });
});
