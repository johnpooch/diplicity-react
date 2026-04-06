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

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { sandbox: false },
  }),
  useGamesChannelsListSuspense: () => ({
    data: mockChannelsData(),
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
        memberIds: [1, 2],
        unreadMessageCount: 5,
        messages: [
          {
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
        ],
      },
    ]);

    renderChannelList();

    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("does not show unread badge when count is zero", () => {
    mockChannelsData.mockReturnValue([
      {
        id: 1,
        name: "Secret Alliance",
        private: true,
        memberIds: [1, 2],
        unreadMessageCount: 0,
        messages: [],
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
        memberIds: [1, 2],
        unreadMessageCount: 3,
        messages: [],
      },
      {
        id: 2,
        name: "Public Press",
        private: false,
        memberIds: [1, 2, 3],
        unreadMessageCount: 0,
        messages: [],
      },
    ]);

    renderChannelList();

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Public")).toBeInTheDocument();
    // No badge for zero unread
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
