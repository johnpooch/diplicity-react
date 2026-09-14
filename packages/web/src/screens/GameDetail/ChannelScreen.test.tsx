import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
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

const mockGameData = vi.fn();
const mockChannelsData = vi.fn();
const mockMarkRead = vi.fn(() => Promise.resolve());

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useUserRetrieveSuspense: () => ({ data: { userId: 1, canCreateBotGames: false } }),
  useGamesChannelsListSuspense: () => ({ data: mockChannelsData() }),
  useGamesChannelsMessagesCreateCreate: () => ({
    mutateAsync: vi.fn(() => Promise.resolve()),
    isPending: false,
  }),
  useGamesChannelsMarkReadCreate: () => ({ mutateAsync: mockMarkRead }),
  getGamesChannelsListQueryKey: (gameId: string) => ["channels", gameId],
  getGameRetrieveQueryKey: (gameId: string) => ["game", gameId],
  useVariantsListSuspense: () => ({ data: [] }),
  useVariantsRetrieve: () => ({ data: undefined }),
}));

const player = (overrides = {}) => ({
  id: 1,
  nation: "Austria",
  isCurrentUser: false,
  kicked: false,
  ...overrides,
});

const message = (overrides = {}) => ({
  id: 1,
  body: "Hello",
  createdAt: "2026-05-01T12:00:00Z",
  sender: {
    id: 1,
    name: "Alice",
    picture: null,
    nation: { name: "Austria", color: "#c48f65" },
    isCurrentUser: false,
    isGameMaster: false,
  },
  ...overrides,
});

const publicChannel = (messages: unknown[] = []) => ({
  id: 7,
  name: "Public Press",
  private: false,
  memberIds: [1],
  unreadMessageCount: 0,
  messages,
});

const gameRunByGameMaster = (overrides = {}) => ({
  sandbox: false,
  pressType: "public_press",
  status: "active",
  variantId: "classical",
  members: [player()],
  gameMaster: { userId: 1, name: "Mock Player", picture: null },
  ...overrides,
});

const renderChannel = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/chat/channel/7"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/channel/:channelId"
            element={<ChannelScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

beforeEach(() => {
  mockMarkRead.mockClear();
  mockChannelsData.mockReturnValue([publicChannel([message()])]);
});

describe("ChannelScreen", () => {
  it("shows the composer for a seated player", () => {
    mockGameData.mockReturnValue(
      gameRunByGameMaster({
        members: [player({ isCurrentUser: true })],
        gameMaster: null,
      })
    );

    renderChannel();

    expect(screen.getByPlaceholderText("Type a message")).toBeInTheDocument();
  });

  it("shows the composer in public press for the game master", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());

    renderChannel();

    expect(screen.getByPlaceholderText("Type a message")).toBeInTheDocument();
  });

  it("hides the composer for a spectator", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster({ gameMaster: null }));

    renderChannel();

    expect(screen.queryByPlaceholderText("Type a message")).not.toBeInTheDocument();
  });

  it("hides the composer in a private channel for the game master", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());
    mockChannelsData.mockReturnValue([
      { ...publicChannel([message()]), name: "Austria, France", private: true },
    ]);

    renderChannel();

    expect(screen.queryByPlaceholderText("Type a message")).not.toBeInTheDocument();
  });

  it("marks public press read for the game master", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());

    renderChannel();

    expect(mockMarkRead).toHaveBeenCalledWith({ gameId: "game-1", channelId: 7 });
  });

  it("does not mark read for a spectator", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster({ gameMaster: null }));

    renderChannel();

    expect(mockMarkRead).not.toHaveBeenCalled();
  });

  it("attributes a game master message to the Game Master", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());
    mockChannelsData.mockReturnValue([
      publicChannel([
        message({
          id: 2,
          body: "Deadlines are 24 hours.",
          sender: {
            id: 99,
            name: "Mock Player",
            picture: null,
            nation: null,
            isCurrentUser: true,
            isGameMaster: true,
          },
        }),
      ]),
    ]);

    renderChannel();

    expect(screen.getByText("Deadlines are 24 hours.")).toBeInTheDocument();
    expect(screen.getByText("Game Master")).toBeInTheDocument();
    expect(screen.queryByText("Mock Player")).not.toBeInTheDocument();
  });

  it("attributes a game master message for a seated player viewing it", () => {
    mockGameData.mockReturnValue(
      gameRunByGameMaster({
        members: [player({ isCurrentUser: true })],
        gameMaster: { userId: 9, name: "Zara", picture: null },
      })
    );
    mockChannelsData.mockReturnValue([
      publicChannel([
        message({
          id: 3,
          body: "Please submit orders.",
          sender: {
            id: 99,
            name: "Zara",
            picture: null,
            nation: null,
            isCurrentUser: false,
            isGameMaster: true,
          },
        }),
      ]),
    ]);

    renderChannel();

    expect(screen.getByText("Game Master")).toBeInTheDocument();
    expect(screen.queryByText("Zara")).not.toBeInTheDocument();
  });

  it("still attributes player messages to their nation", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());

    renderChannel();

    expect(screen.getByText("Austria")).toBeInTheDocument();
  });
});
