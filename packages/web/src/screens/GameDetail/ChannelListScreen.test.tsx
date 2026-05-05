import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";

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

const mockLoggedIn = vi.fn(() => true);
const defaultChannels: unknown[] = [
  {
    id: 1,
    name: "Public Chat",
    private: false,
    messages: [
      {
        id: 1,
        body: "Hello",
        sender: { nation: { name: "France" } },
      },
    ],
  },
];
const mockChannelsData = vi.fn<() => unknown[]>(() => defaultChannels);

vi.mock("@/auth", () => ({
  useAuth: () => ({
    loggedIn: mockLoggedIn(),
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { id: "1", sandbox: false },
  }),
  useGamesChannelsListSuspense: () => ({
    data: mockChannelsData(),
  }),
}));

import { ChannelListScreen } from "./ChannelListScreen";

const renderChannelList = () =>
  render(
    <MemoryRouter initialEntries={["/game/1/phase/1/chat"]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/chat"
          element={<ChannelListScreen />}
        />
      </Routes>
    </MemoryRouter>
  );

describe("ChannelListScreen", () => {
  it("shows Create Channel button when logged in", async () => {
    mockLoggedIn.mockReturnValue(true);
    renderChannelList();

    expect(await screen.findByText("Create Channel")).toBeInTheDocument();
  });

  it("hides Create Channel button when not logged in", async () => {
    mockLoggedIn.mockReturnValue(false);
    renderChannelList();

    expect(await screen.findByText("Public Chat")).toBeInTheDocument();
    expect(screen.queryByText("Create Channel")).not.toBeInTheDocument();
  });

  it("shows unread badge when channel has unread messages", () => {
    mockLoggedIn.mockReturnValue(true);
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
    mockLoggedIn.mockReturnValue(true);
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
    mockLoggedIn.mockReturnValue(true);
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
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
