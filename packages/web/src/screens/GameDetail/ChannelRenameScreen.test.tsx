import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import type { Channel } from "@/api/generated/endpoints";
import { ChannelRenameScreen } from "./ChannelRenameScreen";

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

const renameChannel = vi.fn().mockResolvedValue({ id: 1, title: "Renamed" });

const mockChannelsData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGamesChannelsListSuspense: () => ({ data: mockChannelsData() }),
  useGamesChannelsPartialUpdate: () => ({
    mutateAsync: renameChannel,
    isPending: false,
  }),
  getGamesChannelsListQueryKey: (gameId: string) => [`/games/${gameId}/channels/`],
}));

const channel = {
  id: 1,
  name: "England, France",
  title: "The great alliance",
  private: true,
} as Channel;

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/chat/channel/1/rename"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/channel/:channelId/rename"
            element={<ChannelRenameScreen />}
          />
          <Route path="*" element={<div />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ChannelRenameScreen", () => {
  it("renames the channel to the name the player types", async () => {
    mockChannelsData.mockReturnValue([channel]);
    const user = userEvent.setup();
    renderScreen();

    const input = screen.getByLabelText("Channel name");
    expect(input).toHaveValue("The great alliance");

    await user.clear(input);
    await user.type(input, "The greater alliance");
    await user.click(screen.getByRole("button", { name: "Rename channel" }));

    await waitFor(() =>
      expect(renameChannel).toHaveBeenCalledWith({
        gameId: "game-1",
        channelId: 1,
        data: { title: "The greater alliance" },
      })
    );
  });

  it("refuses to clear the name", async () => {
    mockChannelsData.mockReturnValue([channel]);
    renameChannel.mockClear();
    const user = userEvent.setup();
    renderScreen();

    await user.clear(screen.getByLabelText("Channel name"));
    await user.click(screen.getByRole("button", { name: "Rename channel" }));

    expect(await screen.findByText("Channel name is required")).toBeInTheDocument();
    expect(renameChannel).not.toHaveBeenCalled();
  });
});
