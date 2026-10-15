import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { ChannelListScreen } from "./ChannelListScreen";

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

const mockChannelsData = vi.fn();
const mockMembersData = vi.fn(() => [{ id: 1, nation: "Austria", isCurrentUser: true }]);
const mockCanCreateChannel = vi.fn(() => true);

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      sandbox: false,
      pressType: "public_press",
      status: "active",
      variantId: "standard",
      members: mockMembersData(),
      canCreateChannel: mockCanCreateChannel(),
    },
  }),
  useGamesChannelPreviewsListSuspense: () => ({
    data: mockChannelsData(),
  }),
  useVariantsListSuspense: () => ({
    data: [],
  }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useUserRetrieveSuspense: () => ({
    data: { canCreateBotGames: false },
  }),
}));

const renderChannelList = () =>
  render(
    <MemoryRouter initialEntries={["/game/game-1/phase/1/chat"]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/chat"
          element={<ChannelListScreen />}
        />
      </Routes>
    </MemoryRouter>
  );

describe("ChannelListScreen", () => {
  it("shows unread badge when channel has unread messages", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Secret Alliance",
        private: true,
        unreadMessageCount: 5,
        latestMessage: {
          id: 1,
          body: "Hello",
          sender: {
            id: 1,
            name: "Alice",
            picture: null,
            nation: { name: "Austria" },
            isCurrentUser: false,
          },
          createdAt: "2024-01-15T12:00:00Z",
        },
      },
    ]);

    renderChannelList();

    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("Austria: Hello")).toBeInTheDocument();
  });

  it("says when a channel has no messages yet", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Secret Alliance",
        private: true,
        unreadMessageCount: 0,
        latestMessage: null,
      },
    ]);

    renderChannelList();

    expect(screen.getByText("No messages")).toBeInTheDocument();
  });

  it("does not show unread badge when count is zero", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Secret Alliance",
        private: true,
        unreadMessageCount: 0,
        latestMessage: null,
      },
    ]);

    renderChannelList();

    expect(screen.getByText("Secret Alliance")).toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("shows multiple badges for multiple channels with unread counts", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Private Chat",
        private: true,
        unreadMessageCount: 3,
        latestMessage: null,
      },
      {
        id: 2,
        name: "Public Press",
        private: false,
        unreadMessageCount: 0,
        latestMessage: null,
      },
    ]);

    renderChannelList();

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByLabelText("Public channel")).toBeInTheDocument();
    // No badge for zero unread
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("shows create channel button when the game allows creating channels", () => {
    mockChannelsData.mockReturnValue([]);

    renderChannelList();

    const createLinks = screen.getAllByRole("link", { name: /create channel/i });
    expect(createLinks).toHaveLength(2);
    for (const link of createLinks) {
      expect(link.querySelector("svg")).toBeInTheDocument();
    }
  });

  it("hides create channel button when the game does not allow creating channels", () => {
    mockChannelsData.mockReturnValue([]);
    mockCanCreateChannel.mockReturnValue(false);

    renderChannelList();

    expect(screen.queryByRole("link", { name: /create channel/i })).not.toBeInTheDocument();
  });
});
