import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Link, MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from "vitest";
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
const mockChannelData = vi.fn();
const mockUseChannelMessages = vi.fn();
const mockFetchOlder = vi.fn();
const mockMarkRead = vi.fn(() => Promise.resolve());
const mockCreateMessage = vi.fn();
const mockToastError = vi.fn();

vi.mock("sonner", () => ({
  toast: { error: (...args: unknown[]) => mockToastError(...args) },
}));

vi.mock("@/hooks/useChannelMessages", () => ({
  useChannelMessages: (...args: unknown[]) => mockUseChannelMessages(...args),
}));

vi.mock("@/hooks/useInfiniteScroll", () => ({
  useInfiniteScroll: () => ({ current: null }),
}));

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useUserRetrieveSuspense: () => ({ data: { userId: 1, canCreateBotGames: false } }),
  useGamesChannelsRetrieveSuspense: () => ({ data: mockChannelData() }),
  useGamesChannelsMessagesCreateCreate: () => ({
    mutateAsync: mockCreateMessage,
    isPending: false,
  }),
  useGamesChannelsMarkReadCreate: () => ({ mutateAsync: mockMarkRead }),
  getGamesChannelsRetrieveQueryKey: (gameId: string, channelId: number) => [
    "channel",
    gameId,
    channelId,
  ],
  getGamesChannelPreviewsListQueryKey: (gameId: string) => ["previews", gameId],
  getGameRetrieveQueryKey: (gameId: string) => ["game", gameId],
  useVariantsListSuspense: () => ({ data: [] }),
  useVariantsRetrieve: () => ({ data: undefined }),
}));

