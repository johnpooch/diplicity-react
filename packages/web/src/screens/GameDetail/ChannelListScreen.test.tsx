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

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      sandbox: false,
      pressType: "public_press",
      status: "active",
      variantId: "standard",
      members: mockMembersData(),
    },
  }),
  useGamesChannelsListSuspense: () => ({
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
  it("shows the latest message preview with the sender nation", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Secret Alliance",
        private: true,
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

    expect(screen.getByText("Austria: Hello")).toBeInTheDocument();
  });

  it("labels the preview 'You' when the latest message is the current user's", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Secret Alliance",
        private: true,
        latestMessage: {
          id: 1,
          body: "See you there",
          sender: {
            id: 1,
            name: "Alice",
            picture: null,
            nation: { name: "Austria" },
            isCurrentUser: true,
          },
          createdAt: "2024-01-15T12:00:00Z",
        },
      },
    ]);

    renderChannelList();

    expect(screen.getByText("You: See you there")).toBeInTheDocument();
  });

  it("shows 'No messages' when the channel has no latest message", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Secret Alliance",
        private: true,
        latestMessage: null,
      },
    ]);

    renderChannelList();

    expect(screen.getByText("Secret Alliance")).toBeInTheDocument();
    expect(screen.getByText("No messages")).toBeInTheDocument();
  });

  it("marks public channels with a badge", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Private Chat",
        private: true,
        latestMessage: null,
      },
      {
        id: 2,
        name: "Public Press",
        private: false,
        latestMessage: null,
      },
    ]);

    renderChannelList();

    expect(screen.getByText("Public")).toBeInTheDocument();
  });

  it("shows create channel button for a member", () => {
    mockChannelsData.mockReturnValue([]);

    renderChannelList();

    expect(screen.getByRole("link", { name: /create channel/i })).toBeInTheDocument();
  });

  it("hides create channel button when the user is not a member", () => {
    mockChannelsData.mockReturnValue([]);
    mockMembersData.mockReturnValue([{ id: 1, nation: "Austria", isCurrentUser: false }]);

    renderChannelList();

    expect(screen.queryByRole("link", { name: /create channel/i })).not.toBeInTheDocument();
  });
});
