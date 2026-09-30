import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";
import { ChannelOptionsScreen } from "./ChannelOptionsScreen";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const muteChannel = vi.fn();
const mockChannel = vi.fn();

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/hooks/useGameVariant", () => ({
  useGameVariant: () => ({
    nations: [
      { name: "England", flagUrl: "england.svg", color: "#ff0000" },
      { name: "France", flagUrl: "france.svg", color: "#0000ff" },
    ],
  }),
}));

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      status: "active",
      pressType: "full_press",
      sandbox: false,
      gameMaster: null,
      members: [
        {
          id: 1,
          name: "Alice",
          nation: "England",
          isCurrentUser: true,
          kicked: false,
        },
        {
          id: 2,
          name: "Bob",
          nation: "France",
          isCurrentUser: false,
          kicked: false,
        },
      ],
    },
  }),
  useUserRetrieveSuspense: () => ({ data: { userId: 1 } }),
  useGamesChannelsListSuspense: () => ({ data: [mockChannel()] }),
  useGamesChannelsMutePartialUpdate: () => ({
    mutateAsync: muteChannel,
    isPending: false,
  }),
  getGamesChannelsListQueryKey: (gameId: string) => ["channels", gameId],
}));

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter
        initialEntries={["/game/game-1/phase/1/chat/channel/7/options"]}
      >
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/channel/:channelId/options"
            element={<ChannelOptionsScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

beforeEach(() => {
  vi.clearAllMocks();
  mockChannel.mockReturnValue({
    id: 7,
    name: "England, France",
    title: "The Entente",
    private: true,
    muted: false,
  });
  muteChannel.mockResolvedValue({ muted: false });
});

describe("ChannelOptionsScreen", () => {
  it("shows the channel profile, member roster, and options", () => {
    renderScreen();

    expect(
      screen.getByRole("heading", { name: "The Entente" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "2 members" })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "2 members" })
    ).toBeInTheDocument();

    const memberList = screen.getByRole("list", { name: "2 members" });
    expect(within(memberList).getByText("England")).toBeInTheDocument();
    expect(within(memberList).getByText("France")).toBeInTheDocument();
    const englandFlag = within(memberList).getByRole("img", {
      name: "England",
    });
    const franceFlag = within(memberList).getByRole("img", {
      name: "France",
    });
    expect(englandFlag).toHaveAttribute("src", "england.svg");
    expect(englandFlag).toHaveStyle("box-shadow: 0 0 0 2px #ff0000");
    expect(franceFlag).toHaveAttribute("src", "france.svg");
    expect(franceFlag).toHaveStyle("box-shadow: 0 0 0 2px #0000ff");
    expect(within(memberList).queryByText("Alice")).not.toBeInTheDocument();
    expect(within(memberList).queryByText("Bob")).not.toBeInTheDocument();
    const renameLink = screen.getByRole("link", { name: /Rename channel/ });
    expect(renameLink).toHaveAttribute(
      "href",
      "/game/game-1/phase/1/chat/channel/7/rename"
    );
    expect(renameLink).toHaveClass("cursor-pointer");
    expect(
      screen.getByRole("button", { name: "Mute notifications" })
    ).toHaveClass("cursor-pointer");
    expect(
      screen.queryByRole("link", { name: /Mute notifications/ })
    ).not.toBeInTheDocument();
  });

  it("mutes immediately without navigating deeper", async () => {
    const user = userEvent.setup();
    renderScreen();

    await user.click(
      screen.getByRole("button", { name: "Mute notifications" })
    );

    await waitFor(() =>
      expect(muteChannel).toHaveBeenCalledWith({
        gameId: "game-1",
        channelId: 7,
        data: { muteDuration: "indefinite" },
      })
    );
    expect(toast.success).toHaveBeenCalledWith(
      "Successfully muted The Entente"
    );
  });

  it("shows feedback when muting fails", async () => {
    const user = userEvent.setup();
    muteChannel.mockRejectedValue(new Error("Request failed"));
    renderScreen();

    await user.click(
      screen.getByRole("button", { name: "Mute notifications" })
    );

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith(
        "There was an error muting this channel"
      )
    );
  });

  it("unmutes immediately without navigating deeper", async () => {
    const user = userEvent.setup();
    mockChannel.mockReturnValue({
      id: 7,
      name: "England, France",
      title: "The Entente",
      private: true,
      muted: true,
    });
    renderScreen();

    await user.click(
      screen.getByRole("button", { name: "Unmute notifications" })
    );

    expect(
      screen.getByRole("button", { name: "Unmute notifications" })
    ).toHaveClass("cursor-pointer");

    await waitFor(() =>
      expect(muteChannel).toHaveBeenCalledWith({
        gameId: "game-1",
        channelId: 7,
        data: { muteDuration: null },
      })
    );
    expect(toast.success).toHaveBeenCalledWith(
      "Successfully unmuted The Entente"
    );
    expect(
      screen.queryByRole("link", { name: /Unmute notifications/ })
    ).not.toBeInTheDocument();
  });
});
