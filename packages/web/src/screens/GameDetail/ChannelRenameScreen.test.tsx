import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { toast } from "sonner";
import type { ChannelDetail } from "@/api/generated/endpoints";
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

const mockChannelData = vi.fn();

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/api/generated/endpoints", () => ({
  useGamesChannelsRetrieveSuspense: () => ({ data: mockChannelData() }),
  useGamesChannelsPartialUpdate: () => ({
    mutateAsync: renameChannel,
    isPending: false,
  }),
  getGamesChannelsRetrieveQueryKey: (gameId: string, channelId: number) => [
    `/games/${gameId}/channels/${channelId}/`,
  ],
  getGamesChannelPreviewsListQueryKey: (gameId: string) => [
    `/games/${gameId}/channel-previews/`,
  ],
}));

const channel = {
  id: 1,
  name: "England, France",
  title: "The great alliance",
  private: true,
} as ChannelDetail;

const renderScreen = (queryClient = new QueryClient()) =>
  render(
    <QueryClientProvider client={queryClient}>
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

beforeEach(() => {
  vi.clearAllMocks();
  renameChannel.mockResolvedValue({ id: 1, title: "Renamed" });
});

describe("ChannelRenameScreen", () => {
  it("renames the channel to the name the player types", async () => {
    mockChannelData.mockReturnValue(channel);
    const user = userEvent.setup();
    renderScreen();

    const input = screen.getByLabelText("Channel name");
    expect(input).toHaveValue("The great alliance");
    expect(screen.getByRole("button", { name: "Rename channel" })).toHaveClass(
      "cursor-pointer"
    );

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
    expect(toast.success).not.toHaveBeenCalled();
  });

  it("refreshes the channel and its preview after renaming", async () => {
    mockChannelData.mockReturnValue(channel);
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");
    const user = userEvent.setup();
    renderScreen(queryClient);

    await user.click(screen.getByRole("button", { name: "Rename channel" }));

    await waitFor(() =>
      expect(invalidate.mock.calls.map(call => call[0]?.queryKey)).toEqual([
        ["/games/game-1/channels/1/"],
        ["/games/game-1/channel-previews/"],
      ])
    );
  });

  it("refuses to clear the name", async () => {
    mockChannelData.mockReturnValue(channel);
    renameChannel.mockClear();
    const user = userEvent.setup();
    renderScreen();

    await user.clear(screen.getByLabelText("Channel name"));
    await user.click(screen.getByRole("button", { name: "Rename channel" }));

    expect(await screen.findByText("Channel name is required")).toBeInTheDocument();
    expect(renameChannel).not.toHaveBeenCalled();
  });

  it("shows feedback when renaming fails", async () => {
    mockChannelData.mockReturnValue(channel);
    renameChannel.mockRejectedValue(new Error("Request failed"));
    const user = userEvent.setup();
    renderScreen();

    await user.clear(screen.getByLabelText("Channel name"));
    await user.type(screen.getByLabelText("Channel name"), "A new alliance");
    await user.click(screen.getByRole("button", { name: "Rename channel" }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Failed to rename channel")
    );
  });
});
