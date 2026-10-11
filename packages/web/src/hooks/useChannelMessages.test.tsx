import React, { Suspense } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  ChannelMessage,
  ChannelMessagePage,
  GamesChannelsMessagesRetrieveParams,
} from "@/api/generated/endpoints";
import { useChannelMessages } from "./useChannelMessages";

const mockMessagesRetrieve = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  gamesChannelsMessagesRetrieve: (
    gameId: string,
    channelId: number,
    params: GamesChannelsMessagesRetrieveParams
  ) => mockMessagesRetrieve(gameId, channelId, params),
  getGamesChannelsMessagesRetrieveQueryKey: (
    gameId: string,
    channelId: number
  ) => [`/games/${gameId}/channels/${channelId}/messages/`],
}));

const message = (id: number): ChannelMessage =>
  ({
    id,
    body: `Message ${id}`,
    createdAt: new Date(Date.UTC(2026, 4, 1, 12, id)).toISOString(),
    sender: { id: 1, name: "Alice", isCurrentUser: false },
  }) as ChannelMessage;

const page = (
  ids: number[],
  { hasOlder = false, hasNewer = false } = {}
): ChannelMessagePage => ({
  results: ids.map(message),
  hasOlder,
  hasNewer,
});

const ids = (messages: readonly ChannelMessage[]) => messages.map(m => m.id);

interface HookProps {
  gameId: string;
  channelId: number;
  latestMessageId: number | null;
}

const renderMessages = (initialProps: HookProps) => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>
      <Suspense fallback={null}>{children}</Suspense>
    </QueryClientProvider>
  );
  return renderHook(
    ({ gameId, channelId, latestMessageId }: HookProps) =>
      useChannelMessages(gameId, channelId, latestMessageId),
    { wrapper, initialProps }
  );
};

const loaded = async (result: { current: unknown }) =>
  waitFor(() => expect(result.current).toBeTruthy());

beforeEach(() => {
  mockMessagesRetrieve.mockReset();
});

describe("useChannelMessages", () => {
  it("loads the newest page without a boundary", async () => {
    mockMessagesRetrieve.mockResolvedValue(page([3, 4], { hasOlder: true }));

    const { result } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 4,
    });
    await loaded(result);

    expect(mockMessagesRetrieve).toHaveBeenCalledTimes(1);
    expect(mockMessagesRetrieve).toHaveBeenCalledWith("game-1", 7, {});
    expect(ids(result.current.messages)).toEqual([3, 4]);
    expect(result.current.hasOlder).toBe(true);
  });

  it("loads older pages before the oldest loaded message", async () => {
    mockMessagesRetrieve
      .mockResolvedValueOnce(page([3, 4], { hasOlder: true }))
      .mockResolvedValueOnce(page([1, 2], { hasNewer: true }));

    const { result } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 4,
    });
    await loaded(result);
    await act(() => result.current.fetchOlder());

    await waitFor(() =>
      expect(ids(result.current.messages)).toEqual([1, 2, 3, 4])
    );
    expect(mockMessagesRetrieve).toHaveBeenLastCalledWith("game-1", 7, {
      before: 3,
    });
    expect(result.current.hasOlder).toBe(false);
  });

  it("follows newer pages until none are left", async () => {
    mockMessagesRetrieve
      .mockResolvedValueOnce(page([1, 2]))
      .mockResolvedValueOnce(page([3, 4], { hasOlder: true, hasNewer: true }))
      .mockResolvedValueOnce(page([5, 6], { hasOlder: true, hasNewer: true }))
      .mockResolvedValueOnce(page([7], { hasOlder: true }));

    const { result, rerender } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 2,
    });
    await loaded(result);
    rerender({ gameId: "game-1", channelId: 7, latestMessageId: 7 });

    await waitFor(() =>
      expect(ids(result.current.messages)).toEqual([1, 2, 3, 4, 5, 6, 7])
    );
    expect(mockMessagesRetrieve.mock.calls.map(call => call[2])).toEqual([
      {},
      { after: 2 },
      { after: 4 },
      { after: 6 },
    ]);
  });

  it("does not request newer messages when the channel has none", async () => {
    mockMessagesRetrieve.mockResolvedValue(page([1, 2]));

    const { result, rerender } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 2,
    });
    await loaded(result);
    rerender({ gameId: "game-1", channelId: 7, latestMessageId: 2 });
    await act(() => new Promise(resolve => setTimeout(resolve, 20)));

    expect(mockMessagesRetrieve).toHaveBeenCalledTimes(1);
  });

  it("shows a message once when pages overlap", async () => {
    mockMessagesRetrieve
      .mockResolvedValueOnce(page([1, 2]))
      .mockResolvedValueOnce(page([2, 3], { hasOlder: true }));

    const { result, rerender } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 2,
    });
    await loaded(result);
    rerender({ gameId: "game-1", channelId: 7, latestMessageId: 3 });

    await waitFor(() =>
      expect(ids(result.current.messages)).toEqual([1, 2, 3])
    );
  });

  it("does not repeat a request that brought nothing newer", async () => {
    mockMessagesRetrieve
      .mockResolvedValueOnce(page([1, 2]))
      .mockResolvedValue(page([], { hasOlder: true }));

    const { result, rerender } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 2,
    });
    await loaded(result);
    rerender({ gameId: "game-1", channelId: 7, latestMessageId: 3 });

    await waitFor(() => expect(mockMessagesRetrieve).toHaveBeenCalledTimes(2));
    await act(() => new Promise(resolve => setTimeout(resolve, 20)));
    expect(mockMessagesRetrieve).toHaveBeenCalledTimes(2);
    expect(ids(result.current.messages)).toEqual([1, 2]);
  });

  it("loads the newest page once an empty channel gets its first message", async () => {
    mockMessagesRetrieve
      .mockResolvedValueOnce(page([]))
      .mockResolvedValueOnce(page([1]));

    const { result, rerender } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: null,
    });
    await loaded(result);
    rerender({ gameId: "game-1", channelId: 7, latestMessageId: 1 });

    await waitFor(() => expect(ids(result.current.messages)).toEqual([1]));
    expect(mockMessagesRetrieve).toHaveBeenLastCalledWith("game-1", 7, {});
  });

  it("starts a separate history for another channel", async () => {
    mockMessagesRetrieve.mockImplementation((_gameId, channelId) =>
      Promise.resolve(channelId === 7 ? page([1, 2]) : page([10]))
    );

    const { result, rerender } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 2,
    });
    await loaded(result);
    rerender({ gameId: "game-1", channelId: 8, latestMessageId: 10 });

    await waitFor(() => expect(ids(result.current.messages)).toEqual([10]));
    expect(mockMessagesRetrieve).toHaveBeenLastCalledWith("game-1", 8, {});
  });

  it("reports a failed older page without losing loaded messages", async () => {
    mockMessagesRetrieve
      .mockResolvedValueOnce(page([3, 4], { hasOlder: true }))
      .mockRejectedValueOnce(new Error("Network Error"));

    const { result } = renderMessages({
      gameId: "game-1",
      channelId: 7,
      latestMessageId: 4,
    });
    await loaded(result);
    await act(() => result.current.fetchOlder());

    await waitFor(() => expect(result.current.isFetchOlderError).toBe(true));
    expect(ids(result.current.messages)).toEqual([3, 4]);
  });
});
