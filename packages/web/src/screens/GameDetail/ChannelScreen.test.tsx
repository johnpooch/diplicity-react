import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { ChannelScreen } from "./ChannelScreen";

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

const message = (id: number, body: string, createdAt: string) => ({
  id,
  body,
  createdAt,
  sender: {
    id: 2,
    name: "Player 2",
    picture: null,
    isCurrentUser: false,
    nation: { name: "France", color: "#0000ff" },
  },
});

const mockChannelsData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      sandbox: false,
      pressType: "public_press",
      status: "active",
      variantId: "standard",
      members: [
        { id: 1, name: "Player 1", nation: "England", isCurrentUser: true },
        { id: 2, name: "Player 2", nation: "France", isCurrentUser: false },
      ],
    },
  }),
  useGamesChannelsListSuspense: () => ({ data: mockChannelsData() }),
  useGamesChannelsMessagesCreateCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGamesChannelsMarkReadCreate: () => ({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  }),
  useGamesChannelsPartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useVariantsListSuspense: () => ({ data: [] }),
  useVariantsRetrieve: () => ({ data: undefined }),
  getGamesChannelsListQueryKey: (gameId: string) => [`/games/${gameId}/channels/`],
  getGameRetrieveQueryKey: (gameId: string) => [`/games/${gameId}/`],
}));

const renderChannel = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/chat/channel/1"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/channel/:channelId"
            element={<ChannelScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ChannelScreen", () => {
  it("shows a rename between the messages it happened between", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "England, France",
        title: "The great alliance",
        private: true,
        unreadMessageCount: 0,
        messages: [
          message(1, "Before", "2026-09-15T10:00:00Z"),
          message(2, "After", "2026-09-15T10:10:00Z"),
        ],
        events: [
          {
            id: 1,
            text: "France renamed the channel to The great alliance",
            createdAt: "2026-09-15T10:05:00Z",
          },
        ],
      },
    ]);

    renderChannel();

    const before = screen.getByText("Before");
    const notice = screen.getByText(
      "France renamed the channel to The great alliance"
    );
    const after = screen.getByText("After");

    expect(
      before.compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(
      notice.compareDocumentPosition(after) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });

  it("names the player behind the nation in a direct channel", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "England, France",
        title: "",
        private: true,
        unreadMessageCount: 0,
        messages: [],
        events: [],
      },
    ]);

    renderChannel();

    expect(screen.getByText("France")).toBeInTheDocument();
    expect(screen.getByText("Player 2")).toBeInTheDocument();
  });
});
