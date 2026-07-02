import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";

import { AddBotSheet } from "./AddBotSheet";

const mockAvailableBots = vi.fn();
const mockAddBotMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameAvailableBotsListSuspense: () => ({ data: mockAvailableBots() }),
  useGameAddBotCreate: () => ({
    mutateAsync: mockAddBotMutateAsync,
    isPending: false,
  }),
  getGameRetrieveQueryKey: () => ["game"],
  getGameAvailableBotsListQueryKey: () => ["available-bots"],
}));

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

const renderSheet = (open = true) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <AddBotSheet gameId="game-1" open={open} onOpenChange={vi.fn()} />
    </QueryClientProvider>
  );

describe("AddBotSheet", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAvailableBots.mockReturnValue([
      { userId: 101, name: "The Dealmaker", picture: null },
      { userId: 102, name: "The Iron Lady", picture: null },
    ]);
  });

  it("lists the available bots", async () => {
    renderSheet();

    expect(await screen.findByText("The Dealmaker")).toBeInTheDocument();
    expect(screen.getByText("The Iron Lady")).toBeInTheDocument();
  });

  it("adds the chosen bot to the game", async () => {
    const user = userEvent.setup();
    mockAddBotMutateAsync.mockResolvedValue({});

    renderSheet();

    await user.click(await screen.findByText("The Iron Lady"));
    expect(mockAddBotMutateAsync).toHaveBeenCalledWith({
      gameId: "game-1",
      data: { userId: 102 },
    });
  });

  it("shows an empty state when every bot is already in the game", async () => {
    mockAvailableBots.mockReturnValue([]);

    renderSheet();

    expect(
      await screen.findByText("No AI players available")
    ).toBeInTheDocument();
  });
});
