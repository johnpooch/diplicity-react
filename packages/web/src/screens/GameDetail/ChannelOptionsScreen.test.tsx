import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ChannelDetail, GameRetrieve } from "@/api/generated/endpoints";
import { ChannelOptionsScreen } from "./ChannelOptionsScreen";

const leave = vi.fn();

let channel: ChannelDetail;

const buildChannel = (overrides: Partial<ChannelDetail> = {}): ChannelDetail => ({
  id: 5,
  name: "England, Italy",
  title: "",
  private: true,
  muted: false,
  canMute: true,
  canRename: true,
  canLeave: true,
  unreadMessageCount: 0,
  firstUnreadMessageId: null,
  latestMessageId: null,
  latestEventId: null,
  events: [],
  ...overrides,
});

const game = {
  id: "g1",
  variantId: "classical",
  members: [{ id: 1, isCurrentUser: true, nation: "England", name: "Alice" }],
} as unknown as GameRetrieve;

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: game }),
  useGamesChannelsRetrieveSuspense: () => ({ data: channel }),
  useGamesChannelsMutePartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGamesChannelsLeaveCreate: () => ({ mutateAsync: leave, isPending: false }),
}));

vi.mock("@/hooks/useGameVariant", () => ({
  useGameVariant: () => ({ nations: [] }),
}));

vi.mock("@/hooks/use-platform", () => ({ useIsDesktopWeb: () => false }));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/g1/phase/7/chat/channel/5/options"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/channel/:channelId/options"
            element={<ChannelOptionsScreen />}
          />
          <Route
            path="/game/:gameId/phase/:phaseId/chat"
            element={<div>Channel list</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ChannelOptionsScreen", () => {
  beforeEach(() => {
    leave.mockReset().mockResolvedValue(undefined);
    channel = buildChannel();
  });

  it("warns that leaving is permanent before leaving", async () => {
    renderScreen();

    await userEvent.click(await screen.findByText("Leave channel"));

    expect(screen.getByText(/you cannot rejoin this channel/i)).toBeInTheDocument();
    expect(leave).not.toHaveBeenCalled();
  });

  it("leaves the channel and returns to the channel list once confirmed", async () => {
    renderScreen();

    await userEvent.click(await screen.findByText("Leave channel"));
    await userEvent.click(screen.getByRole("button", { name: "Leave" }));

    await waitFor(() =>
      expect(leave).toHaveBeenCalledWith({ gameId: "g1", channelId: 5 })
    );
    expect(await screen.findByText("Channel list")).toBeInTheDocument();
  });

  it("does not leave when the warning is cancelled", async () => {
    renderScreen();

    await userEvent.click(await screen.findByText("Leave channel"));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(leave).not.toHaveBeenCalled();
  });

  it("hides the action when the channel cannot be left", async () => {
    channel = buildChannel({ canLeave: false });
    renderScreen();

    await screen.findByText("Mute notifications");
    expect(screen.queryByText("Leave channel")).not.toBeInTheDocument();
  });
});
