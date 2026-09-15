import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import type { Channel } from "@/api/generated/endpoints";
import { ChannelRenameDialog } from "./ChannelRenameDialog";

const renameChannel = vi.fn().mockResolvedValue({ id: 1, title: "Renamed" });

vi.mock("@/api/generated/endpoints", () => ({
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

const renderDialog = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ChannelRenameDialog gameId="game-1" channel={channel} />
    </QueryClientProvider>
  );

describe("ChannelRenameDialog", () => {
  it("renames the channel to the name the player types", async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByLabelText("Rename channel"));
    const input = screen.getByLabelText("Channel name");
    expect(input).toHaveValue("The great alliance");

    await user.clear(input);
    await user.type(input, "The greater alliance");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(renameChannel).toHaveBeenCalledWith({
        gameId: "game-1",
        channelId: 1,
        data: { title: "The greater alliance" },
      })
    );
  });

  it("refuses to clear the name", async () => {
    const user = userEvent.setup();
    renameChannel.mockClear();
    renderDialog();

    await user.click(screen.getByLabelText("Rename channel"));
    await user.clear(screen.getByLabelText("Channel name"));
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Channel name is required")).toBeInTheDocument();
    expect(renameChannel).not.toHaveBeenCalled();
  });
});
