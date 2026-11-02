import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { GameRetrieve } from "@/api/generated/endpoints";
import { ActionList } from "./ActionList";

const leaveGame = vi.fn();

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
}));

vi.mock("@/hooks/useCheckNotificationPermission", () => ({
  useCheckNotificationPermission: () => vi.fn(),
}));

const renderList = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/g1"]}>
        <Routes>
          <Route
            path="/game/:gameId"
            element={
              <ActionList
                gameId="g1"
                actions={[{ key: "leave", blockedReason: null }]}
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
});
