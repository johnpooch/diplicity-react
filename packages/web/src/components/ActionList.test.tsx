import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  GameRetrieve,
  MemberActionKeyEnum,
} from "@/api/generated/endpoints";
import { ActionList } from "./ActionList";

const leaveGame = vi.fn();
const withdrawFromGame = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({
    data: {
      sandbox: false,
      isFirstYear: false,
      showShortGameJoinWarning: false,
    } as GameRetrieve,
  }),
  useGameLeaveDestroy: () => ({ mutateAsync: leaveGame }),
  useGameMemberWithdrawPartialUpdate: () => ({ mutateAsync: withdrawFromGame }),
}));

vi.mock("@/hooks/useCheckNotificationPermission", () => ({
  useCheckNotificationPermission: () => vi.fn(),
}));

const renderList = (key: MemberActionKeyEnum = "leave") =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/g1"]}>
        <Routes>
          <Route
            path="/game/:gameId"
            element={
              <ActionList
                gameId="g1"
                actions={[{ key, blockedReason: null }]}
              />
            }
          />
          <Route path="/" element={<div>Home screen</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ActionList", () => {
  beforeEach(() => {
    leaveGame.mockReset();
    withdrawFromGame.mockReset();
    Element.prototype.hasPointerCapture = () => false;
    Element.prototype.scrollIntoView = () => {};
  });

  it("returns home after leaving a game", async () => {
    leaveGame.mockResolvedValue(undefined);
    renderList();

    await userEvent.click(screen.getByRole("button", { name: "Leave game" }));
    await userEvent.click(screen.getByRole("button", { name: "Leave" }));

    expect(leaveGame).toHaveBeenCalledWith({ gameId: "g1" });
    expect(await screen.findByText("Home screen")).toBeInTheDocument();
  });

  it("stays on the game when leaving fails", async () => {
    leaveGame.mockRejectedValue(new Error("failed"));
    renderList();

    await userEvent.click(screen.getByRole("button", { name: "Leave game" }));
    await userEvent.click(screen.getByRole("button", { name: "Leave" }));

    expect(
      await screen.findByRole("button", { name: "Leave game" })
    ).toBeInTheDocument();
    expect(screen.queryByText("Home screen")).not.toBeInTheDocument();
  });

  it("withdraws with the reason the player picks", async () => {
    withdrawFromGame.mockResolvedValue(undefined);
    renderList("withdraw");

    await userEvent.click(
      screen.getByRole("button", { name: "Withdraw from game" })
    );
    await userEvent.click(
      screen.getByRole("combobox", { name: "Why are you withdrawing?" })
    );
    await userEvent.click(
      screen.getByRole("option", { name: "I'm in too many games" })
    );
    await userEvent.click(screen.getByRole("button", { name: "Withdraw" }));

    expect(withdrawFromGame).toHaveBeenCalledWith({
      gameId: "g1",
      data: { reason: "too_many_games" },
    });
  });
});
