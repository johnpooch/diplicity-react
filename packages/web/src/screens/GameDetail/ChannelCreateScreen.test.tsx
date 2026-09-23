import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { ChannelCreateScreen } from "./ChannelCreateScreen";

const { mockToastError } = vi.hoisted(() => ({
  mockToastError: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: mockToastError },
}));

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

const member = (id: number, nation: string, overrides = {}) => ({
  id,
  userId: id,
  name: `Player ${id}`,
  picture: null,
  isCurrentUser: false,
  isBot: false,
  commitment: null,
  nation,
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  isAdmin: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
  seekingReplacement: false,
  replaceable: false,
  ...overrides,
});

const createChannel = vi.fn().mockResolvedValue({ id: 7 });

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      variantId: "standard",
      members: [
        member(1, "England", { isCurrentUser: true }),
        member(2, "Italy", { kicked: true, name: "Departed Player" }),
        member(3, "Italy", { name: "The Dealmaker", isBot: true }),
      ],
    },
  }),
  useVariantsListSuspense: () => ({ data: [] }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamesChannelsCreateCreate: () => ({ mutateAsync: createChannel, isPending: false }),
  getGamesChannelsListQueryKey: (gameId: string) => [`/game/${gameId}/channels/`],
}));

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/chat/create"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/create"
            element={<ChannelCreateScreen />}
          />
          <Route path="*" element={<div />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ChannelCreateScreen", () => {
  it("offers the replacement for a seat but not the member it replaced", () => {
    renderScreen();

    expect(screen.getByText(/The Dealmaker/)).toBeInTheDocument();
    expect(screen.queryByText(/Departed Player/)).not.toBeInTheDocument();
    expect(screen.getAllByText("Italy")).toHaveLength(1);
  });

  it("labels a bot member", () => {
    renderScreen();

    expect(screen.getByText("The Dealmaker (bot)")).toBeInTheDocument();
  });

  it("creates the channel with the selected members", async () => {
    const user = userEvent.setup();
    renderScreen();

    await user.click(screen.getByLabelText("Select Italy"));
    await user.click(screen.getByRole("button", { name: "Create channel" }));

    await waitFor(() =>
      expect(createChannel).toHaveBeenCalledWith({
        gameId: "game-1",
        data: { memberIds: [3] },
      })
    );
  });

  it("surfaces the server's message when the channel already exists", async () => {
    createChannel.mockRejectedValueOnce({
      response: {
        data: { memberIds: ["Channel already exists."] },
      },
    });
    const user = userEvent.setup();
    renderScreen();

    await user.click(screen.getByLabelText("Select Italy"));
    await user.click(screen.getByRole("button", { name: "Create channel" }));

    await waitFor(() =>
      expect(mockToastError).toHaveBeenCalledWith("Channel already exists.")
    );
  });
});
