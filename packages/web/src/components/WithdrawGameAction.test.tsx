import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { toast } from "sonner";
import { WithdrawGameAction } from "./WithdrawGameAction";

const mockWithdrawMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
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

const renderAction = () => {
  const queryClient = new QueryClient();
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  render(
    <QueryClientProvider client={queryClient}>
      <WithdrawGameAction game={{ id: "game-1" }} />
    </QueryClientProvider>
  );
  return { invalidateQueries };
};

const openDialog = async () => {
  await userEvent.click(
    screen.getByRole("button", { name: /withdraw from game/i })
  );
  return within(screen.getByRole("alertdialog"));
};

describe("WithdrawGameAction", () => {
  beforeEach(() => {
    mockWithdrawMutateAsync.mockReset();
    vi.mocked(toast.success).mockClear();
    vi.mocked(toast.error).mockClear();
  });

  it("explains the consequences before withdrawing", async () => {
    renderAction();

    const dialog = await openDialog();

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
    const { invalidateQueries } = renderAction();

    const dialog = await openDialog();
    await userEvent.click(dialog.getByRole("button", { name: /^withdraw$/i }));

    expect(mockWithdrawMutateAsync).toHaveBeenCalledWith({ gameId: "game-1" });
    expect(toast.success).not.toHaveBeenCalled();
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["games"] });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["game", "game-1"],
    });
  });

  it("does not withdraw when cancelled", async () => {
    renderAction();

    const dialog = await openDialog();
    await userEvent.click(dialog.getByRole("button", { name: /cancel/i }));

    expect(mockWithdrawMutateAsync).not.toHaveBeenCalled();
  });

  it("shows an error when withdrawal fails", async () => {
    mockWithdrawMutateAsync.mockRejectedValue(new Error("boom"));
    renderAction();

    const dialog = await openDialog();
    await userEvent.click(dialog.getByRole("button", { name: /^withdraw$/i }));

    expect(toast.error).toHaveBeenCalledWith("Failed to withdraw from game");
  });
});