const player = (overrides = {}) => ({
  id: 1,
  name: "Player 1",
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

const numberedMessage = (id: number) =>
  message({
    id,
    body: `Message ${id}`,
    createdAt: `2026-05-01T12:${String(id).padStart(2, "0")}:00Z`,
  });

const channelDetail = (overrides = {}) => ({
  id: 7,
  name: "Public Press",
  title: "",
  private: false,
  muted: false,
  canMute: true,
  canRename: false,
  unreadMessageCount: 0,
  firstUnreadMessageId: null,
  latestMessageId: 1,
  latestEventId: null,
  events: [],
  ...overrides,
});

const history = (messages: unknown[], overrides = {}) => ({
  messages,
  hasOlder: false,
  fetchOlder: mockFetchOlder,
  isFetchingOlder: false,
  isFetchOlderError: false,
  ...overrides,
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

const seatedPlayerGame = () =>
  gameRunByGameMaster({
    members: [player({ isCurrentUser: true })],
    gameMaster: null,
  });

const directChannelGame = () =>
  gameRunByGameMaster({
    variantId: "standard",
    members: [
      player({ id: 1, name: "Player 1", nation: "England", isCurrentUser: true }),
      player({ id: 2, name: "Player 2", nation: "France" }),
    ],
    gameMaster: null,
  });

const franceMessage = (overrides = {}) =>
  message({
    sender: {
      id: 2,
      name: "Player 2",
      picture: null,
      isCurrentUser: false,
      nation: { name: "France", color: "#0000ff" },
      isGameMaster: false,
    },
    ...overrides,
  });

const screenTree = (
  queryClient: QueryClient,
  channelId: number | string
) => (
  <QueryClientProvider client={queryClient}>
    <MemoryRouter initialEntries={[`/game/game-1/phase/1/chat/channel/${channelId}`]}>
      <Link to="/game/game-1/phase/1/chat/channel/8">Next channel</Link>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/chat/channel/:channelId"
          element={<ChannelScreen />}
        />
      </Routes>
    </MemoryRouter>
  </QueryClientProvider>
);

const renderChannel = (channelId: number | string = 7) => {
  const queryClient = new QueryClient();
  const view = render(screenTree(queryClient, channelId));
  return {
    queryClient,
    rerender: () => view.rerender(screenTree(queryClient, channelId)),
  };
};

const thread = () =>
  screen.getByText("Message 5").closest(".overflow-y-auto") as HTMLElement;

const precedes = (first: HTMLElement, second: HTMLElement) =>
  !!(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING);

beforeEach(() => {
  sessionStorage.clear();
  mockMarkRead.mockClear();
  mockCreateMessage.mockReset();
  mockToastError.mockClear();
  mockFetchOlder.mockReset();
  mockChannelData.mockReturnValue(channelDetail());
  mockUseChannelMessages.mockReturnValue(history([message()]));
});

describe("ChannelScreen", () => {
  it("shows the composer for a seated player", () => {
    mockGameData.mockReturnValue(seatedPlayerGame());

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
    mockChannelData.mockReturnValue(
      channelDetail({ name: "Austria, France", private: true })
    );

    renderChannel();

    expect(screen.queryByPlaceholderText("Type a message")).not.toBeInTheDocument();
  });

  it("only shows the title tooltip when the label is truncated", async () => {
    const user = userEvent.setup();
    mockGameData.mockReturnValue(gameRunByGameMaster());

    renderChannel();

    const title = screen.getByText("Public Press");
    Object.defineProperties(title, {
      clientWidth: { configurable: true, value: 100 },
      scrollWidth: { configurable: true, value: 100 },
    });
    fireEvent(window, new Event("resize"));
    await user.hover(title);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    expect(title).toHaveClass("inline-block", "max-w-full");
    expect(title).not.toHaveAttribute("tabindex");

    Object.defineProperty(title, "scrollWidth", {
      configurable: true,
      value: 200,
    });
    fireEvent(window, new Event("resize"));
    await user.unhover(title);
    expect(title).toHaveAttribute("tabindex", "0");
    fireEvent.focus(title);

    expect(await screen.findByRole("tooltip")).toHaveTextContent("Public Press");
  });

  it("links the channel heading to chat options", () => {
    mockGameData.mockReturnValue(seatedPlayerGame());
    mockChannelData.mockReturnValue(
      channelDetail({ name: "Austria, France", private: true })
    );

    renderChannel();

    expect(
      screen.getByRole("link", { name: "Open chat options for France" })
    ).toHaveAttribute("href", "/game/game-1/phase/1/chat/channel/7/options");
    expect(
      screen.queryByRole("link", { name: "Rename channel" })
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("separator")).not.toBeInTheDocument();
  });

  it("marks public press read for the game master", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());

    renderChannel();

    expect(mockMarkRead).toHaveBeenCalledWith({ gameId: "game-1", channelId: 7 });
  });

  it("refreshes the channel, previews and game once marked read", async () => {
    mockGameData.mockReturnValue(seatedPlayerGame());
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");

    render(screenTree(queryClient, 7));

    await waitFor(() => expect(invalidate).toHaveBeenCalledTimes(3));
    expect(invalidate.mock.calls.map(call => call[0]?.queryKey)).toEqual([
      ["channel", "game-1", 7],
      ["previews", "game-1"],
      ["game", "game-1"],
    ]);
  });

  it("does not mark read for a spectator", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster({ gameMaster: null }));

    renderChannel();

    expect(mockMarkRead).not.toHaveBeenCalled();
    expect(
      screen.getByRole("link", { name: "Open chat options for Public Press" })
    ).toHaveAttribute("href", "/game/game-1/phase/1/chat/channel/7/options");
  });

  it("attributes a game master message to the Game Master", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());
    mockUseChannelMessages.mockReturnValue(
      history([
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
      ])
    );

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
    mockUseChannelMessages.mockReturnValue(
      history([
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
      ])
    );

    renderChannel();

    expect(screen.getByText("Game Master")).toBeInTheDocument();
    expect(screen.queryByText("Zara")).not.toBeInTheDocument();
  });

  it("still attributes player messages to their nation", () => {
    mockGameData.mockReturnValue(gameRunByGameMaster());

    renderChannel();

    expect(screen.getByText("Austria")).toBeInTheDocument();
  });

  it("names the player behind the nation in a direct channel", () => {
    mockGameData.mockReturnValue(directChannelGame());
    mockChannelData.mockReturnValue(
      channelDetail({ id: 1, name: "England, France", private: true })
    );
    mockUseChannelMessages.mockReturnValue(history([]));

    renderChannel(1);

    expect(screen.getByText("France")).toBeInTheDocument();
    expect(screen.getByText("Player 2")).toBeInTheDocument();
  });

  it("does not label bubbles with the sender in a direct channel", () => {
    mockGameData.mockReturnValue(directChannelGame());
    mockChannelData.mockReturnValue(
      channelDetail({ id: 1, name: "England, France", private: true })
    );
    mockUseChannelMessages.mockReturnValue(
      history([franceMessage({ body: "Hello there" })])
    );

    renderChannel(1);

    expect(screen.getByText("Hello there")).toBeInTheDocument();
    expect(screen.getAllByText("France")).toHaveLength(1);
  });

  it("labels bubbles with the sender nation in a group channel", () => {
    mockGameData.mockReturnValue(
      gameRunByGameMaster({
        variantId: "standard",
        members: [
          player({ id: 1, name: "Player 1", nation: "England", isCurrentUser: true }),
          player({ id: 2, name: "Player 2", nation: "France" }),
          player({ id: 3, name: "Player 3", nation: "Germany" }),
        ],
        gameMaster: null,
      })
    );
    mockChannelData.mockReturnValue(
      channelDetail({ id: 1, name: "England, France, Germany", private: true })
    );
    mockUseChannelMessages.mockReturnValue(
      history([franceMessage({ body: "Hello there" })])
    );

    renderChannel(1);

    expect(screen.getByText("Hello there")).toBeInTheDocument();
    expect(screen.getByText("France")).toBeInTheDocument();
  });

  it("shows a rename between the messages it happened between", () => {
    mockGameData.mockReturnValue(directChannelGame());
    mockChannelData.mockReturnValue(
      channelDetail({
        id: 1,
        name: "England, France",
        title: "The great alliance",
        private: true,
        events: [
          {
            id: 1,
            text: "France renamed the channel to The great alliance",
            createdAt: "2026-09-15T10:05:00Z",
          },
        ],
      })
    );
    mockUseChannelMessages.mockReturnValue(
      history([
        franceMessage({ id: 1, body: "Before", createdAt: "2026-09-15T10:00:00Z" }),
        franceMessage({ id: 2, body: "After", createdAt: "2026-09-15T10:10:00Z" }),
      ])
    );

    renderChannel(1);

    const notice = screen.getByText(
      "France renamed the channel to The great alliance"
    );
    expect(precedes(screen.getByText("Before"), notice)).toBe(true);
    expect(precedes(notice, screen.getByText("After"))).toBe(true);
  });

  describe("history", () => {
    beforeEach(() => {
      mockGameData.mockReturnValue(seatedPlayerGame());
    });

    it("loads history up to the channel's latest message", () => {
      mockChannelData.mockReturnValue(channelDetail({ latestMessageId: 12 }));

      renderChannel();

      expect(mockUseChannelMessages).toHaveBeenCalledWith("game-1", 7, 12);
    });

    it("shows a rename that arrives in a poll", () => {
      const { rerender } = renderChannel();

      mockChannelData.mockReturnValue(channelDetail({ title: "Town square" }));
      rerender();

      expect(screen.getByText("Town square")).toBeInTheDocument();
    });

    it("shows an event that arrives in a poll", () => {
      const { rerender } = renderChannel();

      mockChannelData.mockReturnValue(
        channelDetail({
          events: [
            {
              id: 4,
              text: "Germany joined the channel",
              createdAt: "2026-05-01T12:05:00Z",
            },
          ],
        })
      );
      rerender();

      expect(screen.getByText("Germany joined the channel")).toBeInTheDocument();
    });

    it("hides events older than the loaded history until it reaches them", () => {
      const olderEvent = {
        id: 4,
        text: "France renamed the channel",
        createdAt: "2026-05-01T12:03:00Z",
      };
      mockChannelData.mockReturnValue(channelDetail({ events: [olderEvent] }));
      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(5), numberedMessage(6)], { hasOlder: true })
      );

      const { rerender } = renderChannel();

      expect(screen.queryByText("France renamed the channel")).not.toBeInTheDocument();

      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(1), numberedMessage(5), numberedMessage(6)])
      );
      rerender();

      const notice = screen.getByText("France renamed the channel");
      expect(precedes(screen.getByText("Message 1"), notice)).toBe(true);
      expect(precedes(notice, screen.getByText("Message 5"))).toBe(true);
    });

    it("shows the events of a channel without messages", () => {
      mockChannelData.mockReturnValue(
        channelDetail({
          latestMessageId: null,
          events: [
            {
              id: 4,
              text: "France renamed the channel",
              createdAt: "2026-05-01T12:00:00Z",
            },
          ],
        })
      );
      mockUseChannelMessages.mockReturnValue(history([]));

      renderChannel();

      expect(screen.getByText("France renamed the channel")).toBeInTheDocument();
    });

    it("offers to retry when older messages fail to load", () => {
      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(5)], { hasOlder: true, isFetchOlderError: true })
      );

      renderChannel();
      fireEvent.click(screen.getByRole("button", { name: "Load earlier messages" }));

      expect(mockFetchOlder).toHaveBeenCalled();
    });

    it("shows the error state when the channel fails to load", () => {
      vi.spyOn(console, "error").mockImplementation(() => {});
      mockChannelData.mockImplementation(() => {
        throw new Error("Server Error");
      });

      renderChannel();

      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    });

    it("shows the error state when history fails to load", () => {
      vi.spyOn(console, "error").mockImplementation(() => {});
      mockUseChannelMessages.mockImplementation(() => {
        throw new Error("Server Error");
      });

      renderChannel();

      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    });

    it("starts afresh when switching channel", () => {
      mockChannelData.mockReturnValue(channelDetail({ firstUnreadMessageId: 2 }));
      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(1), numberedMessage(2)])
      );
      renderChannel();
      expect(screen.getByText("New messages")).toBeInTheDocument();

      mockChannelData.mockReturnValue(
        channelDetail({ id: 8, latestMessageId: 9, firstUnreadMessageId: null })
      );
      mockUseChannelMessages.mockReturnValue(history([numberedMessage(9)]));
      fireEvent.click(screen.getByRole("link", { name: "Next channel" }));

      expect(mockUseChannelMessages).toHaveBeenLastCalledWith("game-1", 8, 9);
      expect(screen.getByText("Message 9")).toBeInTheDocument();
      expect(screen.queryByText("New messages")).not.toBeInTheDocument();
    });
  });

  describe("unread divider", () => {
    beforeEach(() => {
      mockGameData.mockReturnValue(seatedPlayerGame());
    });

    it("sits above the first unread message", () => {
      mockChannelData.mockReturnValue(channelDetail({ firstUnreadMessageId: 2 }));
      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(1), numberedMessage(2)])
      );

      renderChannel();

      const divider = screen.getByText("New messages");
      expect(precedes(screen.getByText("Message 1"), divider)).toBe(true);
      expect(precedes(divider, screen.getByText("Message 2"))).toBe(true);
    });

    it("stays in place once the channel is marked read", () => {
      mockChannelData.mockReturnValue(channelDetail({ firstUnreadMessageId: 2 }));
      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(1), numberedMessage(2)])
      );
      const { rerender } = renderChannel();

      mockChannelData.mockReturnValue(channelDetail({ firstUnreadMessageId: null }));
      rerender();

      expect(screen.getByText("New messages")).toBeInTheDocument();
    });

    it("sits at the top while the first unread message is not yet loaded", () => {
      mockChannelData.mockReturnValue(channelDetail({ firstUnreadMessageId: 2 }));
      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(5), numberedMessage(6)], { hasOlder: true })
      );
      const { rerender } = renderChannel();

      const divider = screen.getByText("New messages");
      expect(precedes(divider, screen.getByText("Message 5"))).toBe(true);

      mockUseChannelMessages.mockReturnValue(
        history([1, 2, 5, 6].map(numberedMessage))
      );
      rerender();

      const exactDivider = screen.getByText("New messages");
      expect(precedes(screen.getByText("Message 1"), exactDivider)).toBe(true);
      expect(precedes(exactDivider, screen.getByText("Message 2"))).toBe(true);
    });

    it("is absent when nothing is unread", () => {
      mockUseChannelMessages.mockReturnValue(
        history([numberedMessage(1), numberedMessage(2)])
      );

      renderChannel();

      expect(screen.queryByText("New messages")).not.toBeInTheDocument();
    });
  });

  describe("scrolling", () => {
    const scrollThread = (scrollTop: number) => {
      const element = thread();
      element.scrollTop = scrollTop;
      fireEvent.scroll(element);
    };

    beforeEach(() => {
      mockGameData.mockReturnValue(seatedPlayerGame());
      Object.defineProperty(HTMLElement.prototype, "scrollHeight", {
        configurable: true,
        get(this: HTMLElement) {
          return this.childElementCount * 100;
        },
      });
      Object.defineProperty(HTMLElement.prototype, "clientHeight", {
        configurable: true,
        get: () => 100,
      });
      mockUseChannelMessages.mockReturnValue(
        history([5, 6, 7, 8].map(numberedMessage), { hasOlder: true })
      );
    });

    afterEach(() => {
      Reflect.deleteProperty(HTMLElement.prototype, "scrollHeight");
      Reflect.deleteProperty(HTMLElement.prototype, "clientHeight");
    });

    it("opens at the latest message", () => {
      renderChannel();

      expect(thread().scrollTop).toBe(500);
    });

    it("keeps the reader's place when older messages load", () => {
      const { rerender } = renderChannel();
      scrollThread(0);

      mockUseChannelMessages.mockReturnValue(
        history([3, 4, 5, 6, 7, 8].map(numberedMessage), { hasOlder: true })
      );
      rerender();

      expect(thread().scrollTop).toBe(200);
    });

    it("follows new messages while at the bottom", () => {
      const { rerender } = renderChannel();

      mockUseChannelMessages.mockReturnValue(
        history([5, 6, 7, 8, 9].map(numberedMessage), { hasOlder: true })
      );
      rerender();

      expect(thread().scrollTop).toBe(600);
    });

    it("stays put for new messages while reading further up", () => {
      const { rerender } = renderChannel();
      scrollThread(100);

      mockUseChannelMessages.mockReturnValue(
        history([5, 6, 7, 8, 9].map(numberedMessage), { hasOlder: true })
      );
      rerender();

      expect(thread().scrollTop).toBe(100);
    });

    it("jumps to the reader's own message after sending", async () => {
      mockCreateMessage.mockResolvedValue({});
      const { rerender } = renderChannel();
      scrollThread(100);

      fireEvent.change(screen.getByPlaceholderText("Type a message"), {
        target: { value: "On my way" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Send message" }));
      await waitFor(() =>
        expect(screen.getByPlaceholderText("Type a message")).toHaveValue("")
      );
      mockUseChannelMessages.mockReturnValue(
        history([5, 6, 7, 8, 9].map(numberedMessage), { hasOlder: true })
      );
      rerender();

      expect(thread().scrollTop).toBe(600);
    });
  });

  describe("sending a message", () => {
    const sentClientMessageId = (call = 0) =>
      mockCreateMessage.mock.calls[call][0].data.clientMessageId;

    const typeAndSend = (body: string) => {
      fireEvent.change(screen.getByPlaceholderText("Type a message"), {
        target: { value: body },
      });
      fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    };

    beforeEach(() => {
      mockGameData.mockReturnValue(seatedPlayerGame());
    });

    it("refreshes the channel and previews but not the loaded history", async () => {
      mockCreateMessage.mockResolvedValue({});
      mockMarkRead.mockReturnValue(new Promise(() => {}));
      const queryClient = new QueryClient();
      const invalidate = vi.spyOn(queryClient, "invalidateQueries");
      render(screenTree(queryClient, 7));

      typeAndSend("Can u tap Sev");

      await waitFor(() => expect(invalidate).toHaveBeenCalledTimes(2));
      expect(invalidate.mock.calls.map(call => call[0]?.queryKey)).toEqual([
        ["channel", "game-1", 7],
        ["previews", "game-1"],
      ]);
    });

    it("sends only once when Send is pressed twice quickly", () => {
      mockCreateMessage.mockReturnValue(new Promise(() => {}));
      renderChannel();

      typeAndSend("Can u tap Sev");
      fireEvent.click(screen.getByRole("button", { name: "Send message" }));

      expect(mockCreateMessage).toHaveBeenCalledTimes(1);
    });

    it("sends the same client message id when the same text is resent", async () => {
      mockCreateMessage.mockRejectedValue(new Error("Network Error"));
      renderChannel();

      typeAndSend("Can u tap Sev");
      await waitFor(() => expect(mockToastError).toHaveBeenCalledTimes(1));
      fireEvent.click(screen.getByRole("button", { name: "Send message" }));
      await waitFor(() => expect(mockCreateMessage).toHaveBeenCalledTimes(2));

      expect(mockCreateMessage.mock.calls[0][0].data.body).toBe("Can u tap Sev");
      expect(sentClientMessageId(0)).toEqual(expect.any(String));
      expect(sentClientMessageId(1)).toBe(sentClientMessageId(0));
    });

    it("keeps the text and shows an error when the send fails", async () => {
      mockCreateMessage.mockRejectedValue(new Error("Network Error"));
      renderChannel();

      typeAndSend("Can u tap Sev");

      await waitFor(() =>
        expect(mockToastError).toHaveBeenCalledWith("Failed to send message")
      );
      expect(screen.getByPlaceholderText("Type a message")).toHaveValue("Can u tap Sev");
    });
  });
});
